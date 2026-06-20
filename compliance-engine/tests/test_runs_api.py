"""Integration tests for the public compliance-run API."""

import json

from app.api.v1 import routes_runs
from app.config import settings


def _csv(basic_salary: str = "25000") -> bytes:
    return (
        "payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,"
        "employee_id,employment_type,basic_salary,annual_payroll_estimate\n"
        f"PAY-2026-001,COMP-001,2026-04-30,2026_27,monthly,"
        f"EMP-001,employee,{basic_salary},750000\n"
    ).encode()


async def _fake_store_raw_file(content: bytes, filename: str) -> str:
    return "test-raw-file.csv"


def test_create_run_success(client, monkeypatch):
    """A valid CSV should complete through the real API route."""
    monkeypatch.setattr(routes_runs, "store_raw_file", _fake_store_raw_file)

    response = client.post(
        "/api/v1/runs",
        files={"file": ("payroll.csv", _csv(), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["payroll_run_id"] == "PAY-2026-001"
    assert body["ruleset_version_used"] == "ZA_2026_27_v1"
    assert body["totals"]["employee_count"] == 1

    detail = client.get(f"/api/v1/runs/{body['run_id']}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"


def test_validation_failure_is_persisted_as_failed(client, monkeypatch):
    """Blocking validation errors must not be labelled completed."""
    monkeypatch.setattr(routes_runs, "store_raw_file", _fake_store_raw_file)

    response = client.post(
        "/api/v1/runs",
        files={"file": ("payroll.csv", _csv(basic_salary="0"), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["issue_count"]["errors"] >= 1
    assert body["totals"] is None

    detail = client.get(f"/api/v1/runs/{body['run_id']}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "failed"


def test_schema_error_remains_client_error(client, monkeypatch):
    """A malformed CSV should return 400 rather than being wrapped as 500."""
    monkeypatch.setattr(routes_runs, "store_raw_file", _fake_store_raw_file)

    response = client.post(
        "/api/v1/runs",
        files={"file": ("payroll.csv", b"employee_id\nEMP-001\n", "text/csv")},
    )

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_upload_size_limit(client, monkeypatch):
    """Oversized uploads should be rejected before parsing or storage."""
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 8)
    monkeypatch.setattr(routes_runs, "store_raw_file", _fake_store_raw_file)

    response = client.post(
        "/api/v1/runs",
        files={"file": ("payroll.csv", b"123456789", "text/csv")},
    )

    assert response.status_code == 413


def test_api_key_protects_payroll_routes(client, monkeypatch):
    """Configured API keys must protect payroll data endpoints."""
    monkeypatch.setattr(
        settings,
        "API_KEY_BINDINGS",
        json.dumps({"COMP-001": ["test-secret"]}),
    )
    monkeypatch.setattr(routes_runs, "store_raw_file", _fake_store_raw_file)

    unauthorized = client.post(
        "/api/v1/runs",
        files={"file": ("payroll.csv", _csv(), "text/csv")},
    )
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/api/v1/runs",
        headers={"X-API-Key": "test-secret"},
        files={"file": ("payroll.csv", _csv(), "text/csv")},
    )
    assert authorized.status_code == 200


def test_tenant_isolation_for_uploads_and_reads(client, monkeypatch):
    """A company key must not create or retrieve another company's runs."""
    monkeypatch.setattr(
        settings,
        "API_KEY_BINDINGS",
        json.dumps(
            {
                "COMP-001": ["company-one-key"],
                "COMP-002": ["company-two-key"],
            }
        ),
    )
    monkeypatch.setattr(routes_runs, "store_raw_file", _fake_store_raw_file)

    created = client.post(
        "/api/v1/runs",
        headers={"X-API-Key": "company-one-key"},
        files={"file": ("payroll.csv", _csv(), "text/csv")},
    )
    assert created.status_code == 200
    run_id = created.json()["run_id"]

    hidden = client.get(
        f"/api/v1/runs/{run_id}",
        headers={"X-API-Key": "company-two-key"},
    )
    assert hidden.status_code == 404

    hidden_export = client.get(
        f"/api/v1/runs/{run_id}/export/employee-breakdown.csv",
        headers={"X-API-Key": "company-two-key"},
    )
    assert hidden_export.status_code == 404

    mismatched_upload = client.post(
        "/api/v1/runs",
        headers={"X-API-Key": "company-two-key"},
        files={"file": ("payroll.csv", _csv(), "text/csv")},
    )
    assert mismatched_upload.status_code == 403


def test_rate_limit_returns_retry_after(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "API_KEY_BINDINGS",
        json.dumps({"COMP-001": ["rate-key"]}),
    )
    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)

    first = client.get(
        "/api/v1/runs/missing",
        headers={"X-API-Key": "rate-key"},
    )
    second = client.get(
        "/api/v1/runs/missing",
        headers={"X-API-Key": "rate-key"},
    )

    assert first.status_code == 404
    assert second.status_code == 429
    assert second.headers["Retry-After"]


def test_audit_request_id_is_returned(client):
    response = client.get("/health", headers={"X-Request-ID": "request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"


def test_unpersisted_evidence_is_deleted(client, monkeypatch):
    deleted: list[str] = []

    async def fail_persistence(run) -> None:
        raise RuntimeError("database unavailable")

    async def record_delete(file_id: str) -> bool:
        deleted.append(file_id)
        return True

    monkeypatch.setattr(routes_runs, "store_raw_file", _fake_store_raw_file)
    monkeypatch.setattr(routes_runs, "persist_compliance_run", fail_persistence)
    monkeypatch.setattr(routes_runs, "delete_raw_file", record_delete)

    response = client.post(
        "/api/v1/runs",
        files={"file": ("payroll.csv", _csv(), "text/csv")},
    )

    assert response.status_code == 500
    assert deleted == ["test-raw-file.csv"]
