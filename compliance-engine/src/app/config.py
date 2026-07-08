"""
Application configuration using Pydantic Settings.
"""

import json
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
    API_KEY_BINDINGS: str = ""
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Administrator dashboard
    ADMIN_USERS: str = ""
    ADMIN_USERNAME: str = ""
    ADMIN_PASSWORD_HASH: str = ""
    ADMIN_SESSION_SECRET: str = ""
    ADMIN_SESSION_TTL_SECONDS: int = 8 * 60 * 60
    ADMIN_COOKIE_SECURE: bool = False

    # Alert delivery
    ALERT_WEBHOOK_URL: str = ""
    ALERT_WEBHOOK_TIMEOUT_SECONDS: int = 5
    ALERT_DEDUP_WINDOW_SECONDS: int = 15 * 60
    ALERT_SEVERITIES: str = "critical,warning"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Reject unsafe production configuration at process startup."""
        if self.APP_ENV != "production":
            return self

        if self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        if not self.api_key_bindings:
            raise ValueError("API_KEY_BINDINGS must contain at least one company in production")
        admin_users = self.admin_user_configs
        if not admin_users:
            raise ValueError(
                "ADMIN_USERS and ADMIN_SESSION_SECRET must be configured in production"
            )
        if not any(user["role"] == "admin" for user in admin_users.values()):
            raise ValueError("ADMIN_USERS must contain at least one administrator in production")
        if len(self.ADMIN_SESSION_SECRET) < 32:
            raise ValueError("ADMIN_SESSION_SECRET must be at least 32 characters in production")
        if not self.ADMIN_COOKIE_SECURE:
            raise ValueError("ADMIN_COOKIE_SECURE must be true in production")
        if not self.alert_delivery_configured:
            raise ValueError("ALERT_WEBHOOK_URL must be configured in production")
        if not self.ALERT_WEBHOOK_URL.startswith("https://"):
            raise ValueError("ALERT_WEBHOOK_URL must use https in production")
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
    def api_key_bindings(self) -> dict[str, tuple[str, ...]]:
        """
        Return company-to-key bindings.

        Format:
        {"COMPANY_ID": ["active-key", "rotation-key"]}
        """
        if not self.API_KEY_BINDINGS.strip():
            return {}

        try:
            raw = json.loads(self.API_KEY_BINDINGS)
        except json.JSONDecodeError as exc:
            raise ValueError("API_KEY_BINDINGS must be valid JSON") from exc

        if not isinstance(raw, dict):
            raise ValueError("API_KEY_BINDINGS must be a JSON object")

        bindings: dict[str, tuple[str, ...]] = {}
        for company_id, keys in raw.items():
            if not isinstance(company_id, str) or not company_id.strip():
                raise ValueError("API_KEY_BINDINGS company IDs must be non-empty strings")
            if not isinstance(keys, list):
                raise ValueError("Each API_KEY_BINDINGS value must be a JSON array")
            normalized = tuple(key.strip() for key in keys if isinstance(key, str) and key.strip())
            if not normalized:
                raise ValueError(f"Company {company_id!r} must have at least one API key")
            bindings[company_id.strip()] = normalized

        return bindings

    @property
    def admin_dashboard_configured(self) -> bool:
        """Return whether administrator login has all required secrets configured."""
        return bool(self.admin_user_configs and self.ADMIN_SESSION_SECRET.strip())

    @property
    def admin_user_configs(self) -> dict[str, dict[str, str]]:
        """
        Return administrator user configuration.

        Preferred production format:
        {
          "admin@example.com": {
            "password_hash": "pbkdf2_sha256$...",
            "role": "admin"
          }
        }

        Supported roles: admin, operator, viewer.
        """
        allowed_roles = {"admin", "operator", "viewer"}
        if self.ADMIN_USERS.strip():
            try:
                raw = json.loads(self.ADMIN_USERS)
            except json.JSONDecodeError as exc:
                raise ValueError("ADMIN_USERS must be valid JSON") from exc

            if not isinstance(raw, dict):
                raise ValueError("ADMIN_USERS must be a JSON object")

            users: dict[str, dict[str, str]] = {}
            for username, config in raw.items():
                if not isinstance(username, str) or not username.strip():
                    raise ValueError("ADMIN_USERS usernames must be non-empty strings")
                if not isinstance(config, dict):
                    raise ValueError("Each ADMIN_USERS value must be an object")
                password_hash = config.get("password_hash")
                role = config.get("role", "viewer")
                if not isinstance(password_hash, str) or not password_hash.strip():
                    raise ValueError(f"Admin user {username!r} must have a password_hash")
                if not isinstance(role, str) or role not in allowed_roles:
                    raise ValueError(
                        f"Admin user {username!r} role must be one of "
                        f"{', '.join(sorted(allowed_roles))}"
                    )
                users[username.strip()] = {
                    "password_hash": password_hash.strip(),
                    "role": role,
                }

            return users

        if self.ADMIN_USERNAME.strip() and self.ADMIN_PASSWORD_HASH.strip():
            return {
                self.ADMIN_USERNAME.strip(): {
                    "password_hash": self.ADMIN_PASSWORD_HASH.strip(),
                    "role": "admin",
                }
            }

        return {}

    @property
    def alert_severities_list(self) -> tuple[str, ...]:
        """Return alert severities that should be delivered externally."""
        return tuple(
            severity.strip()
            for severity in self.ALERT_SEVERITIES.split(",")
            if severity.strip()
        )

    @property
    def alert_delivery_configured(self) -> bool:
        """Return whether outbound alert delivery is configured."""
        return bool(self.ALERT_WEBHOOK_URL.strip())

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
