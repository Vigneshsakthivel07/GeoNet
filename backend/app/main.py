import json
import logging
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import boto3
import psycopg
from botocore.config import Config
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, generate_latest
from redis import Redis

from app.config import Settings

logger = logging.getLogger("uvicorn.error")
Probe = Callable[[Settings], dict[str, bool]]


def check_dependencies(settings: Settings) -> dict[str, bool]:
    """Bounded probes; never disclose connection strings or exception messages."""
    checks = {"postgis": False, "redis": False, "object_storage": False}
    try:
        with psycopg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password.get_secret_value(),
            connect_timeout=2,
            options="-c statement_timeout=2000",
        ) as connection:
            row = connection.execute("SELECT PostGIS_Version()").fetchone()
            checks["postgis"] = bool(row and row[0])
    except Exception:
        pass
    try:
        with Redis.from_url(
            settings.redis_url, socket_connect_timeout=2, socket_timeout=2
        ) as client:
            checks["redis"] = bool(client.ping())
    except Exception:
        pass
    try:
        storage = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            region_name="us-east-1",
            config=Config(
                connect_timeout=2,
                read_timeout=2,
                retries={"max_attempts": 0},
                s3={"addressing_style": "path"},
            ),
        )
        try:
            storage.head_bucket(Bucket=settings.s3_bucket)
            checks["object_storage"] = True
        finally:
            storage.close()
    except Exception:
        pass
    return checks


def create_app(settings: Settings | None = None, probe: Probe | None = None) -> FastAPI:
    settings = settings or Settings()
    dependency_probe = probe or check_dependencies
    application = FastAPI(
        title="Land Intelligence Platform",
        version="0.1.0",
        description="Development foundation only. Spatial evidence is not a legal determination.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    registry = CollectorRegistry()
    requests = Counter(
        "geonet_http_requests_total",
        "HTTP requests by registered route and status",
        ["route", "status"],
        registry=registry,
    )

    @application.middleware("http")
    async def observe_request(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        started = time.monotonic()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Cache-Control"] = "no-store"
            return response
        finally:
            route = getattr(request.scope.get("route"), "path", "unmatched")
            requests.labels(route=route, status=str(status)).inc()
            logger.info(json.dumps({
                "event": "http_request",
                "request_id": request_id,
                "route": route,
                "status": status,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
            }))

    @application.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/ready", tags=["health"])
    def ready() -> JSONResponse:
        checks = dependency_probe(settings)
        healthy = all(checks.get(name, False) for name in (
            "postgis", "redis", "object_storage"
        ))
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={"status": "ready" if healthy else "not_ready", "checks": checks},
        )

    @application.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})

    return application
