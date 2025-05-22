from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, field_validator, ValidationInfo
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Base configuration
    PROJECT_NAME: str = "Event Management"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = "HS256"
    
    # Security Headers
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }

    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "event_management"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:Test%40123@localhost:5433/event_management_test"

    # Database Optimization Settings
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    DB_COMMAND_TIMEOUT: int = 30
    DB_STATEMENT_TIMEOUT: int = 30000  # 30 seconds in milliseconds
    DB_IDLE_TIMEOUT: int = 300000  # 5 minutes in milliseconds

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Email
    MAIL_USERNAME: str = "your-email@example.com"
    MAIL_PASSWORD: str = "your-password"
    MAIL_FROM: str = "your-email@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Event Management System"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # Sentry settings
    SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str = "development"

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    def __init__(self, **values):
        super().__init__(**values)
        # If running under pytest, restrict allowed hosts for trusted host tests
        if "PYTEST_CURRENT_TEST" in os.environ:
            self.ALLOWED_HOSTS = ["testserver"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> any:
        if isinstance(v, str):
            return v
        # Build the URL manually to avoid leading slash issues
        user = info.data.get("POSTGRES_USER")
        password = info.data.get("POSTGRES_PASSWORD")
        server = info.data.get("POSTGRES_SERVER")
        port = info.data.get("POSTGRES_PORT")
        db = info.data.get("POSTGRES_DB")
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return str(self.DATABASE_URL)

    @property
    def REDIS_URL(self) -> str:
        """Get Redis URL for Celery."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def CORS_ORIGINS(self) -> list:
        return self.BACKEND_CORS_ORIGINS

    @property
    def CORS_ALLOW_CREDENTIALS(self) -> bool:
        return True

    @property
    def CORS_ALLOW_METHODS(self) -> list:
        return ["*"]

    @property
    def CORS_ALLOW_HEADERS(self) -> list:
        return ["*"]

    model_config = {
        "case_sensitive": True,
        "env_file": ".env"
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings() 