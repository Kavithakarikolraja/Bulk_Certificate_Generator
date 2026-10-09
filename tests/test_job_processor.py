import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.job import GenerationJob, JobRecipient, JobStatus, RecipientStatus
from app.models.certificate import Certificate
from app.services.job_processor import process_generation_job

@pytest.fixture
def db_session(tmp_path, monkeypatch):
    db_file = tmp_path / "test_processor.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Patch SessionLocal inside app.services.job_processor to use our test DB
    monkeypatch.setattr("app.services.job_processor.SessionLocal", TestingSessionLocal)
    
    db = TestingSessionLocal()
    yield db
    db.close()

def test_process_job_with_partial_failures(db_session):
    job_id = str(uuid.uuid4())
    job = GenerationJob(
        id=job_id,
        title="Data Science Bootcamp",
        issuer_name="AI School",
        issue_date="2026-10-09",
        template_theme="indigo",
        status=JobStatus.PENDING.value,
        total_count=3,
        processed_count=0,
        success_count=0,
        failed_count=0
    )
    db_session.add(job)

    # Valid recipient 1
    r1 = JobRecipient(id=str(uuid.uuid4()), job_id=job_id, name="Valid Recipient One", email="valid1@test.com")
    # Invalid recipient 2 (blank name)
    r2 = JobRecipient(id=str(uuid.uuid4()), job_id=job_id, name="", email="invalid@test.com")
    # Valid recipient 3
    r3 = JobRecipient(id=str(uuid.uuid4()), job_id=job_id, name="Valid Recipient Two", email="valid2@test.com")

    db_session.add_all([r1, r2, r3])
    db_session.commit()

    # Process job synchronously
    process_generation_job(job_id)

    db_session.refresh(job)
    assert job.status == JobStatus.PARTIALLY_FAILED.value
    assert job.total_count == 3
    assert job.processed_count == 3
    assert job.success_count == 2
    assert job.failed_count == 1

    # Check recipient statuses
    db_session.refresh(r1)
    db_session.refresh(r2)
    db_session.refresh(r3)

    assert r1.status == RecipientStatus.SUCCESS.value
    assert r1.certificate_id is not None

    assert r2.status == RecipientStatus.FAILED.value
    assert "required" in r2.error_message.lower()

    assert r3.status == RecipientStatus.SUCCESS.value
    assert r3.certificate_id is not None
