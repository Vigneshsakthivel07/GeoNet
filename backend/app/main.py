"""Operational endpoints only; parcel APIs and authentication are not implemented yet."""

import asyncio
import json
import logging
import os
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import boto3
import psycopg
import redis
from botocore.config import Config
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

logger = logging.getLogger("geonet")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
logger.propagate = False

REQUESTS = Counter("geonet_http_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("geonet_http_request_seconds", "HTTP latency", ["method", "route"])


def required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Missing configuration: {name}")
    return value


def check_database() -> None:
    with psycopg.connect(
        host=required_env("POSTGRES_HOST"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=required_env("POSTGRES_DB"),
        user=required_env("POSTGRES_USER"),
        password=required_env("POSTGRES_PASSWORD"),
        connect_timeout=3,
        options="-c statement_timeout=3000",
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT PostGIS_Version()")
            if cursor.fetchone() is None:
                raise RuntimeError("PostGIS is unavailable")


def check_redis() -> None:
    client = redis.Redis(
        host=required_env("REDIS_HOST"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        password=required_env("REDIS_PASSWORD"),
        socket_connect_timeout=2,
        socket_timeout=2,
        retry_on_timeout=False,
    )
    try:
        if not client.ping():
            raise RuntimeError("Redis is unavailable")
    finally:
        client.close()


def check_storage() -> None:
    client = boto3.client(
        "s3",
        endpoint_url=required_env("S3_ENDPOINT_URL"),
        aws_access_key_id=required_env("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=required_env("S3_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        config=Config(
            connect_timeout=2,
            read_timeout=2,
            retries={"max_attempts": 0},
            s3={"addressing_style": "path"},
        ),
    )
    try:
        client.head_bucket(Bucket=required_env("S3_BUCKET"))
    finally:
        client.close()


def create_app(checkers: dict[str, Callable[[], None]] | None = None) -> FastAPI:
    checks = checkers if checkers is not None else {
        "database": check_database,
        "redis": check_redis,
        "object_storage": check_storage,
    }
    application = FastAPI(title="GeoNet API", version="0.1.0")
    origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "").split(",") if item.strip()]
    if "*" in origins:
        raise ValueError("CORS_ORIGINS must contain explicit origins, not a wildcard")
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["GET"],
            allow_headers=["Content-Type", "Authorization"],
        )

    @application.middleware("http")
    async def observe(request: Request, call_next):
        request_id = str(uuid.uuid4())
        started = time.perf_counter()
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
            elapsed = time.perf_counter() - started
            route = getattr(request.scope.get("route"), "path", "unmatched")
            method = request.method if request.method in {
                "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"
            } else "OTHER"
            REQUESTS.labels(method, route, str(status)).inc()
            LATENCY.labels(method, route).observe(elapsed)
            logger.info(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "http_request",
                "request_id": request_id,
                "method": method,
                "route": route,
                "status": status,
                "duration_ms": round(elapsed * 1000, 3),
            }))

    @application.get("/health/live", tags=["Operations"])
    def live() -> dict[str, str]:
        return {"status": "alive"}

    @application.get("/health/ready", tags=["Operations"], responses={503: {"description": "Not ready"}})
    async def ready() -> JSONResponse:
        async def run_check(name: str, check: Callable[[], None]) -> tuple[str, str]:
            try:
                await asyncio.to_thread(check)
            except Exception:
                # Never expose dependency exceptions: they can contain credentials or hosts.
                return name, "unavailable"
            return name, "ok"

        results = dict(await asyncio.gather(*(run_check(name, check) for name, check in checks.items())))
        healthy = bool(results) and all(value == "ok" for value in results.values())
        return JSONResponse(
            {"status": "ready" if healthy else "not_ready", "checks": results},
            status_code=200 if healthy else 503,
        )

    @application.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})

    return application


app = create_app()
