from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.recipient import RecipientCreate, RecipientResponse

class JobCreateRequest(BaseModel):
    title: str = Field("Certificate Course", description="Course or Event Title")
    issuer_name: str = Field("Tech Academy", description="Issuing organization or authority")
    issue_date: str = Field("2026-10-09", description="Date of issuance (e.g. 2026-10-09)")
    template_theme: str = Field("gold", description="Template visual theme: gold, indigo, emerald, or crimson")
    recipients: List[RecipientCreate] = Field(default_factory=list, description="List of recipient details")

class JobProgressSummary(BaseModel):
    total: int
    processed: int
    successful: int
    failed: int
    percentage: float

class JobResponse(BaseModel):
    id: str
    title: str
    issuer_name: str
    issue_date: str
    template_theme: str
    status: str
    progress: JobProgressSummary
    recipients: Optional[List[RecipientResponse]] = None
    download_zip_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total_count: int
