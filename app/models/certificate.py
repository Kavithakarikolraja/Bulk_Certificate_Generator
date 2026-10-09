import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=False)
    recipient_id = Column(String(36), ForeignKey("job_recipients.id"), nullable=False)
    
    certificate_code = Column(String(100), unique=True, nullable=False, index=True)
    recipient_name = Column(String(255), nullable=False)
    course_title = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    # Relationships
    job = relationship("GenerationJob", back_populates="certificates")
    recipient = relationship("JobRecipient", back_populates="certificate")
