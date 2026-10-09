import os
import tempfile
import pytest
from app.services.generator import generate_certificate_pdf

def test_generate_certificate_pdf_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_cert.pdf")
        result_path = generate_certificate_pdf(
            recipient_name="Alice Smith",
            course_title="Python Microservices",
            issuer_name="Test Academy",
            issue_date="2026-10-09",
            certificate_code="CERT-TEST-001",
            output_path=output_path,
            template_theme="gold"
        )
        
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 1000  # Non-empty PDF
        
        with open(result_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"
