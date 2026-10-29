# Integration contracts — source construction, runtime unverified

Synthetic authored observations; fictional assumptions. Not legal approval or
OCR accuracy. No runtime/import/test/generator/SQLite/browser execution is
recorded by this document. Local machine hashes bind reproducibility, not
authentication, a secure boundary or legal approval.

## Genuine evidence path

`Job.model_validate_json` retains the strict normalized application/panel/OCR/
candidate/pin schema. Decimal application values are JSON strings. Unknown fields,
nonfinite numbers, duplicate identities, invalid boxes and declared pixel/word
caps are refused. The eventual adapter must independently decode actual PNG/JPEG,
verify bytes/pixel limits/orientation/transforms and supply genuine OCR/quality
provenance; these adapters do not exist here.

All seven real `RuleRef` admissions and `Job.admission=admitted` remain required.
Neither documentary flags nor caller strings authenticate human ratification.
Pending admission/missing or unratified rules keep genuine findings at review.
Exact finite literal predicates, contiguous supported words, uniqueness across
panels, containment, bounded proposals, conservative quality and threshold
refusals remain engine responsibilities. Missing evidence has a search observation
receipt; it never becomes verified absence or an invented span. No real sources,
readers, signatures, calibration or legal validity are supplied by the demo.

`check INPUT OUTPUT` assesses the genuine Job. `report INPUT OUTPUT` dispatches
only explicit real/demo transports (legacy missing kind is real), validates all
model invariants, then compares the full report to reassessment before display.
Unknown/mismatched discriminants and changed machine findings are refused.

## Synthetic producer and assessment

Declared exact source seams:

- `demo_artwork.build_demo_bundle()` returns `artifacts` (relative PNG name to
  original bytes), `scenarios` (three raw producer dictionaries), `manifest`
  (body plus actual canonical `manifest_sha256`).
- As-built producer fields: context, application, panels, observations, candidates,
  threshold, pins. context contains scenario_id and manifest_sha256; candidates
  use synthetic_authored and observations have no extra provenance member.
  Manifest payload_core_sha256 hashes every payload field except context, avoiding
  a self-reference. The context manifest hash is verified separately.
- DL4 preserves unchanged raw payloads as .producer.json, validates their exact
  manifest core digests, then upgrades code_sha256 to the installed composition
  source and config_sha256 to bind producer config plus fictional policy/threshold.
  Producer method and authored-quality pins remain intact. No observation/proposal
  coercion, fake OCR engine/traineddata, real rules or human fields are introduced.
- `demo_policy.demo_job_from_payload(dict) -> DemoJob` validates the distinct
  synthetic transport, using the actual local `DEMO_POLICY_SHA256`.
  `pipeline.assess_demo(DemoJob) -> DemoReport` emits
  kind=synthetic_demo_report with fictional policy references and all seven findings.
  The genuine report discriminant is real_evidence_report.
- `demo.create_demo(Path)` accepts only a new directory under an existing parent.
  It validates ordered DEMO-01..03, recipe/payload/artifact hashes and lengths,
  declared panel-to-artwork identity and safe local filenames before writing.
  The PNG signature is checked; there is no independent decode or pixel audit.
  Exact installed source file bytes define code_sha256; it is not a signed build ID.

The producer/assessment path never opens fixtures/demo/expected.json. Expected maps
are later comparison inputs only. Authored confidence/quality values and geometry
are drawing controls, not OCR measurements or independently audited pixel truth.
The fixed threshold is neither calibrated nor probabilistic.

Output: manifest.json, index.html, artwork/*.png and per-scenario .producer.json, .source.json,
.machine.json and .html. The HTML has escaped data strings, CSP prohibiting scripts
and remote images, validated relative PNG paths, complete original artwork and
proposed/tight original-pixel coordinates. No crop/overlay is claimed. Imported
reports render coordinates without guessing sibling artwork locations.
Runtime status always remains unverified_source_milestone in construction artifacts.

All output files use exclusive creation; new demo directory creation also refuses
reuse. Links/junctions are rejected at operation boundaries. Failure may preserve
a partial new directory; never overwrite or silently resume it. These local checks
are not a hostile-filesystem security sandbox or immutable custody guarantee.

## Separate annotation CLI

Read [annotation protocol](DEMO-REVIEW.md) for storage/event semantics. The CLI
validates/reassesses current demo machine JSON before deriving
`canonical_machine_digest(exact_bytes)` and `revision_key(validated_report_dict)`.
Only synthetic reports enter this workflow. Actor labels remain unverified;
machine bytes/findings/reasons are never edited.

After runtime activation only, with a separate existing ledger parent directory:

```text
labelverify review-append NEWDIR/DEMO-01.machine.json --db LEDGER/review.sqlite3 --actor "operator-label" --check A-MATCH --action agree --reason "review note" --event-id first-review
labelverify review-export NEWDIR/DEMO-01.machine.json --db LEDGER/review.sqlite3 --out NEW_EVENTS.jsonl
labelverify review-import NEWDIR/DEMO-01.machine.json --db LEDGER/replayed.sqlite3 --input NEW_EVENTS.jsonl
labelverify review-replay NEWDIR/DEMO-01.machine.json --db LEDGER/replayed.sqlite3 --out NEW_REPLAY.json --html-out NEW_ANNOTATED.html
```

First event for a check uses expected_prior=null. To append to an existing check,
supply `--expected-prior PREVIOUS_EVENT_ID`; exact retries reuse event ID/content.
The CLI constructs schema_version=1, identity_verified=false, current revision and
exact machine hash. DL3 owns transaction/CAS/idempotence implementation.
Import parses and binds the entire JSONL batch before transactional mutation;
wrong revision/digest or authenticated-identity claims are refused. Export selects
current-revision events only. Replay of a new revision is open, not old approval.
A reused DB's changed-revision history remains separate.

DB suffix must be .sqlite3 outside the machine artifact directory. Every annotation
export/replay/HTML output is a distinct new file. JSON/HTML annotations are escaped
and separate from original machine artifacts. JSONL event arrays/blank records and
oversized/malformed input are refused. Supplied actor labels are not authenticated
human approvals, and override annotations never remove hard machine reasons.

## Deferred activation

The one later acceptance recipe is [DEMO-ACCEPTANCE.md](DEMO-ACCEPTANCE.md), HELD.
INT reconciles assembled producer/schema/annotation APIs; no joined runtime result
is claimed here. Later authorized validation must exercise all three expected maps,
ordinary pending real jobs, transport tampering, safe paths/exclusive creation,
HTML injection, transactional CAS/conflicts/idempotence/import rollback, restart/
replay and deterministic reproduction. Genuine P1 admission remains pending.
No keys, spend, accounts, services, OCR/model calls, real unsealing or publication.
