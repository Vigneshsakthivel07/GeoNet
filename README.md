# GeoNet

India Land Intelligence Platform — building toward a parcel-centred digital twin with spatial
validation, historical evidence, and audited human review.

**Status: backend foundation committed, verification blocked. Not a complete product, not
production-ready, not deployed.** There is no web UI, authentication, parcel schema, OCR processor
or upload API in this batch.

## Verification blocker

The connector successfully committed the application files but failed twice when publishing
`.github/workflows/ci.yml`. A subsequent branch comparison confirmed that no workflow file was
committed. The returned error did not identify the cause; a workflow-permission problem is possible
but not confirmed. GitHub Actions returned zero runs for this branch. No lint, type-check, unit-test
or Compose success is claimed. Run the commands below locally or restore workflow publishing before
merging. CI is planned, not installed.

## Problem and solution

Historical cadastral documents and modern surveys need a shared spatial reference, traceable
provenance and comparison tools. GeoNet will integrate these sources around versioned parcels in
PostGIS. Automated results support authorized reviewers, not ownership or legal decisions.
Administrative geography will be data-driven across India rather than specific to one state.

## Committed foundation

| Component | Implementation, pending execution checks |
|---|---|
| FastAPI | Liveness, dependency readiness, OpenAPI, JSON request logs and request IDs |
| Metrics | Prometheus request counts and duration histograms |
| PostGIS | Local database service; readiness executes `PostGIS_Version()` |
| Redis | Password-protected local service and authenticated readiness probe |
| MinIO | Local storage, private evidence-bucket initialization and bucket readiness probe |
| Legacy GIS | Decision engine copied byte-for-byte; integrity and behavior tests |
| Docker | Compose, persistent volumes, service health checks and non-root API container |
| Tests | Assertions for engine outcomes, dependency failure, CORS, logging and metrics |

## Architecture and stack

The backend probes PostGIS, Redis and MinIO. PostgreSQL will be the spatial source of truth;
large evidence files belong in object storage. No parcel geometries or user data are seeded.

| Layer | Planned technology |
|---|---|
| Web | Next.js App Router, React, TypeScript, Tailwind, shadcn/ui |
| Map | MapLibre GL JS; Cesium later |
| API | FastAPI, REST/OpenAPI, backend authorization |
| Spatial data | PostgreSQL/PostGIS, versioned geometry and spatial indexes |
| Jobs | Celery with Redis |
| Evidence | S3-compatible object storage |
| GIS | GDAL, GEOS, PROJ, Shapely, GeoPandas, Rasterio |
| FMB | OpenCV and PaddleOCR with retained intermediate artifacts |
| AI | PyTorch, Transformers, ONNX Runtime; pgvector when retrieval is implemented |
| Identity | Keycloak-compatible OAuth2/OIDC and RBAC |
| Production | AWS, Kubernetes and Terraform after release readiness |

Kafka, OpenSearch and nationwide partitioning are deferred until justified. No mobile app is planned
for this phase.

## Local setup

Requires Git and Docker Compose v2. No AWS credentials are needed. These instructions are provided
for verification; this environment has not executed them.

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
| http://localhost:8000/docs | API documentation |
| http://localhost:8000/openapi.json | API schema |
| http://localhost:8000/health/live | Process liveness |
| http://localhost:8000/health/ready | PostGIS, Redis and evidence-bucket readiness; 503 on failure |
| http://localhost:8000/metrics | Internal Prometheus metrics |
| http://localhost:9001 | MinIO administrative console |

Published ports bind to loopback. Database, Redis and S3 API ports remain internal to Compose.
Container health checks process liveness; check readiness separately.

```bash
docker compose logs --tail=100 api
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT PostGIS_Version();"'
docker compose down
```

`docker compose down` preserves volumes. Adding `--volumes` destroys local database and evidence
storage. Changing `.env` does not rotate credentials in an existing database volume.

## Database and migrations

The PostGIS image initializes the extension for a fresh volume. Domain tables and Alembic migrations
are not implemented. The next data milestone requires administrative units, parcels, geometry
versions, surveys, documents, provenance, validation rules and audit events. A healthy empty database
is not a completed land information system.

## Test commands

Use Python 3.12. Unit tests inject dependency checkers and do not need cloud credentials or Docker.
Run and retain all outputs; fix failures before merging.

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
mypy
pytest --cov=app --cov-report=term-missing
```

The planned CI additionally builds the Compose stack, verifies readiness against actual services,
stops Redis, and asserts readiness becomes 503 while liveness remains 200. It is not yet committed.
Workflow history: https://github.com/Vigneshsakthivel07/GeoNet/actions

Legacy source is excluded from lint transformation to retain exact source bytes; an integrity test
checks its Git blob. Full GIS, browser, authentication and OCR tests cannot be claimed before those
components exist. Release work must add dependency lockfiles, image digests and vulnerability review.

## GIS integration

See [provenance and compatibility plan](docs/gis-integration.md). Only the final decision engine is
copied. The complete `validate_parcel_from_files()` pipeline is not yet integrated. Its interface and
behavior must be preserved during integration. The original fixed UTM 43N conversion is not an
India-wide default; explicit CRS adapters and characterization tests precede projection changes.
The copied engine is not exposed as an unvalidated HTTP endpoint.

## FMB and AI architecture — planned

Retain source documents, preprocessing output, OCR text/confidence, detected lines, control points,
reconstructed geometries, model versions and review decisions. Expensive processing belongs in a
queued worker. Georeferencing and geometry validation precede accepting results into PostGIS.
AI-extracted fields require provenance and human review. No accuracy or government integration claim
is made.

## Security and deployment

**Local development only.** Compose uses database bootstrap and MinIO administrative identities.
Production needs least-privilege roles, scoped storage policies, a secrets manager, TLS and ingress
controls. Application authentication and rate limiting are not implemented. Do not expose this
foundation publicly or upload sensitive records.

Production also requires organization isolation, secure upload scanning and quotas, audit persistence,
backups and restore tests, migrations, security scans and reviewed infrastructure. AWS, Kubernetes,
Terraform and deployment workflows are not delivered. No live application URL exists.

## Roadmap

| Milestone | Remaining work |
|---|---|
| Foundation verification | Publish CI and pass lint, type checks, tests and Compose smoke checks |
| Land database | Administrative hierarchy, versioned parcels, migrations and indexes |
| Secure web workflow | Authentication, authorization, Next.js and MapLibre with real parcel APIs |
| GIS integration | Preserved pipeline, validated input, CRS adapters and configurable versioned rules |
| Evidence processing | Secure uploads, survey import, Celery, OCR/CV artifacts and review |
| Digital twin | History, evidence, comparisons, reports and audit trails |
| Release | End-to-end tests, security review, deployment automation and verified live environment |

## Screenshots

No screenshots: the web UI is not implemented. Future screenshots must show real workflows.

## Contributing

Inspect existing behavior before changing code. Use focused feature branches, assertions and passing
checks. Document API and migration impacts. Never commit credentials or sensitive datasets. Keep
automated spatial status distinct from human review and legal authority.

## License

No distribution license has been selected. Do not assume unrestricted redistribution rights.
The owner-authorized original GIS source is attributed in the integration document.
