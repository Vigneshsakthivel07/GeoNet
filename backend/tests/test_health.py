import secrets

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app


def settings() -> Settings:
    return Settings(
        postgres_password=secrets.token_urlsafe(32),
        s3_access_key=secrets.token_hex(12),
        s3_secret_key=secrets.token_urlsafe(32),
        environment="test",
    )


def test_liveness_does_not_probe_dependencies():
    def fail_if_called(_):
        raise AssertionError("Liveness must not depend on infrastructure")

    with TestClient(create_app(settings(), probe=fail_if_called)) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


@pytest.mark.parametrize("failed", [None, "postgis", "redis", "object_storage"])
def test_readiness_reflects_each_dependency(failed):
    checks = {name: name != failed for name in ("postgis", "redis", "object_storage")}
    with TestClient(create_app(settings(), probe=lambda _: checks)) as client:
        response = client.get("/health/ready")
    assert response.status_code == (200 if failed is None else 503)
    assert response.json()["checks"] == checks


def test_empty_probe_result_is_not_ready():
    with TestClient(create_app(settings(), probe=lambda _: {})) as client:
        assert client.get("/health/ready").status_code == 503


def test_untrusted_host_is_rejected():
    with TestClient(create_app(settings())) as client:
        assert client.get("/health/live", headers={"host": "evil.invalid"}).status_code == 400


def test_cors_rejects_unconfigured_origin():
    with TestClient(create_app(settings())) as client:
        response = client.options("/health/live", headers={
            "Origin": "https://evil.invalid",
            "Access-Control-Request-Method": "GET",
        })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_metrics_use_bounded_route_labels():
    with TestClient(create_app(settings())) as client:
        client.get("/health/live")
        client.get("/unknown-sensitive-path")
        response = client.get("/metrics")
    assert response.status_code == 200
    assert 'route="/health/live"' in response.text
    assert 'route="unmatched"' in response.text
    assert "unknown-sensitive-path" not in response.text


def test_production_is_not_silently_enabled():
    with pytest.raises(ValidationError):
        Settings(environment="production")
