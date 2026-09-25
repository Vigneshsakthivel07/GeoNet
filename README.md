# GeoNet — Land Intelligence Platform

India Land Digital Twin & Spatial Intelligence Platform.

> **Status: initial backend and infrastructure foundation, not a completed MVP.** Code has been committed but not executed in the authoring environment. See [implementation status](docs/implementation-status.md) for exact boundaries. There is no frontend or parcel API yet.

## Problem and product

Historical cadastral documents and modern surveys often live in disconnected systems. GeoNet aims to connect versioned parcel geometry, survey observations and supporting records with traceable spatial analysis and human review.

Spatial checks and AI extraction are decision support, not determinations of ownership, title or legal validity. No government integration or official tolerance is currently implemented.

## Architecture

The intended system is a web-first Next.js application calling modular FastAPI services, with PostgreSQL/PostGIS as the spatial source of truth, MinIO/S3 for evidence and Redis/Celery for asynchronous processing. Administrative units will be data-driven across India, not specific to one state. Parcel geometry and evidence history must be append-only/versioned rather than silently overwritten.

| Component | Current state |
| --- | --- |
| FastAPI | Application factory, OpenAPI and health endpoints |
| PostgreSQL/PostGIS | Compose service and real readiness query; no parcel schema yet |
| Redis | Compose service and real readiness probe |
| MinIO | Compose service, private bucket initialization and readiness probe |
| Observability | JSON request log messages and Prometheus request metrics |
| Tests | Unit-test source committed, not run |
| Docker | API container and local Compose source committed, not run |
| GitHub Actions | Workflow write failed; no CI run exists |
| Next.js / MapLibre | Not implemented |
| Identity / RBAC | Not implemented; no business endpoints exposed |
| Celery / OCR / AI | Not implemented |

## Local setup

Requires Git, Docker Engine and Docker Compose v2. Python 3.12 is required for host-side backend tests. No AWS account is required.

```bash
git clone --branch feat/platform-foundation https://github.com/Vigneshsakthivel07/GeoNet.git
cd GeoNet
cp .env.example .env
```

Generate three independent local values, then put them in the corresponding empty fields in `.env`. Never share or commit the resulting file.

```bash
python3 -c "import secrets; print(secrets.token_hex(24))"
python3 -c "import secrets; print(secrets.token_hex(12))"
python3 -c "import secrets; print(secrets.token_hex(24))"
```

The first value is `POSTGRES_PASSWORD`, the second `MINIO_ROOT_USER`, and the third `MINIO_ROOT_PASSWORD`. Use at least 16 characters for passwords. On POSIX systems restrict the file with `chmod 600 .env`.

```bash
docker compose config --quiet
docker compose up --build --detach
curl --fail http://127.0.0.1:8000/health/live
curl --fail http://127.0.0.1:8000/health/ready
```

`/health/ready` returns HTTP 503 until PostGIS, Redis and the evidence bucket respond successfully. It never substitutes sample healthy results for dependency failures. Initial image download may take time. Container tags and dependency ranges have not been verified by a build in this environment; lock and scan dependencies before any release.

| Local endpoint | Purpose |
| --- | --- |
| http://127.0.0.1:8000/docs | Interactive API documentation |
| http://127.0.0.1:8000/openapi.json | OpenAPI schema |
| http://127.0.0.1:8000/health/live | Process liveness |
| http://127.0.0.1:8000/health/ready | Infrastructure readiness |
| http://127.0.0.1:8000/metrics | Prometheus request metrics |
| http://127.0.0.1:9001 | Local MinIO console |

PostgreSQL, Redis and the MinIO API are reachable only within the Compose network. Named volumes preserve local data. `docker compose down` stops the stack without deleting those volumes. Do not use `down --volumes` on data you need to retain.

## Database

The PostGIS image initializes its extension on a fresh data volume. Readiness executes `SELECT PostGIS_Version()` against the configured database. This is not a migration framework: administrative hierarchy, organization scope, parcels, immutable parcel versions, surveys, validation rules, provenance and audit tables are not yet implemented. Add migration tests before business features.

Changing the password in `.env` does not change the database password in an existing data volume. Rotate the actual database credential separately; do not delete persisted data as a routine repair.

## Testing

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install '.[dev]'
ruff check .
mypy app
pytest -q
```

Unit tests inject dependency probes; they do not validate real infrastructure. They generate ephemeral test credentials and check readiness failures, liveness independence, allowed hosts, CORS and bounded metric labels.

With the Compose stack running, test a real dependency failure:

```bash
docker compose stop redis
curl --include http://127.0.0.1:8000/health/ready
docker compose start redis
```

Expect HTTP 503 while Redis is stopped, then HTTP 200 once all dependencies recover. No test has been reported as passing yet. The intended CI workflow write was unsuccessful, so execute these checks locally before merging. No workflow or cloud deployment should be assumed to exist.

## GIS integration

Reuse source: [sih26010-gis](https://github.com/Vigneshsakthivel07/sih26010-gis).

Its public `validate_land_parcel()` API and underlying affine fitting, point inclusion, overlap and validation code were inspected. They are not yet integrated. The next GIS increment must pin the source revision, preserve attribution, confirm reuse rights and establish assertion-based characterization tests before refactoring.

The original GPS projection is fixed to EPSG:32643 and cannot be used indiscriminately across India. New workflows must validate source and analysis CRS and use a suitable projected metric CRS. Original overlap is intersection-over-union, not historical-area coverage. Registration fitting can absorb geometric change; preserve fitting parameters and control-point residuals as evidence. Automated VERIFIED must remain distinct from human verification and legal conclusions.

## FMB and AI architecture — planned, not implemented

The intended pipeline stores the original PDF/image in object storage, then records preprocessing, OpenCV detection, PaddleOCR output, geometry candidates, control-point georeferencing and review artifacts. Every extracted value needs source coordinates/page, method/model version, confidence when genuinely provided, and an audited human review status. No OCR or AI output should become authoritative parcel geometry automatically.

Celery processing, model dependencies, pgvector retrieval and future imagery comparison remain outstanding. Heavy ML libraries are intentionally not installed in the health-only API image.

## Security and deployment

This Compose environment is **local development only**. It uses bootstrap database and MinIO identities, not production least-privilege service accounts. Do not bind these services publicly or load sensitive land/person data. Production mode is intentionally not supported by the settings model yet.

Before production: verified Keycloak/OIDC tokens, backend tenant/RBAC checks, constrained service accounts, secure evidence upload/quarantine, immutable audits, migration ownership, dependency locks, image scanning, TLS, secret management, rate limits, backups and restore tests are required. Authentication cannot be delegated solely to a future frontend.

AWS/EKS, RDS, S3, ElastiCache and Terraform remain a deployment roadmap, not deployed or generated infrastructure. No AWS credentials were requested or used.

## Roadmap and contribution

See [implementation status](docs/implementation-status.md) for staged acceptance gates. The immediate gate is a passing foundation build/test run. The next vertical slice should introduce migrations, identity, parcel CRUD/history and a real Next.js/MapLibre workflow before OCR and AI expansion.

Use focused branches and reviewable changes. Inspect existing behavior first, add characterization tests before refactoring and attach actual lint/type-check/test results. Never commit `.env`, credentials, private records, build output or generated survey artifacts. Keep government providers disabled until a real authorized integration exists.

## Screenshots

None yet: the web interface is not implemented. No mock screenshot is presented as a working application.

## License

No license has been selected by the repository owner. This project is not represented as permissively licensed. Confirm licensing of reused GIS code before redistribution; do not add a license on behalf of the owner without approval.
