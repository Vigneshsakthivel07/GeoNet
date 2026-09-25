import json
import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def available():
    return None


def unavailable():
    raise RuntimeError("secret-password-must-not-leak")


def test_liveness_is_independent_of_dependencies():
    with TestClient(create_app({"database": unavailable})) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
    assert uuid.UUID(response.headers["X-Request-ID"])
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"


def test_readiness_checks_all_dependencies():
    checks = dict.fromkeys(["database", "redis", "object_storage"], available)
    with TestClient(create_app(checks)) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok", "redis": "ok", "object_storage": "ok"},
    }


@pytest.mark.parametrize("failed", ["database", "redis", "object_storage"])
def test_dependency_failure_is_not_ready_and_does_not_leak(failed):
    checks = dict.fromkeys(["database", "redis", "object_storage"], available)
    checks[failed] = unavailable
    with TestClient(create_app(checks)) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"][failed] == "unavailable"
    assert "secret-password" not in response.text


def test_no_checks_cannot_claim_readiness():
    with TestClient(create_app({})) as client:
        assert client.get("/health/ready").status_code == 503


def test_metrics_are_exposed():
    with TestClient(create_app({"database": available})) as client:
        client.get("/health/live")
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "geonet_http_requests_total" in response.text
    assert "geonet_http_request_seconds" in response.text


def test_wildcard_cors_is_rejected(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(ValueError, match="explicit origins"):
        create_app({})


def test_cors_allows_only_configured_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    with TestClient(create_app({})) as client:
        allowed = client.get("/health/live", headers={"Origin": "http://localhost:3000"})
        denied = client.get("/health/live", headers={"Origin": "https://untrusted.invalid"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in denied.headers


def test_structured_logs_do_not_record_query_strings_or_authorization():
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(json.loads(record.getMessage()))

    logger = logging.getLogger("geonet")
    handler = Capture()
    logger.addHandler(handler)
    try:
        with TestClient(create_app({})) as client:
            client.get("/health/live?token=private-value", headers={"Authorization": "Bearer secret"})
    finally:
        logger.removeHandler(handler)
    assert len(records) == 1
    assert records[0]["route"] == "/health/live"
    assert records[0]["status"] == 200
    assert "private-value" not in json.dumps(records)
    assert "Bearer secret" not in json.dumps(records)


def test_missing_configuration_fails_readiness_not_liveness(monkeypatch):
    for variable in ("POSTGRES_HOST", "REDIS_HOST", "S3_ENDPOINT_URL"):
        monkeypatch.delenv(variable, raising=False)
    with TestClient(create_app()) as client:
        assert client.get("/health/live").status_code == 200
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert set(response.json()["checks"].values()) == {"unavailable"}
