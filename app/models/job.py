import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class JobStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"
    FAILED = "FAILED"

class RecipientStatus(str, PyEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False, default="Organization")
    issue_date = Column(String(50), nullable=False)
    template_theme = Column(String(50), nullable=False, default="gold")
    
    status = Column(String(50), nullable=False, default=JobStatus.PENDING.value)
    total_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


    # Relationships
    recipients = relationship("JobRecipient", back_populates="job", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")


class JobRecipient(Base):
    __tablename__ = "job_recipients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    custom_fields = Column(JSON, nullable=True)
    
    status = Column(String(50), nullable=False, default=RecipientStatus.PENDING.value)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    # Relationships
    job = relationship("GenerationJob", back_populates="recipients")
    certificate = relationship("Certificate", back_populates="recipient", uselist=False)

    @property
    def certificate_id(self):
        return self.certificate.id if self.certificate else None

