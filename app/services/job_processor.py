import os
import uuid
from pathlib import Path
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.job import GenerationJob, JobRecipient, JobStatus, RecipientStatus
from app.models.certificate import Certificate
from app.services.validator import validate_recipient_data
from app.services.generator import generate_certificate_pdf


def generate_unique_cert_code() -> str:
    """Generates a clean unique certificate code e.g. CERT-9F2B-4A1C."""
    u = uuid.uuid4().hex.upper()
    return f"CERT-{u[:4]}-{u[4:8]}"


def process_generation_job(job_id: str):
    """
    Background worker function that processes a bulk certificate generation job.
    Uses its own DB session so it can run safely in background threads or tasks.
    """
    db: Session = SessionLocal()
    try:
        job: GenerationJob = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING.value
        db.commit()

        # Storage subfolder for this specific job
        job_storage_dir = Path(settings.STORAGE_DIR) / f"job_{job.id}"
        os.makedirs(job_storage_dir, exist_ok=True)

        recipients = db.query(JobRecipient).filter(JobRecipient.job_id == job.id).all()
        
        for recipient in recipients:
            # 1. Validate recipient data
            is_valid, err_msg = validate_recipient_data(
                name=recipient.name,
                email=recipient.email,
                custom_fields=recipient.custom_fields
            )

            if not is_valid:
                recipient.status = RecipientStatus.FAILED.value
                recipient.error_message = err_msg
                job.failed_count += 1
                job.processed_count += 1
                db.commit()
                continue

            # 2. Process Certificate Generation
            try:
                cert_code = generate_unique_cert_code()
                
                # Clean recipient name for filename
                safe_name = "".join(c if c.isalnum() else "_" for c in recipient.name.strip())
                file_name = f"Certificate_{safe_name}_{cert_code}.pdf"
                output_file_path = str(job_storage_dir / file_name)

                # Generate PDF
                generate_certificate_pdf(
                    recipient_name=recipient.name.strip(),
                    course_title=job.title.strip(),
                    issuer_name=job.issuer_name.strip(),
                    issue_date=job.issue_date.strip(),
                    certificate_code=cert_code,
                    output_path=output_file_path,
                    template_theme=job.template_theme
                )

                # Save Certificate record
                cert = Certificate(
                    id=str(uuid.uuid4()),
                    job_id=job.id,
                    recipient_id=recipient.id,
                    certificate_code=cert_code,
                    recipient_name=recipient.name.strip(),
                    course_title=job.title.strip(),
                    issuer_name=job.issuer_name.strip(),
                    issue_date=job.issue_date.strip(),
                    file_path=output_file_path,
                    file_name=file_name
                )
                db.add(cert)
                db.flush()

                # Update Recipient status
                recipient.status = RecipientStatus.SUCCESS.value
                job.success_count += 1
                job.processed_count += 1
                db.commit()

            except Exception as e:
                db.rollback()
                recipient.status = RecipientStatus.FAILED.value
                recipient.error_message = f"Certificate generation failed: {str(e)}"
                job.failed_count += 1
                job.processed_count += 1
                db.commit()

        # Update Final Job Status
        if job.failed_count == 0 and job.success_count > 0:
            job.status = JobStatus.COMPLETED.value
        elif job.success_count > 0 and job.failed_count > 0:
            job.status = JobStatus.PARTIALLY_FAILED.value
        elif job.success_count == 0 and job.failed_count > 0:
            job.status = JobStatus.FAILED.value
        else:
            job.status = JobStatus.COMPLETED.value
            
        db.commit()

    except Exception as exc:
        if job:
            job.status = JobStatus.FAILED.value
            db.commit()
    finally:
        db.close()
