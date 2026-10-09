from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CertificateResponse(BaseModel):
    id: str
    job_id: str
    recipient_id: str
    certificate_code: str
    recipient_name: str
    course_title: str
    issuer_name: str
    issue_date: str
    file_name: str
    download_url: str
    verify_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class CertificateVerificationResponse(BaseModel):
    is_valid: bool = Field(..., description="True if the certificate code is authentic and valid")
    certificate_code: Optional[str] = None
    recipient_name: Optional[str] = None
    course_title: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[str] = None
    issued_at: Optional[datetime] = None
    download_url: Optional[str] = None
    message: str
