"""Characterize real dependency-probe control flow without network access."""

import secrets
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings


@pytest.fixture
def settings():
    return Settings(
        environment="test",
        postgres_password=secrets.token_urlsafe(32),
        s3_access_key=secrets.token_hex(12),
        s3_secret_key=secrets.token_urlsafe(32),
    )


@pytest.fixture
def clients(monkeypatch):
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = ("3.4",)
    database_context = MagicMock()
    database_context.__enter__.return_value = connection
    connect = MagicMock(return_value=database_context)
    monkeypatch.setattr(main.psycopg, "connect", connect)

    redis = MagicMock()
    redis.ping.return_value = True
    redis_context = MagicMock()
    redis_context.__enter__.return_value = redis
    redis_factory = MagicMock(return_value=redis_context)
    monkeypatch.setattr(main.Redis, "from_url", redis_factory)

    storage = MagicMock()
    storage_factory = MagicMock(return_value=storage)
    monkeypatch.setattr(main.boto3, "client", storage_factory)
    return SimpleNamespace(
        connect=connect,
        database_context=database_context,
        connection=connection,
        redis_factory=redis_factory,
        redis_context=redis_context,
        redis=redis,
        storage_factory=storage_factory,
        storage=storage,
    )


def test_success_checks_postgis_redis_and_bucket(settings, clients):
    assert main.check_dependencies(settings) == {
        "postgis": True,
        "redis": True,
        "object_storage": True,
    }
    clients.connect.assert_called_once_with(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        connect_timeout=2,
        options="-c statement_timeout=2000",
    )
    clients.connection.execute.assert_called_once_with("SELECT PostGIS_Version()")
    clients.redis_factory.assert_called_once_with(
        settings.redis_url, socket_connect_timeout=2, socket_timeout=2
    )
    clients.redis.ping.assert_called_once_with()
    clients.storage_factory.assert_called_once()
    args, kwargs = clients.storage_factory.call_args
    assert args == ("s3",)
    assert kwargs["endpoint_url"] == settings.s3_endpoint
    assert kwargs["aws_access_key_id"] == settings.s3_access_key.get_secret_value()
    assert kwargs["aws_secret_access_key"] == settings.s3_secret_key.get_secret_value()
    assert kwargs["region_name"] == "us-east-1"
    config = kwargs["config"]
    assert config.connect_timeout == 2
    assert config.read_timeout == 2
    assert config.retries == {"max_attempts": 0}
    assert config.s3 == {"addressing_style": "path"}
    clients.storage.head_bucket.assert_called_once_with(Bucket=settings.s3_bucket)
    clients.storage.close.assert_called_once_with()
    clients.database_context.__exit__.assert_called_once()
    clients.redis_context.__exit__.assert_called_once()


@pytest.mark.parametrize("row", [None, (), (None,), ("",)])
def test_missing_postgis_version_is_not_ready(settings, clients, row):
    clients.connection.execute.return_value.fetchone.return_value = row
    assert main.check_dependencies(settings) == {
        "postgis": False, "redis": True, "object_storage": True
    }


@pytest.mark.parametrize("result", [False, None, 0])
def test_negative_redis_ping_is_not_ready(settings, clients, result):
    clients.redis.ping.return_value = result
    assert main.check_dependencies(settings) == {
        "postgis": True, "redis": False, "object_storage": True
    }


@pytest.mark.parametrize(
    ("failure", "dependency"),
    [
        ("database_factory", "postgis"),
        ("database_enter", "postgis"),
        ("database_query", "postgis"),
        ("database_fetch", "postgis"),
        ("redis_factory", "redis"),
        ("redis_enter", "redis"),
        ("redis_ping", "redis"),
        ("storage_factory", "object_storage"),
        ("storage_head", "object_storage"),
    ],
)
def test_dependency_failures_are_isolated(settings, clients, failure, dependency):
    operations = {
        "database_factory": clients.connect,
        "database_enter": clients.database_context.__enter__,
        "database_query": clients.connection.execute,
        "database_fetch": clients.connection.execute.return_value.fetchone,
        "redis_factory": clients.redis_factory,
        "redis_enter": clients.redis_context.__enter__,
        "redis_ping": clients.redis.ping,
        "storage_factory": clients.storage_factory,
        "storage_head": clients.storage.head_bucket,
    }
    operations[failure].side_effect = RuntimeError("Dependency unavailable")
    expected = {"postgis": True, "redis": True, "object_storage": True}
    expected[dependency] = False
    assert main.check_dependencies(settings) == expected
    clients.connect.assert_called_once()
    clients.redis_factory.assert_called_once()
    clients.storage_factory.assert_called_once()
    if failure != "storage_factory":
        clients.storage.close.assert_called_once_with()
    if failure in {"database_query", "database_fetch"}:
        clients.database_context.__exit__.assert_called_once()
    if failure == "redis_ping":
        clients.redis_context.__exit__.assert_called_once()


def test_storage_close_failure_preserves_completed_probe(settings, clients):
    # Characterization, not a new policy: head_bucket already succeeded.
    clients.storage.close.side_effect = RuntimeError("Close failed")
    assert main.check_dependencies(settings) == {
        "postgis": True, "redis": True, "object_storage": True
    }
    clients.storage.close.assert_called_once_with()


def test_real_probe_http_failure_does_not_disclose_secrets(settings, clients, caplog):
    secret_values = (
        settings.postgres_password.get_secret_value(),
        settings.s3_access_key.get_secret_value(),
        settings.s3_secret_key.get_secret_value(),
    )
    message = "dependency-secret-marker " + " ".join(secret_values)
    clients.connect.side_effect = RuntimeError(message)
    clients.redis_factory.side_effect = RuntimeError(message)
    clients.storage.head_bucket.side_effect = RuntimeError(message)
    with caplog.at_level("INFO", logger="uvicorn.error"):
        with TestClient(main.create_app(settings)) as client:
            response = client.get("/health/ready")
            live = client.get("/health/live")
    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"postgis": False, "redis": False, "object_storage": False},
    }
    assert live.status_code == 200
    assert "dependency-secret-marker" not in response.text + caplog.text
    for value in secret_values:
        assert value not in response.text + caplog.text
    clients.storage.close.assert_called_once_with()
