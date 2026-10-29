# label-evidence-verifier

Evidence review only. Not a label approval or agency determination.

Source milestone for fictional domestic plain distilled-spirits artwork.
**Dirty Mode construction; runtime unverified.** No accuracy or compliance claim.

Authoritative adopted plan: `../planning/promoted/PLAN-M16-v1.md`. Coordination and transcripts remain outside this product repository.

Built source: strict typed application/panel/OCR/rule contracts; seven finite
present-evidence checks; contiguous OCR support and conservative abstention; JSON
machine records and escaped self-contained HTML. Missing evidence always needs
review. All seven rule admissions remain required. No ratified rule pack is shipped.

The CLI consumes a normalized OCR job, not raw images. Future authorized activation
requires Python 3.12+, resolving and locking Pydantic 2 and setuptools, and installing
the local package. Dependencies have not been installed or runtime-validated.

```text
labelverify check normalized-job.json machine-report.json
labelverify report machine-report.json review.html
```

Outputs must be new paths. Use `Job.model_json_schema()` after activation to obtain
the input schema; decimal application values are JSON strings. See
[integration contract](docs/INTEGRATION.md) for adapter responsibilities and limits.

Deferred: image decode/OCR/quality detectors, official legal-source acquisition and
human ratification, split-warning policy detection, numeric contradictory-field
detection, calibration/experimental absence/baselines, crops/overlays, reviewer
annotation ledger, provider accounting, evaluation/custody and actual runtime tests.
No keys or hosted services are required by this milestone. No study data, legal
sources or sibling code are bundled. Licence decisions remain pending.
