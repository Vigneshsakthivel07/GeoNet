# GIS integration and provenance

## Preserved component

| Property | Value |
|---|---|
| Upstream repository | https://github.com/Vigneshsakthivel07/sih26010-gis |
| Upstream file | `src/validation/engine.py` |
| Upstream Git blob | `94da2f30964b6123a8bb26bdfa5e67a3e4427503` |
| GeoNet destination | `backend/app/legacy/engine.py` |
| Modification | None: byte-for-byte copy authorized by the repository owner |
| Integrity protection | `test_upstream_source_is_unchanged` verifies the Git blob hash |

The original repository is not modified. No external GIS package or government API is fabricated.
The source repository root inspected did not contain a license file. The repository owner authorized
reuse here; a distribution license must still be selected before release. Do not infer an open-source
license from public availability.

## Existing contract and limitations

The inspected upstream `validate_parcel_from_files()` loads historical and modern CSVs, aligns
control points using an affine transform, creates polygons, calculates corresponding-point
deviations and overlap, checks survey points, and invokes `validate_parcel()`.
Only that final decision function is copied in this foundation batch. The complete file-based
pipeline and its public interface are not yet integrated or exposed through HTTP.

The decision function computes maximum and arithmetic-mean supplied deviations. Threshold
comparisons are inclusive. All three checks must pass for `VERIFIED`; otherwise it returns
`MISMATCH`. An empty deviation dictionary raises `ValueError`. These behaviors are characterized
before any refactor. The function does not validate input types, units, ranges, or finite values;
it must not be exposed directly to untrusted requests.

The inspected upstream survey loader accepts latitude/longitude or x/y CSVs. Its projection helper
always uses EPSG:32643 (UTM Zone 43N). That fixed CRS is not an India-wide spatial reference strategy.
Local x/y coordinates alone do not establish units, datum, or georeferencing. Corresponding-point
displacement also must not be labelled as a complete continuous-boundary distance metric.

## Integration sequence

| Stage | Required work |
|---|---|
| Characterization | Preserve the copied decision engine and assert matching, failing and threshold cases |
| Complete source inspection | Read remaining transformation, geometry, overlap, point-check and data-loading modules before copying/refactoring |
| Input adapter | Reject nonfinite numbers, duplicate IDs, invalid geometry, absent CRS and invalid control-point configurations |
| CRS adapter | Preserve legacy calls while introducing explicit CRS and appropriate projected metric calculations |
| Persistence | Store versioned geometries in PostGIS with provenance; store documents and artifacts in object storage |
| Rule management | Version configurable validation rules separately from parcel geometry |
| Evidence review | Audit human review independently of automated check status |

For historical affine alignment, retain control-point selection, residuals and transformation
parameters. Review possible changes that alignment could mask. Maintain source and output CRS.
Never compute metre-based distances directly on longitude/latitude degrees.

## Interpretation and evidence

Test thresholds are synthetic configuration values, not official Indian survey tolerances.
`VERIFIED` here means the supplied measurements satisfy the configured automated checks; it is not
proof of ownership, a legal boundary determination, or human approval. The future data model must
keep automated status, reviewer status and authoritative record references separate.

The inspected upstream `test_validation_engine.py` and `test_mismatch.py` print results without
assertions. GeoNet adds assertion-based characterization tests; the remaining upstream test suite
has not been certified. Source inspection is not a substitute for running the checks.
