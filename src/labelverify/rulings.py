"""Separate annotations for synthetic authored observations, fictional assumptions.

Not legal approval or OCR accuracy; runtime unverified. Actor labels are unverified
claims. This local append-only workflow is not a security or custody boundary.
Importing never opens storage or modifies machine report bytes.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

CHECKS = ("W-TEXT", "W-HEAD", "A-FORMAT", "A-MATCH", "N-MATCH", "B-MATCH", "C-MATCH")
MAX_EVENTS = 10_000
MAX_BYTES = 16 * 1024 * 1024
_FIELDS = frozenset(("schema_version", "revision_key", "machine_sha256", "check_id",
                     "actor_label", "identity_verified", "action", "reason",
                     "expected_prior", "event_id"))


class AnnotationError(ValueError):
    """Annotation transport or concurrency failure."""


class InvalidAnnotation(AnnotationError):
    """Malformed transport; no partial batch committed."""


class AnnotationConflict(AnnotationError):
    """Stale prior, changed retry or inconsistent machine reference."""


def _json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise InvalidAnnotation("expected finite JSON transport") from exc


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise InvalidAnnotation(f"{name} must be a lowercase SHA256")
    return value


def _text(value: Any, name: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise InvalidAnnotation(f"invalid {name}")
    if any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise InvalidAnnotation(f"control/surrogate in {name}")
    return value


def canonical_machine_digest(machine_bytes: bytes) -> str:
    """Hash exact preserved machine bytes without rewriting/normalizing them."""
    if not isinstance(machine_bytes, bytes) or not machine_bytes:
        raise InvalidAnnotation("nonempty exact machine bytes required")
    return hashlib.sha256(machine_bytes).hexdigest()


def revision_key(report_payload: dict[str, Any]) -> str:
    """Hash full validated demo report, including source/application/policy/pins.

    Caller validates DemoReport before supplying its JSON dictionary. Including
    every field conservatively reopens review whenever any report content changes.
    This key is reproducibility metadata, never authentication.
    """
    if not isinstance(report_payload, dict) or not report_payload:
        raise InvalidAnnotation("nonempty validated demo report payload required")
    return hashlib.sha256(_json(report_payload).encode("ascii")).hexdigest()


def _event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise InvalidAnnotation("annotation fields do not match schema v1")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise InvalidAnnotation("schema_version must be 1")
    if value["identity_verified"] is not False:
        raise InvalidAnnotation("actor identity must remain explicitly unverified")
    for name in ("revision_key", "machine_sha256"):
        _digest(value[name], name)
    for name, limit in (("event_id", 128), ("actor_label", 200), ("reason", 4000)):
        _text(value[name], name, limit)
    if value["expected_prior"] is not None:
        _text(value["expected_prior"], "expected_prior", 128)
    if value["check_id"] not in CHECKS:
        raise InvalidAnnotation("unknown check_id")
    if value["action"] not in ("agree", "override", "escalate"):
        raise InvalidAnnotation("unknown annotation action")
    return json.loads(_json(value))  # detach caller-owned transport


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidAnnotation("duplicate JSON object key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise InvalidAnnotation(f"nonfinite JSON constant: {value}")


def _load(line: str) -> Any:
    try:
        return json.loads(line, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError) as exc:
        raise InvalidAnnotation("invalid JSON annotation") from exc


def _batch(events: str | Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(events, str):
        if len(events.encode("utf-8")) > MAX_BYTES:
            raise InvalidAnnotation("JSONL byte limit exceeded")
        lines = events.splitlines()
        if len(lines) > MAX_EVENTS:
            raise InvalidAnnotation("event count limit exceeded")
        if any(not line.strip() for line in lines):
            raise InvalidAnnotation("blank JSONL record")
        events = (_load(line) for line in lines)
    result = []
    total = 0
    for value in events:
        if len(result) >= MAX_EVENTS:
            raise InvalidAnnotation("event count limit exceeded")
        event = _event(value)
        total += len(_json(event)) + 1
        if total > MAX_BYTES:
            raise InvalidAnnotation("batch byte limit exceeded")
        result.append(event)
    return result


def _schema(connection: sqlite3.Connection) -> None:
    # Separate execute calls preserve the encompassing explicit transaction.
    connection.execute("""CREATE TABLE IF NOT EXISTS annotations (
        sequence INTEGER PRIMARY KEY,
        event_id TEXT NOT NULL UNIQUE,
        revision_key TEXT NOT NULL,
        machine_sha256 TEXT NOT NULL,
        check_id TEXT NOT NULL,
        payload TEXT NOT NULL
    )""")
    connection.execute("""CREATE TRIGGER IF NOT EXISTS annotation_no_update
        BEFORE UPDATE ON annotations BEGIN
        SELECT RAISE(ABORT, 'annotations are append-only'); END""")
    connection.execute("""CREATE TRIGGER IF NOT EXISTS annotation_no_delete
        BEFORE DELETE ON annotations BEGIN
        SELECT RAISE(ABORT, 'annotations are append-only'); END""")


def _append(connection: sqlite3.Connection, event: dict[str, Any]) -> bool:
    payload = _json(event)
    prior = connection.execute("SELECT payload FROM annotations WHERE event_id = ?",
                               (event["event_id"],)).fetchone()
    if prior is not None:
        if prior[0] != payload:
            raise AnnotationConflict("event_id already has different content")
        return False  # Retry before CAS; its old prior is intentional.
    machine = connection.execute(
        "SELECT machine_sha256 FROM annotations WHERE revision_key = ? LIMIT 1",
        (event["revision_key"],)).fetchone()
    if machine is not None and machine[0] != event["machine_sha256"]:
        raise AnnotationConflict("machine digest changed within revision")
    head = connection.execute(
        "SELECT event_id FROM annotations WHERE revision_key = ? AND check_id = ? "
        "ORDER BY sequence DESC LIMIT 1",
        (event["revision_key"], event["check_id"])).fetchone()
    if event["expected_prior"] != (head[0] if head else None):
        raise AnnotationConflict("expected_prior differs from current check head")
    connection.execute(
        "INSERT INTO annotations(event_id, revision_key, machine_sha256, check_id, payload) "
        "VALUES (?, ?, ?, ?, ?)",
        (event["event_id"], event["revision_key"], event["machine_sha256"],
         event["check_id"], payload))
    return True


def import_annotations(db_path: str | Path,
                       events: str | Iterable[dict[str, Any]]) -> int:
    """Atomic append in input order; exact retries insert nothing.

    Validation precedes connection. Conflict rolls back the whole batch/schema.
    A failed first write may leave an empty SQLite file, without committed events.
    Future authorized execution only.
    """
    batch = _batch(events)
    if not batch:
        return 0
    connection = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _schema(connection)
        inserted = sum(_append(connection, event) for event in batch)
        connection.commit()
        return inserted
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()


def append_annotation(db_path: str | Path, event: dict[str, Any]) -> dict[str, Any]:
    """Append one separate observation and return detached validated payload."""
    validated = _event(event)
    import_annotations(db_path, [validated])
    return validated


def _read(db_path: str | Path) -> list[dict[str, Any]]:
    path = Path(db_path).resolve(strict=True)
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        rows = connection.execute("SELECT payload FROM annotations ORDER BY sequence")
        events = []
        ids: set[str] = set()
        heads: dict[tuple[str, str], str] = {}
        digests: dict[str, str] = {}
        for row in rows:
            event = _event(_load(row[0]))
            stream = (event["revision_key"], event["check_id"])
            if event["event_id"] in ids or event["expected_prior"] != heads.get(stream):
                raise AnnotationConflict("stored event chain is inconsistent")
            digest = digests.setdefault(event["revision_key"], event["machine_sha256"])
            if digest != event["machine_sha256"]:
                raise AnnotationConflict("stored machine reference is inconsistent")
            ids.add(event["event_id"])
            heads[stream] = event["event_id"]
            events.append(event)
        return events
    finally:
        connection.close()


def export_annotations(db_path: str | Path) -> str:
    """Return canonical ordered JSONL; never create storage on a read path."""
    return "".join(_json(event) + "\n" for event in _read(db_path))


def replay_annotations(db_path: str | Path, key: str) -> dict[str, Any]:
    """Missing/changed revisions reopen; never replace machine findings."""
    _digest(key, "revision_key")
    events = [event for event in _read(db_path) if event["revision_key"] == key]
    return {
        "revision_key": key,
        "status": "annotated" if events else "open",
        "events": events,
        "latest": {event["check_id"]: event for event in events},
        "identity_verified": False,
        "machine_findings_mutated": False,
    }
