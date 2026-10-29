"""Local evidence/demo CLI. Synthetic observations, not legal approval/OCR accuracy."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

from pydantic import ValidationError

from .contracts import CHECKS, Job, Report
from .pipeline import assess
from .report import DEMO_NOTICE, render_html

MAX_JSON_BYTES = 32 * 1024 * 1024


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=DEMO_NOTICE)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "report"):
        command = commands.add_parser(name)
        command.add_argument("input", type=Path)
        command.add_argument("output", type=Path, help="New path; existing files preserved")
    demo = commands.add_parser("demo", help="Three synthetic mock scenarios; runtime unverified")
    demo.add_argument("--mode", choices=("mock",), required=True)
    demo.add_argument("--out", type=Path, required=True, help="New directory under an existing parent")
    for name in ("review-append", "review-import", "review-export", "review-replay"):
        command = commands.add_parser(name, help="Separate unauthenticated demo annotation workflow")
        command.add_argument("machine", type=Path, help="Preserved demo machine JSON, reassessed first")
        command.add_argument("--db", type=Path, required=True, help="Separate .sqlite3 path")
        if name == "review-append":
            command.add_argument("--actor", required=True, help="Unverified actor label")
            command.add_argument("--check", choices=CHECKS, required=True)
            command.add_argument("--action", choices=("agree", "override", "escalate"), required=True)
            command.add_argument("--reason", required=True)
            command.add_argument("--event-id", required=True, help="Unique retry/idempotency key")
            command.add_argument("--expected-prior", default=None, help="Previous event ID for this check")
        elif name == "review-import":
            command.add_argument("--input", type=Path, required=True, help="Current-revision JSONL batch")
        else:
            command.add_argument("--out", type=Path, required=True, help="New output file")
            if name == "review-replay":
                command.add_argument("--html-out", type=Path, help="Optional separate new escaped HTML view")
    return parser


def _review(args) -> None:
    from .demo import canonical_bytes, local_path, read_bytes, strict_json, validated_machine, write_new
    from .rulings import (append_annotation, canonical_machine_digest, export_annotations,
                          import_annotations, replay_annotations, revision_key)

    raw = read_bytes(args.machine)
    report = validated_machine(raw)
    if getattr(report, "kind", None) != "synthetic_demo_report":
        raise ValueError("annotation workflow accepts only explicit synthetic demo reports")
    key = revision_key(report.model_dump(mode="json"))
    machine_hash = canonical_machine_digest(raw)
    db = local_path(args.db)
    machine = local_path(args.machine)
    if db.suffix.lower() != ".sqlite3" or db == machine or db.parent == machine.parent:
        raise ValueError("use separate .sqlite3 storage outside the machine artifact directory")
    # The DB path and its journal companions must never alias preserved artifacts.
    if not db.parent.is_dir():
        raise ValueError("annotation storage parent must exist")

    def bound(event):
        if not isinstance(event, dict) or event.get("revision_key") != key:
            raise ValueError("annotation revision differs from current machine; review reopened")
        if event.get("machine_sha256") != machine_hash or event.get("identity_verified") is not False:
            raise ValueError("annotation machine digest/identity mismatch")
        return event

    if args.command == "review-append":
        append_annotation(db, {
            "schema_version": 1, "revision_key": key, "machine_sha256": machine_hash,
            "check_id": args.check, "actor_label": args.actor, "identity_verified": False,
            "action": args.action, "reason": args.reason, "expected_prior": args.expected_prior,
            "event_id": args.event_id,
        })
    elif args.command == "review-import":
        content = read_bytes(args.input).decode("utf-8")
        lines = content.splitlines()
        if not lines or len(lines) > 10_000 or any(not line.strip() for line in lines):
            raise ValueError("invalid JSONL batch")
        events = [bound(strict_json(line)) for line in lines]
        # Entire transport is checked before DL3's transactional all-or-nothing import.
        import_annotations(db, events)
    elif args.command == "review-export":
        lines = export_annotations(db).splitlines()
        events = [strict_json(line) for line in lines]
        current = [bound(event) for event in events if event["revision_key"] == key]
        content = b"".join(canonical_bytes(event) + b"\n" for event in current)
        write_new(args.out, content)
    else:
        replay = replay_annotations(db, key)
        for event in replay["events"]:
            bound(event)
        # Preflight both exclusive output paths before either write.
        destinations = [local_path(args.out)]
        if args.html_out is not None:
            destinations.append(local_path(args.html_out))
        if len(set(destinations)) != len(destinations) or any(path.exists() for path in destinations):
            raise ValueError("replay requires distinct new output paths")
        if any(path == db for path in destinations):
            raise ValueError("annotation output cannot alias storage")
        write_new(args.out, canonical_bytes({"notice": DEMO_NOTICE, "replay": replay}))
        if args.html_out is not None:
            write_new(args.html_out, render_html(report, annotations=replay).encode("utf-8"))


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "check":
            from .demo import read_bytes, write_new
            output = assess(Job.model_validate_json(read_bytes(args.input))).model_dump_json(indent=2)
            write_new(args.output, output.encode("utf-8"))
        elif args.command == "report":
            from .demo import read_bytes, validated_machine, write_new
            report = validated_machine(read_bytes(args.input))
            write_new(args.output, render_html(report).encode("utf-8"))
        elif args.command == "demo":
            from .demo import create_demo
            create_demo(args.out)
        else:
            _review(args)
    except (OSError, ValueError, TypeError, KeyError, ValidationError, sqlite3.Error) as error:
        # Never echo source text, annotations or full validation payloads into logs.
        print(f"Input/output refused ({type(error).__name__}); no review claim produced.", file=sys.stderr)
        return 2
    print(DEMO_NOTICE if args.command.startswith(("demo", "review-")) else
          "Evidence review only; runtime unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
