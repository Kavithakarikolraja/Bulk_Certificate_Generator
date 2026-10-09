import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.certificate import Certificate
from app.schemas.certificate import CertificateResponse, CertificateVerificationResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("/verify/{certificate_code}", response_model=CertificateVerificationResponse)
def verify_certificate(certificate_code: str, db: Session = Depends(get_db)):
    """
    Public API endpoint to verify certificate authenticity by its unique code.
    Used by QR codes and public verification portals.
    """
    clean_code = certificate_code.strip().upper()
    cert = db.query(Certificate).filter(Certificate.certificate_code == clean_code).first()

    if not cert:
        return CertificateVerificationResponse(
            is_valid=False,
            certificate_code=clean_code,
            message="Certificate code not found in official verification records."
        )

    download_url = f"{settings.API_V1_STR}/certificates/{cert.id}/download"

    return CertificateVerificationResponse(
        is_valid=True,
        certificate_code=cert.certificate_code,
        recipient_name=cert.recipient_name,
        course_title=cert.course_title,
        issuer_name=cert.issuer_name,
        issue_date=cert.issue_date,
        issued_at=cert.created_at,
        download_url=download_url,
        message="Certificate is authentic and verified."
    )


@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """
    Downloads an individual generated certificate PDF file by certificate ID.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate with ID '{certificate_id}' not found.")

    if not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate PDF file is missing on storage server.")

    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=cert.file_name
    )
