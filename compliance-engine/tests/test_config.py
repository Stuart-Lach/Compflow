"""Configuration safety tests."""

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
        API_KEYS="secret-key",
    )

    assert settings.database_url_for_sqlalchemy.startswith("postgresql+asyncpg://")
    assert settings.api_keys_list == ["secret-key"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("API_KEYS", ""),
        ("DATABASE_URL", "sqlite:///./unsafe.db"),
        ("FILE_STORAGE_BACKEND", "local"),
        ("AUTO_CREATE_SCHEMA", True),
        ("CORS_ORIGINS", "*"),
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
        "API_KEYS": "secret-key",
    }
    config[field] = value

    with pytest.raises(ValidationError):
        Settings(**config)
