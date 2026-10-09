import csv
import io
import os
import zipfile
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.job import GenerationJob, JobRecipient, JobStatus, RecipientStatus
from app.models.certificate import Certificate
from app.schemas.job import JobCreateRequest, JobResponse, JobListResponse, JobProgressSummary
from app.schemas.recipient import RecipientResponse
from app.services.job_processor import process_generation_job

router = APIRouter(prefix="/jobs", tags=["Generation Jobs"])


def build_job_response(job: GenerationJob, db: Session, include_recipients: bool = True) -> JobResponse:
    """Helper to convert GenerationJob DB model to JobResponse schema."""
    total = job.total_count or 0
    processed = job.processed_count or 0
    pct = round((processed / total) * 100.0, 1) if total > 0 else 0.0

    progress = JobProgressSummary(
        total=total,
        processed=processed,
        successful=job.success_count or 0,
        failed=job.failed_count or 0,
        percentage=pct
    )

    recipients_resp = None
    if include_recipients:
        recipients_resp = []
        for r in job.recipients:
            cert_code = r.certificate.certificate_code if r.certificate else None
            recipients_resp.append(RecipientResponse(
                id=r.id,
                job_id=r.job_id,
                name=r.name,
                email=r.email,
                custom_fields=r.custom_fields,
                status=r.status,
                error_message=r.error_message,
                certificate_id=r.certificate_id,
                certificate_code=cert_code
            ))

    zip_url = f"{settings.API_V1_STR}/jobs/{job.id}/download-zip" if job.success_count and job.success_count > 0 else None

    return JobResponse(
        id=job.id,
        title=job.title,
        issuer_name=job.issuer_name,
        issue_date=job.issue_date,
        template_theme=job.template_theme,
        status=job.status,
        progress=progress,
        recipients=recipients_resp,
        download_zip_url=zip_url,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.post("/generate", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_generation_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submits a bulk certificate generation job from JSON recipient array.
    Executes certificate generation asynchronously in background tasks.
    """
    if len(request.recipients) > settings.MAX_RECIPIENTS_PER_JOB:
        raise HTTPException(
            status_code=400,
            detail=f"Exceeded maximum recipient limit of {settings.MAX_RECIPIENTS_PER_JOB} per job."
        )

    job_id = str(uuid.uuid4())
    job = GenerationJob(
        id=job_id,
        title=request.title.strip(),
        issuer_name=request.issuer_name.strip(),
        issue_date=request.issue_date.strip(),
        template_theme=request.template_theme.lower(),
        status=JobStatus.PENDING.value,
        total_count=len(request.recipients),
        processed_count=0,
        success_count=0,
        failed_count=0
    )
    db.add(job)
    db.flush()

    for item in request.recipients:
        recipient = JobRecipient(
            id=str(uuid.uuid4()),
            job_id=job.id,
            name=item.name.strip(),
            email=item.email.strip() if item.email else None,
            custom_fields=item.custom_fields,
            status=RecipientStatus.PENDING.value
        )
        db.add(recipient)

    db.commit()
    db.refresh(job)

    # Queue background processing
    background_tasks.add_task(process_generation_job, job_id=job.id)

    return build_job_response(job, db, include_recipients=True)


@router.post("/upload-csv", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_job_from_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV file containing recipient data"),
    title: str = Form(..., description="Course or event title"),
    issuer_name: str = Form("Tech Academy", description="Issuing authority"),
    issue_date: str = Form(..., description="Issue date (e.g. 2026-10-09)"),
    template_theme: str = Form("gold", description="Template theme: gold, indigo, emerald, or crimson"),
    db: Session = Depends(get_db)
):
    """
    Uploads a CSV file with columns (name, email) to create a bulk certificate generation job.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File uploaded must be a CSV file (.csv).")

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")

    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    recipients_list = []
    for row in csv_reader:
        # Case insensitive key search for name & email
        row_clean = {k.strip().lower(): v.strip() for k, v in row.items() if k and v}
        name = row_clean.get("name") or row_clean.get("full_name") or row_clean.get("recipient_name")
        email = row_clean.get("email") or row_clean.get("email_address")
        
        if name:
            recipients_list.append((name, email))

    if not recipients_list:
        raise HTTPException(status_code=400, detail="CSV file must contain a 'name' column with at least one recipient.")

    if len(recipients_list) > settings.MAX_RECIPIENTS_PER_JOB:
        raise HTTPException(status_code=400, detail=f"CSV exceeds maximum recipient limit of {settings.MAX_RECIPIENTS_PER_JOB}.")

    job_id = str(uuid.uuid4())
    job = GenerationJob(
        id=job_id,
        title=title.strip(),
        issuer_name=issuer_name.strip(),
        issue_date=issue_date.strip(),
        template_theme=template_theme.lower(),
        status=JobStatus.PENDING.value,
        total_count=len(recipients_list),
        processed_count=0,
        success_count=0,
        failed_count=0
    )
    db.add(job)
    db.flush()

    for name, email in recipients_list:
        recipient = JobRecipient(
            id=str(uuid.uuid4()),
            job_id=job.id,
            name=name,
            email=email,
            status=RecipientStatus.PENDING.value
        )
        db.add(recipient)

    db.commit()
    db.refresh(job)

    # Queue background task
    background_tasks.add_task(process_generation_job, job_id=job.id)

    return build_job_response(job, db, include_recipients=True)


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Checks real-time progress and results of a certificate generation job.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Generation job '{job_id}' not found.")

    return build_job_response(job, db, include_recipients=True)


@router.get("/{job_id}/download-zip")
def download_job_zip(job_id: str, db: Session = Depends(get_db)):
    """
    Downloads a ZIP archive containing all successfully generated certificates in the job.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Generation job '{job_id}' not found.")

    certificates = db.query(Certificate).filter(Certificate.job_id == job.id).all()
    if not certificates:
        raise HTTPException(status_code=400, detail="No generated certificates found for this job yet.")

    zip_filename = f"Job_Certificates_{job.id[:8]}.zip"
    zip_path = os.path.join(settings.TEMP_DIR, zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for cert in certificates:
            if os.path.exists(cert.file_path):
                zf.write(cert.file_path, arcname=cert.file_name)

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=zip_filename
    )


@router.get("", response_model=JobListResponse)
def list_jobs(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    """
    Lists recent certificate generation jobs.
    """
    total = db.query(GenerationJob).count()
    jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).offset(offset).limit(limit).all()
    
    return JobListResponse(
        jobs=[build_job_response(j, db, include_recipients=False) for j in jobs],
        total_count=total
    )
