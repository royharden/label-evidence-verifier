# Separate fictional demo review annotations

Synthetic authored observations and fictional assumptions. Not legal approval or
OCR accuracy. Runtime unverified. This is source construction only; SQLite,
CLI, import/export and replay have not been executed in Dirty Mode.

The standard-library rulings module has no import-time storage effects.
Annotations are separate records; no function rewrites machine reports,
findings, reasons or evidence. An override is an attributed disagreement, never
a replacement verdict or approval. Agree and escalate are likewise unverified
observations. Show machine reasons alongside annotations and escape actor/reason
text for the presentation destination.

## Revision and exact bytes

The consumer validates the payload as DemoReport before calling
revision_key(report_payload) on its JSON-compatible dictionary. Canonical full
report JSON binds source, application, policy, config and findings. Any change
conservatively opens a separate stream. Preserve the original machine file and
call canonical_machine_digest(machine_bytes) on its exact nonempty bytes. This
does not reserialize; whitespace changes in that file change its digest.

Events store both references. A revision permits only one machine digest.
Preserve existing exact bytes when replaying; a different serialization needs
distinct revision metadata or is rejected. Hashes identify local content, never
authenticate a person, prove correctness or establish custody. No genuine
study/admission gate closes through an annotation.

## API and JSON transport

append_annotation(db_path, event) returns a detached validated event.
import_annotations(db_path, events) accepts JSONL text or event dictionaries and
returns new insert count; exact duplicates are no-ops. Required fields:

| Field | Meaning |
| --- | --- |
| schema_version | integer 1 |
| event_id | caller-supplied unique idempotency key, 1–128 characters |
| revision_key | lowercase SHA256 of full validated report payload |
| machine_sha256 | SHA256 of preserved exact machine bytes |
| check_id | W-TEXT, W-HEAD, A-FORMAT, A-MATCH, N-MATCH, B-MATCH or C-MATCH |
| actor_label | explicit untrusted attribution, 1–200 characters |
| identity_verified | must be false |
| action | agree, override or escalate |
| reason | nonempty stated reason, at most 4000 characters |
| expected_prior | previous event ID for this revision/check, or null initially |

Whitespace-only strings, control characters, surrogates, extra fields, duplicate
JSON keys, nonfinite numbers and unknown check/action values are rejected.
Batch caps are 10,000 events and 16 MiB. Empty input is a no-op; blank JSONL
records are invalid. A terminal newline is accepted.

export_annotations(db_path) returns canonical JSONL in insertion order, terminal
newline for nonempty output. replay_annotations(db_path, key) returns revision_key,
status, events, latest, identity_verified=false and machine_findings_mutated=false.
Latest maps check IDs to their newest events. Annotated means records exist,
never approved/closed; absent revision means open. Changed reports inherit
nothing. Missing database raises FileNotFoundError rather than creating storage.

AnnotationError derives from ValueError; InvalidAnnotation covers malformed
transport, AnnotationConflict covers CAS/idempotency/reference conflicts.
SQLite errors propagate as sqlite3.Error. Failures never mean accepted review.

## Transaction and trust limits

Write paths validate the batch before connecting, then BEGIN IMMEDIATE covers
schema initialization, inserts, per-check expected-prior CAS and idempotence.
Exact retries succeed even if later events advanced the head. Reusing an ID
with different content fails. A later conflicting prior/digest rolls back every
new event in that import. No executescript implicit commit is used. Connections
close in finally blocks. A failed first write may leave an empty SQLite file.
Read-only URI connections revalidate event chains and digest consistency.

UPDATE/DELETE triggers prevent ordinary accidental mutation; a local file owner
can remove triggers or replace the database. This is application append-only
behavior, not tamper-proof storage, authentication, access control, independent
custody or a signature. Builder stand-ins remain delegated stand-ins, not
human-independent. No identities, credentials or attestations are manufactured.

## Deferred activation

After owner authorization, validate rollback on partial import, concurrent CAS,
retry idempotence, export/import/restart replay, changed/missing revision reopening,
exact machine-byte preservation, SQLite errors and presentation escaping. Check
consumer report validation and source/application/policy/config inclusion during
integration. No such runtime success is claimed here.
