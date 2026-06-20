"""Operational readiness endpoint tests."""


def test_readiness_checks_database_and_ruleset(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["database"] == "ok"
    assert response.json()["checks"]["ruleset"] == "ZA_2026_27_v1"
