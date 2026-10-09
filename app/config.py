import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/certificates.db"
    
    # Storage configuration
    STORAGE_DIR: Path = BASE_DIR / "generated_certificates"
    TEMP_DIR: Path = BASE_DIR / "temp_zips"
    
    # Base URL for Certificate Verification QR code link
    BASE_VERIFY_URL: str = "http://localhost:8000/api/v1/certificates/verify"
    
    # Maximum recipients per batch job
    MAX_RECIPIENTS_PER_JOB: int = 5000
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()


# Ensure required storage directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
