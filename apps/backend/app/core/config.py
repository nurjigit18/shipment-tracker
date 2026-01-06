from pydantic_settings import BaseSettings
from typing import List
import secrets
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS - can be JSON array string or list
    BACKEND_CORS_ORIGINS: List[str] = []

    # Environment
    ENVIRONMENT: str = "development"

    # Optional integrations (for future use)
    GOOGLE_SHEETS_CREDENTIALS_PATH: str | None = None
    GOOGLE_SHEETS_SPREADSHEET_ID: str | None = None
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    SENDGRID_API_KEY: str | None = None
    SENDGRID_FROM_EMAIL: str = "noreply@novaeris.net"

    class Config:
        env_file = ".env"
        case_sensitive = True

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            """Parse BACKEND_CORS_ORIGINS from JSON string if needed"""
            if field_name == "BACKEND_CORS_ORIGINS":
                try:
                    return json.loads(raw_val)
                except json.JSONDecodeError:
                    return [raw_val]
            return raw_val


settings = Settings()
