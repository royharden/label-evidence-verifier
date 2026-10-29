"""Local JSON seam. No image decoding, OCR, model access or rule acquisition."""
import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from .contracts import Job, Report
from .pipeline import assess
from .report import render_html

MAX_JSON_BYTES = 32 * 1024 * 1024


def main() -> int:
    parser = argparse.ArgumentParser(description="Evidence review only; source milestone, runtime unverified")
    parser.add_argument("command", choices=("check", "report"))
    parser.add_argument("input", type=Path, help="Normalized OCR job for check; machine report for report")
    parser.add_argument("output", type=Path, help="New output path; existing files are preserved")
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("JSON byte cap exceeded")
        if args.command == "check":
            output = assess(Job.model_validate_json(raw)).model_dump_json(indent=2)
        else:
            report = Report.model_validate_json(raw)
            if report != assess(report.source):
                raise ValueError("machine record differs from deterministic source assessment")
            output = render_html(report)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(output)
    except (OSError, ValueError, ValidationError) as error:
        # Avoid echoing source text or full validation payloads to terminal logs.
        print(f"Input/output refused ({type(error).__name__}); no review claim produced.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
