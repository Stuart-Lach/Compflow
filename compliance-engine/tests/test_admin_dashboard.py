"""Administrator dashboard authentication and monitoring tests."""

import json

from app.admin.security import hash_admin_password
from app.api.v1 import routes_runs
from app.config import settings


def _configure_admin(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(
        settings,
        "ADMIN_PASSWORD_HASH",
        hash_admin_password("correct-password", "00" * 16),
    )
    monkeypatch.setattr(settings, "ADMIN_SESSION_SECRET", "test-secret-" * 4)
    monkeypatch.setattr(settings, "ADMIN_SESSION_TTL_SECONDS", 3600)
    monkeypatch.setattr(settings, "ADMIN_COOKIE_SECURE", False)


def _csv() -> bytes:
    return (
        b"payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,"
        b"employee_id,employment_type,basic_salary,annual_payroll_estimate\n"
        b"PAY-ADMIN-001,COMP-001,2026-04-30,2026_27,monthly,"
        b"EMP-001,employee,25000,750000\n"
    )


async def _fake_store_raw_file(content: bytes, filename: str) -> str:
    return "admin-test-raw-file.csv"


def test_admin_dashboard_requires_login(client):
    dashboard = client.get("/admin/dashboard", follow_redirects=False)
    overview = client.get("/admin/api/overview")

    assert dashboard.status_code == 303
    assert dashboard.headers["location"] == "/admin/login"
    assert overview.status_code == 401


def test_admin_login_rejects_invalid_credentials(client, monkeypatch):
    _configure_admin(monkeypatch)

    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong"},
    )

    assert response.status_code == 401
    assert "Invalid administrator username or password" in response.text


def test_admin_login_allows_dashboard_and_overview(client, monkeypatch):
    _configure_admin(monkeypatch)
    monkeypatch.setattr(routes_runs, "store_raw_file", _fake_store_raw_file)

    created = client.post(
        "/api/v1/runs",
        files={"file": ("payroll.csv", _csv(), "text/csv")},
    )
    assert created.status_code == 200

    login = client.post(
        "/admin/login",
        data={"username": "admin", "password": "correct-password"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    assert login.headers["location"] == "/admin/dashboard"

    dashboard = client.get("/admin/dashboard")
    assert dashboard.status_code == 200
    assert "Admin Dashboard" in dashboard.text
    assert "administrator" in dashboard.text.lower()

    overview = client.get("/admin/api/overview")
    assert overview.status_code == 200
    body = overview.json()
    assert body["admin_only"] is True
    assert body["network"]["required"] is True
    assert body["metrics"]["runs_total"] == 1
    assert body["recent_runs"][0]["payroll_run_id"] == "PAY-ADMIN-001"


def test_admin_rate_limit_reset_is_protected(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "API_KEY_BINDINGS",
        json.dumps({"COMP-001": ["rate-key"]}),
    )
    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)

    first = client.get("/api/v1/runs/missing", headers={"X-API-Key": "rate-key"})
    second = client.get("/api/v1/runs/missing", headers={"X-API-Key": "rate-key"})
    unauthenticated_reset = client.post("/admin/api/maintenance/rate-limit/reset")

    assert first.status_code == 404
    assert second.status_code == 429
    assert unauthenticated_reset.status_code == 401

    _configure_admin(monkeypatch)
    login = client.post(
        "/admin/login",
        data={"username": "admin", "password": "correct-password"},
        follow_redirects=False,
    )
    assert login.status_code == 303

    reset = client.post("/admin/api/maintenance/rate-limit/reset")
    after_reset = client.get("/api/v1/runs/missing", headers={"X-API-Key": "rate-key"})

    assert reset.status_code == 200
    assert reset.json()["status"] == "ok"
    assert after_reset.status_code == 404
