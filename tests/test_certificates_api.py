import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.job import GenerationJob, JobRecipient, JobStatus, RecipientStatus
from app.models.certificate import Certificate

@pytest.fixture
def client_with_data(tmp_path):
    db_file = tmp_path / "test_cert_api.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    
    # Create test job & certificate
    job_id = str(uuid.uuid4())
    recip_id = str(uuid.uuid4())
    cert_id = str(uuid.uuid4())
    cert_code = "CERT-TEST-VERIFY"

    # Create dummy pdf file
    pdf_path = os.path.join(tmp_path, "dummy.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 dummy content")

    cert = Certificate(
        id=cert_id,
        job_id=job_id,
        recipient_id=recip_id,
        certificate_code=cert_code,
        recipient_name="Sam Test",
        course_title="Testing Mastery",
        issuer_name="QA Org",
        issue_date="2026-10-09",
        file_path=str(pdf_path),
        file_name="dummy.pdf"
    )
    db.add(cert)
    db.commit()
    db.close()

    def override_get_db():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c, cert_id, cert_code
    app.dependency_overrides.clear()


def test_verify_certificate_valid(client_with_data):
    client, cert_id, cert_code = client_with_data
    response = client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["recipient_name"] == "Sam Test"
    assert data["course_title"] == "Testing Mastery"


def test_verify_certificate_invalid(client_with_data):
    client, _, _ = client_with_data
    response = client.get("/api/v1/certificates/verify/NON-EXISTENT-CODE")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert "not found" in data["message"].lower()


def test_download_certificate_pdf(client_with_data):
    client, cert_id, _ = client_with_data
    response = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert b"%PDF-1.4" in response.content
