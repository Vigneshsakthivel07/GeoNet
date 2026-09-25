# GeoNet

India Land Intelligence Platform — building toward a parcel-centred digital twin with spatial
validation, historical evidence, and audited human review.

**Status: backend foundation only. Not a complete product, not production-ready, not deployed.**
There is no Next.js application, authentication, parcel database schema, OCR processor, or upload API
in this batch. Health endpoints are operational infrastructure, not a substitute for those features.

## Problem and solution

Historical cadastral documents and modern surveys need a shared spatial reference, traceable
provenance, and comparison tools. GeoNet will integrate those sources around versioned parcels in
PostGIS. Automated results will support authorized reviewers, not make ownership or legal decisions.
Administrative geography will be data-driven across India rather than specific to one state.

## Implemented foundation

| Component | Implementation |
|---|---|
| FastAPI | Liveness, dependency readiness, OpenAPI, JSON request logs, request IDs |
| Metrics | Prometheus request counts and duration histograms |
| PostgreSQL/PostGIS | Local spatial database service; readiness checks execute `PostGIS_Version()` |
| Redis | Password-protected local service and authenticated readiness probe |
| MinIO | Local object storage, private evidence bucket initialization and bucket readiness probe |
| Legacy GIS | Original decision engine copied without changes; integrity and behavior tests |
| Local runtime | Docker Compose with persistent volumes, health checks and non-root API container |
| CI definition | Lint, type-check, unit tests, Compose configuration validation and stack smoke tests |

CI configuration being present is not proof it has passed. Inspect the workflow results for the
exact commit: https://github.com/Vigneshsakthivel07/GeoNet/actions

## Architecture and stack

The current backend checks PostgreSQL/PostGIS, Redis, and the configured MinIO bucket. PostgreSQL
will be the spatial source of truth; large evidence files belong in object storage. No parcel
geometries or user data are seeded by this batch.

| Layer | Planned platform technology |
|---|---|
| Web | Next.js App Router, React, TypeScript, Tailwind, shadcn/ui |
| Map | MapLibre GL JS; Cesium integration later |
| API | FastAPI with REST/OpenAPI |
| Spatial persistence | PostgreSQL/PostGIS with versioned geometries and spatial indexes |
| Jobs | Celery with Redis |
| Documents | S3-compatible object storage |
| GIS processing | GDAL, GEOS, PROJ, Shapely, GeoPandas, Rasterio |
| FMB intelligence | OpenCV and PaddleOCR with retained processing evidence |
| AI foundations | PyTorch, Transformers, ONNX Runtime; pgvector when retrieval is implemented |
| Authentication | Keycloak-compatible OAuth2/OIDC and backend RBAC |
| Production | AWS/Kubernetes/Terraform after deployment and security readiness |

Kafka, OpenSearch and nationwide partitioning are deferred until justified. No mobile application
is included in the requested phase.

## Local setup

Requires Git and Docker with Docker Compose v2. No AWS credentials are needed.

```bash
git clone --branch feature/geonet-foundation https://github.com/Vigneshsakthivel07/GeoNet.git
cd GeoNet
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(24))"
```

Generate independent passwords and fill every blank value in `.env`. Choose a local MinIO username
of at least three characters and a password of at least eight characters. Never commit `.env`.

```bash
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 240
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
```

| Local endpoint | Purpose |
|---|---|
| http://localhost:8000/docs | Interactive API documentation |
| http://localhost:8000/openapi.json | API schema |
| http://localhost:8000/health/live | Process liveness; independent of dependencies |
| http://localhost:8000/health/ready | PostGIS, Redis, and private-bucket readiness; returns 503 on failure |
| http://localhost:8000/metrics | Prometheus metrics; keep internal in production |
| http://localhost:9001 | Local MinIO administrative console |

Only the API and MinIO console are published, bound to loopback. Database, Redis and S3 API ports
are internal to Compose. API health is liveness; check `/health/ready` separately before use.

```bash
docker compose logs --tail=100 api
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT PostGIS_Version();"'
docker compose down
```

`docker compose down` preserves volumes. Adding `--volumes` destroys local database and evidence
storage; do not use that option unless intentionally discarding all local data. Changing credentials
in `.env` does not rotate credentials in an existing database volume.

## Database and migrations

The PostGIS image initializes the database and extension for a fresh volume. There are no domain
tables or migrations yet. The next data milestone requires Alembic migrations for administrative
units, parcels, geometry versions, surveys, evidence provenance, validation rules and audit events.
Do not interpret an empty healthy database as a completed land information system.

## Tests

Use Python 3.12 for host-based development. Unit tests use injected dependency checkers and do not
require Docker or cloud credentials. CI additionally exercises real services via Compose.

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
mypy
pytest --cov=app --cov-report=term-missing
```

Legacy code is excluded from lint transformation to preserve the upstream file exactly. A Git-blob
integrity test prevents accidental changes. Full GIS, browser, authentication and OCR tests cannot
be claimed until those components exist. Dependencies use bounded version ranges; release work
must add reproducible lockfiles, image digests and vulnerability review.

## GIS integration

See [source provenance and compatibility plan](docs/gis-integration.md). The upstream
`validate_parcel_from_files()` pipeline must retain its public behavior during integration. The
copied decision engine is internal and is not exposed as an unvalidated HTTP endpoint.
The original fixed UTM 43N conversion must not become the default for all India. CRS-aware adapters
and characterization tests precede any projection changes.

## FMB and AI architecture — planned, not implemented

FMB processing will retain the source PDF/image, preprocessing output, OCR text/confidence, detected
lines, control points, reconstructed geometries, model versions and reviewer decisions. A queued
worker will process expensive steps. Georeferencing and geometry validation must precede accepting
results into PostGIS. AI-extracted fields require provenance and human review. No OCR accuracy,
automatic boundary validity, or government data integration is claimed.

## Security and deployment status

This Compose configuration is **local development only**. It uses a database bootstrap identity and
MinIO root credentials internally; production must replace them with least-privilege roles, scoped
storage policies and a secrets manager. There is no application authentication or rate limiter yet.
Do not expose it publicly or upload sensitive land records.

Production release requires authentication/RBAC, organization isolation, secure upload scanning and
quotas, TLS, ingress limits, audit persistence, backups and restore testing, migration procedures,
security scanning, pinned builds and a reviewed infrastructure plan. AWS, Kubernetes, Terraform and
a deployment workflow are not delivered in this batch. No public application URL exists.

## Roadmap

| Milestone | Remaining deliverable |
|---|---|
| Foundation verification | Passing lint, type checks, regression tests and Compose smoke tests |
| Land database | Administrative hierarchy, versioned parcel models, migrations and spatial indexes |
| Secure web workflow | Authentication, backend authorization, Next.js and MapLibre connected to real parcel APIs |
| GIS integration | Full preserved pipeline, input validation, CRS adapters and versioned rules |
| Evidence processing | Secure uploads, survey imports, Celery, OCR/CV artifacts and review |
| Digital twin | History, evidence, validation comparisons, reports and complete audit trails |
| Release | End-to-end tests, security review, deployment automation and verified live environment |

## Screenshots

No screenshots are included because the web UI has not been implemented. Screenshots will show
real running workflows, not fabricated product screens.

## Contribution guidelines

Inspect existing behavior before changing code. Make focused feature-branch changes, add tests,
run CI, and document API or migration impacts. Do not commit credentials or sensitive datasets.
Keep automated spatial results distinct from legal authority and human verification.

## License

A distribution license has not been selected. Do not assume unrestricted redistribution rights.
The original GIS source and its owner are attributed in the integration document.
