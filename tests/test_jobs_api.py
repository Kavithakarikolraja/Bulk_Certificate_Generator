import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "test_api.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_job_json_api(client):
    payload = {
        "title": "FastAPI Masterclass",
        "issuer_name": "Backend Academy",
        "issue_date": "2026-10-09",
        "template_theme": "gold",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@test.com"},
            {"name": "Bob Smith", "email": "bob@test.com"}
        ]
    }
    response = client.post("/api/v1/jobs/generate", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["title"] == "FastAPI Masterclass"
    assert data["progress"]["total"] == 2


def test_create_job_csv_upload_api(client):
    csv_data = "name,email\nCharlie Brown,charlie@test.com\nDiana Prince,diana@test.com\n"
    files = {"file": ("test.csv", csv_data, "text/csv")}
    data = {
        "title": "Cloud Computing Workshop",
        "issuer_name": "Tech Corp",
        "issue_date": "2026-10-09",
        "template_theme": "emerald"
    }
    response = client.post("/api/v1/jobs/upload-csv", data=data, files=files)
    assert response.status_code == 202
    job_data = response.json()
    assert job_data["progress"]["total"] == 2


def test_get_job_status_api(client):
    # First create a job
    payload = {
        "title": "Security Engineering",
        "issuer_name": "SecAcademy",
        "issue_date": "2026-10-09",
        "template_theme": "crimson",
        "recipients": [{"name": "Eve Adams", "email": "eve@test.com"}]
    }
    res_create = client.post("/api/v1/jobs/generate", json=payload)
    job_id = res_create.json()["id"]

    # Query status
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    job_info = response.json()
    assert job_info["id"] == job_id
    assert len(job_info["recipients"]) == 1


def test_list_jobs_api(client):
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total_count" in data
