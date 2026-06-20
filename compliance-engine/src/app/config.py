"""
Application configuration using Pydantic Settings.
"""

from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "compliance-engine"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024
    AUTO_CREATE_SCHEMA: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # File Storage
    FILE_STORAGE_PATH: str = "./storage/files"
    FILE_STORAGE_BACKEND: Literal["local", "database"] = "local"

    # Logging
    LOG_LEVEL: str = "INFO"

    # API
    API_V1_PREFIX: str = "/api/v1"
    API_KEYS: str = ""

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Reject unsafe production configuration at process startup."""
        if self.APP_ENV != "production":
            return self

        if self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        if not self.api_keys_list:
            raise ValueError("API_KEYS must contain at least one key in production")
        if self.database_url_for_sqlalchemy.startswith("sqlite"):
            raise ValueError("Production requires PostgreSQL; SQLite is not supported")
        if self.FILE_STORAGE_BACKEND != "database":
            raise ValueError("Production requires FILE_STORAGE_BACKEND=database")
        if not self.cors_origins_list or any(
            origin == "*" or "YOUR-" in origin for origin in self.cors_origins_list
        ):
            raise ValueError("CORS_ORIGINS must contain explicit production origins")
        if self.AUTO_CREATE_SCHEMA:
            raise ValueError("AUTO_CREATE_SCHEMA must be false in production; use Alembic")

        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def api_keys_list(self) -> list[str]:
        """Return configured API keys without empty values."""
        return [key.strip() for key in self.API_KEYS.split(",") if key.strip()]

    @property
    def database_url_for_sqlalchemy(self) -> str:
        """Return DATABASE_URL normalized for SQLAlchemy async drivers."""
        database_url = self.DATABASE_URL.strip()

        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql+asyncpg://", 1)

        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        if database_url.startswith("postgresql+asyncpg://"):
            return database_url

        if database_url.startswith("sqlite+aiosqlite://"):
            return database_url

        if database_url.startswith("sqlite://"):
            return database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

        raise ValueError("DATABASE_URL must use sqlite, postgresql, or postgres")

    @property
    def storage_path(self) -> Path:
        """Get file storage path as Path object."""
        path = Path(self.FILE_STORAGE_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.APP_ENV == "production"


settings = Settings()
