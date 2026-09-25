# Foundation audit

Audit date: 2026-09-25 UTC. Target: `Vigneshsakthivel07/GeoNet`, branch `feat/platform-foundation`.

## Executive finding

This repository is a backend/infrastructure foundation, not a completed Land Intelligence Platform. The national-scale master prompt is an acceptance roadmap, not a description of delivered functionality. No production deployment or legal authority is claimed.

This increment is limited to the three expressly approved paths. Existing application interfaces, GIS source, deployment configuration and database behavior are unchanged. No migration is required for the added tests. The requested future repository name `land-intelligence-platform` has not been created or substituted for the explicitly approved GeoNet target.

## Evidence inspected

| Source | Finding |
| --- | --- |
| `backend/app/main.py` | FastAPI factory; liveness; sequential PostGIS, Redis and S3 readiness; bounded metric labels; JSON request log messages; basic security headers |
| `backend/app/config.py` | Development/test settings only; required secret fields; host and CORS settings |
| `backend/tests/test_health.py` | Existing assertions for routes, readiness injection, headers, hosts, CORS and metrics |
| `backend/pyproject.toml` | Python 3.12; pytest, Ruff and strict application mypy configuration; dependency ranges, no lockfile |
| `backend/Dockerfile` | Non-root API image and liveness health check |
| `compose.yaml` | PostGIS, Redis, MinIO, private bucket initializer and API; host-published ports bind to loopback |
| Repository root and backend directory | No frontend, parcel domain, migrations or integrated GIS modules present |
| `docs/implementation-status.md` | Earlier foundation status and outstanding implementation gates; retained unchanged |
| `sih26010-gis/src/validation/api.py` | Public `validate_land_parcel()` wrapper and existing result shape |
| `sih26010-gis/src/validation/validator.py` | CSV loading, affine registration, geometry construction and comparison pipeline |
| `sih26010-gis/src/validation/engine.py` | Threshold-based VERIFIED/MISMATCH calculation |
| `sih26010-gis/src/validation/overlap.py` | Overlap is intersection divided by union, expressed as a percentage |
| `sih26010-gis/src/transform/projection.py` | WGS84 to fixed EPSG:32643 with explicit longitude/latitude axis ordering |
| `sih26010-gis/tests/test_mismatch.py` | Top-level demonstration with printed output, not regression assertions |
| `sih26010-gis/test_demo_validation.py` | Demonstration using mismatch data and printed results |

Original GIS source: https://github.com/Vigneshsakthivel07/sih26010-gis

## This increment and verification limits

| Approved file | State |
| --- | --- |
| `backend/tests/test_dependency_probes.py` | Committed: mock-backed characterization of actual dependency-probe control flow and HTTP failure disclosure |
| `.github/workflows/ci.yml` | Two write attempts failed without a diagnostic cause; first failure followed by root verification showing no workflow directory and Actions returning no runs. Installation is not confirmed. |
| `docs/foundation-audit.md` | This audit records inspected evidence, limitations and next acceptance gates |

No shell, Python execution environment or Docker runtime is available in this implementation session. Tests, Ruff, mypy, container builds and integration checks have NOT been executed. A written assertion is not a passing result. No CI badge or claim of verification should be added until a workflow actually runs successfully.

The attempted workflow would run Ruff, mypy, pytest and a separate Compose build/smoke job with generated ephemeral credentials, real readiness checks, private-bucket denial, Redis failure isolation and recovery. It was not successfully installed. Do not infer a permissions failure or GitHub outage from the generic write error. Resolve workflow creation through a workflow-capable GitHub connection or an authorized repository editor, then run it on this branch.

### Added characterization coverage

| Behavior | Assertion |
| --- | --- |
| Successful probes | All three dependency results are true |
| PostgreSQL configuration | Exact connection parameters, timeouts and PostGIS query |
| Redis configuration | Socket/connect timeouts and PING |
| S3 configuration | Endpoint, region, path addressing, timeout and disabled retries |
| Resource lifecycle | Database/Redis contexts exit; S3 client closes after success and bucket failure |
| Missing PostGIS version | Readiness dependency remains false for absent or empty result |
| Negative Redis PING | Dependency remains false |
| Connection, context and operation failures | Other dependency probes still run |
| S3 close failure after successful HEAD | Existing successful bucket result is preserved; this is characterization, not a new policy |
| HTTP response and logs | All-dependency failure returns 503 with booleans, without exception text or secret values; liveness remains 200 |

Mocks prevent these unit tests from contacting external services. They do not establish real database, Redis or object-storage connectivity. They also do not prove a hard end-to-end deadline: DNS resolution, sequential probes and driver behavior require separate operational testing.

Run from the repository root in a Python 3.12 environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e './backend[dev]'
cd backend
python -m ruff check app tests
python -m mypy app
python -m pytest
cd ..
```

For local integration, configure fresh private credentials in `.env` using `.env.example`; never commit the populated file. Run `docker compose config --quiet`, then `docker compose up -d --build`. Confirm `/health/live`, `/health/ready`, `/metrics` and `/docs` on `http://127.0.0.1:8000`. Use `docker compose down` to stop services while retaining data. Do not use `down --volumes` against data you need to preserve.

## Security and deployment gates

| Risk or gap | Required treatment |
| --- | --- |
| No authentication or organization authorization | Implement verified OIDC identities, backend RBAC and tenant isolation before business endpoints |
| Development database bootstrap user | Introduce least-privilege application and migration roles |
| Development MinIO root credentials used by API | Introduce scoped service credentials and restrictive bucket policies |
| Unauthenticated metrics and API documentation | Restrict production exposure through application and ingress policy |
| No upload API | Require size, MIME/signature and archive-expansion limits, quarantine and isolated processors |
| No business audit persistence | Append audit events transactionally with state changes; preserve actor and provenance |
| Mutable dependency/image resolution | Add dependency locks, reviewed image digests and vulnerability checks |
| No rate limiting or production identity/configuration | Add explicit deployment policy; keep production disabled until verified |
| No backup/restore or deployment evidence | Rehearse recovery before production approval |

## GIS preservation and integration gates

Do not replace the original algorithms blindly. Pin the source commit and preserve attribution; confirm redistribution licensing before importing code. No license was visible in the inspected source root. No GIS code has been copied or modified in this increment.

| Concern | Required integration behavior |
| --- | --- |
| Compatibility | Characterize public signatures, output fields, matching and mismatch cases before refactoring |
| Analysis CRS | Preserve fixed Zone 43N only in a legacy adapter; require an appropriate projected CRS with units and area-of-use checks for new workflows |
| Geospatial truth | Persist authoritative versioned geometries in PostGIS; do not use browser or JSON-only geometry as the source of truth |
| Overlap semantics | Label the existing metric IoU; expose historical-area coverage as a separate metric if needed |
| Affine registration | Record controls, transformation parameters and residuals; separate registration controls from independent validation observations |
| Geometry validity | Test ordering, self-intersection, empty/degenerate polygons and coordinate finiteness before authoritative persistence |
| Validation rules | Version configurable tolerances; legacy defaults are not official Indian survey standards |
| Status interpretation | Automated VERIFIED is not human approval, legal ownership or an authoritative boundary determination |
| History | Preserve source, geometry, rules and processing versions; never overwrite historical evidence |

## Remaining delivery sequence

| Phase | Current state | Acceptance gate |
| --- | --- | --- |
| Foundation | Partial source; unverified | Installed CI with passing lint, types, tests, build and real dependency checks |
| Land database | Absent | Data-driven India-wide administrative hierarchy; versioned parcels, surveys, documents and audit; PostGIS indexes and tested migrations |
| Identity | Absent | Verified OIDC tokens, RBAC and cross-organization denial tests |
| Parcel vertical slice | Absent | Authorized create/search/detail, history and transactional audit through real APIs |
| Web GIS | Absent | Next.js App Router, accessible MapLibre interface, viewport-limited queries, real loading/error states and end-to-end tests |
| GIS integration | Original inspected only | Pinned, attributed legacy adapter with assertion-based regression tests and CRS-safe new interface |
| Survey import | Absent | Validated CSV/GeoJSON, explicit CRS, instrument/accuracy metadata and persisted observations |
| Evidence storage | Bucket configuration only | Authorized upload/download, content validation, provenance and private object lifecycle |
| Background processing | Absent | Celery workers with idempotency, persistent job state and retry/failure tests |
| FMB intelligence | Absent | OpenCV/PaddleOCR processing with intermediate artifacts, confidence and human verification |
| Digital twin and validation | Absent | Historical/current comparisons, versioned rules, deviation/area/IoU metrics and audited review |
| Reports | Absent | Reproducible evidence reports tied to input, rule and geometry versions |
| AI foundations | Absent | Model/version registry and evidence-linked outputs; optional heavy dependencies; no invented results |
| Production deployment | Absent | Tested images, least-privilege infrastructure, secrets management, observability and restore verification |
| Future scale | Deferred | Measured need before vector tiles, regional partitioning, OpenSearch, Kafka or Kubernetes expansion |

The next implementation slice should be the land schema plus identity/authorization foundations after the verification gate passes. The first product acceptance milestone is one authenticated, audited parcel workflow backed by PostGIS and rendered in a working web map—not static feature screens.
