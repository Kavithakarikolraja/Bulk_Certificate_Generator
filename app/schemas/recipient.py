from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class RecipientBase(BaseModel):
    name: Optional[str] = Field(None, description="Recipient full name")
    email: Optional[str] = Field(None, description="Recipient email address")
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional custom key-value data")

class RecipientCreate(RecipientBase):
    pass

class RecipientResponse(RecipientBase):
    id: str
    job_id: str
    status: str
    error_message: Optional[str] = None
    certificate_id: Optional[str] = None
    certificate_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
