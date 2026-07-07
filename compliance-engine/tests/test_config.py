"""Configuration safety tests."""

import json

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_safe_production_configuration():
    settings = Settings(
        _env_file=None,
        APP_ENV="production",
        DEBUG=False,
        AUTO_CREATE_SCHEMA=False,
        DATABASE_URL="postgresql://user:pass@db.example/compflow",
        CORS_ORIGINS="https://app.example.com",
        FILE_STORAGE_BACKEND="database",
        API_KEY_BINDINGS=json.dumps({"COMP-001": ["secret-key"]}),
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD_HASH="pbkdf2_sha256$390000$00$11",
        ADMIN_SESSION_SECRET="a" * 32,
        ADMIN_COOKIE_SECURE=True,
    )

    assert settings.database_url_for_sqlalchemy.startswith("postgresql+asyncpg://")
    assert settings.api_key_bindings == {"COMP-001": ("secret-key",)}
    assert settings.admin_dashboard_configured is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("API_KEY_BINDINGS", ""),
        ("DATABASE_URL", "sqlite:///./unsafe.db"),
        ("FILE_STORAGE_BACKEND", "local"),
        ("AUTO_CREATE_SCHEMA", True),
        ("CORS_ORIGINS", "*"),
        ("ADMIN_USERNAME", ""),
        ("ADMIN_PASSWORD_HASH", ""),
        ("ADMIN_SESSION_SECRET", ""),
        ("ADMIN_SESSION_SECRET", "too-short"),
        ("ADMIN_COOKIE_SECURE", False),
    ],
)
def test_unsafe_production_configuration_is_rejected(field, value):
    config = {
        "_env_file": None,
        "APP_ENV": "production",
        "DEBUG": False,
        "AUTO_CREATE_SCHEMA": False,
        "DATABASE_URL": "postgresql://user:pass@db.example/compflow",
        "CORS_ORIGINS": "https://app.example.com",
        "FILE_STORAGE_BACKEND": "database",
        "API_KEY_BINDINGS": json.dumps({"COMP-001": ["secret-key"]}),
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD_HASH": "pbkdf2_sha256$390000$00$11",
        "ADMIN_SESSION_SECRET": "a" * 32,
        "ADMIN_COOKIE_SECURE": True,
    }
    config[field] = value

    with pytest.raises(ValidationError):
        Settings(**config)
