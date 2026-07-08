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
        ADMIN_USERS=json.dumps(
            {"admin": {"password_hash": "pbkdf2_sha256$390000$00$11", "role": "admin"}}
        ),
        ADMIN_SESSION_SECRET="a" * 32,
        ADMIN_COOKIE_SECURE=True,
        ALERT_WEBHOOK_URL="https://alerts.example/webhook",
    )

    assert settings.database_url_for_sqlalchemy.startswith("postgresql+asyncpg://")
    assert settings.api_key_bindings == {"COMP-001": ("secret-key",)}
    assert settings.admin_dashboard_configured is True
    assert settings.admin_user_configs["admin"]["role"] == "admin"
    assert settings.alert_delivery_configured is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("API_KEY_BINDINGS", ""),
        ("DATABASE_URL", "sqlite:///./unsafe.db"),
        ("FILE_STORAGE_BACKEND", "local"),
        ("AUTO_CREATE_SCHEMA", True),
        ("CORS_ORIGINS", "*"),
        ("ADMIN_USERS", ""),
        (
            "ADMIN_USERS",
            json.dumps(
                {"viewer": {"password_hash": "pbkdf2_sha256$390000$00$11", "role": "viewer"}}
            ),
        ),
        ("ADMIN_SESSION_SECRET", ""),
        ("ADMIN_SESSION_SECRET", "too-short"),
        ("ADMIN_COOKIE_SECURE", False),
        ("ALERT_WEBHOOK_URL", ""),
        ("ALERT_WEBHOOK_URL", "http://alerts.example/webhook"),
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
        "ADMIN_USERS": json.dumps(
            {"admin": {"password_hash": "pbkdf2_sha256$390000$00$11", "role": "admin"}}
        ),
        "ADMIN_SESSION_SECRET": "a" * 32,
        "ADMIN_COOKIE_SECURE": True,
        "ALERT_WEBHOOK_URL": "https://alerts.example/webhook",
    }
    config[field] = value

    with pytest.raises(ValidationError):
        Settings(**config)
