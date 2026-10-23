from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "FinPilot AI"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "change-this-in-production-to-a-secure-random-32-char-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str = "sqlite:///./finpilot.db"
    
    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # AI Configuration (Cloud-only Gemini & Deterministic Mock)
    LLM_PROVIDER: str = "mock"  # mock, gemini
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TIMEOUT_SECONDS: float = 15.0

    # Firebase Authentication
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_CREDENTIALS_PATH: str = ""
    ALLOW_MOCK_FIREBASE: bool = True  # Strictly ignored and rejected if ENVIRONMENT == 'production'

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
