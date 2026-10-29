"""Later-authorized local synthetic generator; runtime unverified, no OCR/legal claim."""
import argparse
import json
from pathlib import Path

from labelverify.demo_artwork import build_demo_bundle, safe_artifact_name


def write_demo(destination):
    """Exclusive new directory; no overwrite or expected-map consumption."""
    target = Path(destination)
    # Reject symlink parents: avoid writing through redirected output ancestry.
    for parent in (target, *target.parents):
        if parent.is_symlink():
            raise ValueError("symlink output path refused")
    target.mkdir(parents=False, exist_ok=False)
    bundle = build_demo_bundle()
    for name, data in bundle["artifacts"].items():
        relative = safe_artifact_name(name)
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    for name, value in (("manifest.json", bundle["manifest"]),
                        ("scenarios.json", bundle["scenarios"])):
        with (target / name).open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="new directory; parent must exist")
    args = parser.parse_args()
    write_demo(args.out)


if __name__ == "__main__":
    main()
