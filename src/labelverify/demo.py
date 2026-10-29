"""Compose the local synthetic demo. Construction only; runtime unverified."""
import hashlib
import json
from pathlib import Path

from .report import DEMO_NOTICE, render_html, safe_image_path

MAX_JSON_BYTES = 32 * 1024 * 1024
SCENARIOS = ("DEMO-01", "DEMO-02", "DEMO-03")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict_json(raw: str | bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON object key")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("nonfinite JSON constant")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def local_path(path: Path) -> Path:
    """Reject links/junctions before local artifact operations (not a sandbox)."""
    absolute = path.absolute()
    for part in (absolute, *absolute.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError("linked artifact paths refused")
    return absolute


def read_bytes(path: Path) -> bytes:
    with local_path(path).open("rb") as stream:
        raw = stream.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("JSON byte cap exceeded")
    return raw


def read_json(path: Path) -> object:
    return strict_json(read_bytes(path))


def write_new(path: Path, content: bytes) -> None:
    with local_path(path).open("xb") as stream:
        stream.write(content)


def validated_machine(raw: bytes):
    """Reassess both transports; no imported finding is trusted by display."""
    from .contracts import DemoReport, Report
    from .pipeline import assess, assess_demo

    payload = strict_json(raw)
    if not isinstance(payload, dict):
        raise ValueError("expected machine report object")
    kind = payload.get("kind", "real_evidence_report")
    if kind == "synthetic_demo_report":
        report = DemoReport.model_validate_json(raw)
        expected = assess_demo(report.source)
    elif kind == "real_evidence_report":
        report = Report.model_validate_json(raw)
        expected = assess(report.source)
    else:
        raise ValueError("unknown report transport")
    if report != expected:
        raise ValueError("machine record differs from deterministic source assessment")
    return report


def _producer_job(payload: dict, manifest_hash: str, code_hash: str):
    """Bind DL2's as-built DemoJob-shaped payload to the installed composition."""
    from .demo_policy import DEMO_POLICY_SHA256, demo_job_from_payload

    if set(payload) != {"context", "application", "panels", "observations", "candidates", "threshold", "pins"}:
        raise ValueError("unexpected producer fields")
    if payload["context"]["scenario_id"] not in SCENARIOS:
        raise ValueError("unknown scenario")
    if payload["context"]["manifest_sha256"] != manifest_hash:
        raise ValueError("producer context/manifest mismatch")
    # The unchanged producer payload is preserved separately. These two upgraded
    # pins bind assessment/presentation source and policy as well as producer bytes.
    pins = dict(payload["pins"])
    pins["code_sha256"] = code_hash
    pins["config_sha256"] = digest(canonical_bytes({
        "producer_config_sha256": payload["pins"]["config_sha256"],
        "assumption_pack_sha256": DEMO_POLICY_SHA256, "threshold": payload["threshold"],
    }))
    return demo_job_from_payload({
        **payload, "pins": pins,
    })


def _prepare_bundle(bundle: dict) -> dict[str, bytes]:
    from .pipeline import assess_demo

    if set(bundle) != {"artifacts", "scenarios", "manifest"}:
        raise ValueError("unexpected bundle shape")
    artifacts, scenarios, manifest = bundle["artifacts"], bundle["scenarios"], bundle["manifest"]
    if tuple(item["context"]["scenario_id"] for item in scenarios) != SCENARIOS:
        raise ValueError("all three ordered scenarios required")
    body = dict(manifest)
    supplied_hash = body.pop("manifest_sha256")
    if digest(canonical_bytes(body)) != supplied_hash:
        raise ValueError("manifest digest mismatch")
    items = manifest["scenarios"]
    if tuple(item["scenario_id"] for item in items) != SCENARIOS:
        raise ValueError("manifest scenario mismatch")
    declared = {}
    for item, payload in zip(items, scenarios, strict=True):
        core = {key: value for key, value in payload.items() if key != "context"}
        if item["payload_core_sha256"] != digest(canonical_bytes(core)):
            raise ValueError("producer payload digest mismatch")
        for artifact in item["artifacts"]:
            name = safe_image_path(artifact["path"])
            if name in declared:
                raise ValueError("duplicate artifact")
            declared[name] = artifact
    if set(artifacts) != set(declared):
        raise ValueError("manifest artwork set mismatch")
    files = {}
    for name, data in artifacts.items():
        safe_image_path(name)
        if not isinstance(data, bytes) or len(data) > 10 * 1024 * 1024:
            raise ValueError("invalid artwork bytes")
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("expected authored PNG bytes")
        metadata = declared[name]
        if digest(data) != metadata["sha256"] or len(data) != metadata["byte_length"]:
            raise ValueError("artwork digest/length mismatch")
        files[name] = data
    # Hash exact installed source bytes, not a fabricated revision or execution receipt.
    code_parts = []
    for name in ("contracts.py", "pipeline.py", "demo_policy.py", "demo_artwork.py", "demo.py", "report.py", "cli.py"):
        code_parts.append(name.encode() + b"\0" + Path(__file__).with_name(name).read_bytes())
    code_hash = digest(b"\0".join(code_parts))
    files["manifest.json"] = canonical_bytes(manifest)
    for payload in scenarios:
        scenario = payload["context"]["scenario_id"]
        job = _producer_job(payload, supplied_hash, code_hash)
        report = assess_demo(job)
        images = {}
        for panel in job.panels:
            name = safe_image_path("artwork/" + panel.panel_id + ".png")
            if name not in files or digest(files[name]) != panel.original_sha256:
                raise ValueError("panel/artwork binding mismatch")
            if len(files[name]) != panel.byte_length:
                raise ValueError("panel/artwork length mismatch")
            images[panel.panel_id] = name
        files[scenario + ".producer.json"] = canonical_bytes(payload)
        files[scenario + ".source.json"] = job.model_dump_json(indent=2).encode()
        files[scenario + ".machine.json"] = report.model_dump_json(indent=2).encode()
        files[scenario + ".html"] = render_html(report, images=images).encode()
    files["index.html"] = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;">'
        '<title>Synthetic evidence demo</title><h1>Synthetic evidence demo</h1><p>' + DEMO_NOTICE
        + '</p><ul>' + ''.join('<li><a href="' + name + '.html">' + name + '</a></li>' for name in SCENARIOS)
        + '</ul><p>Three builder-authored software examples, not independent pilots. '
        'Expected outcomes are not consumed by prediction. Annotation commands are separate.</p></html>'
    ).encode()
    return files


def create_demo(out: Path) -> None:
    """Future invocation only: never reuse a directory or overwrite machine artifacts."""
    from .demo_artwork import build_demo_bundle

    target = local_path(out)
    if target.exists() or not target.parent.is_dir():
        raise ValueError("demo requires a new directory under an existing parent")
    files = _prepare_bundle(build_demo_bundle())
    # Validate every name/prefix before creating any directory.
    for name in files:
        parts = name.split("/")
        if any(part in ("", ".", "..") or ":" in part or "\\" in part for part in parts):
            raise ValueError("unsafe output name")
    target.mkdir()  # no exist_ok; partial failures are preserved, never silently resumed
    for name, data in files.items():
        destination = target.joinpath(*name.split("/"))
        if destination.parent != target:
            destination.parent.mkdir(parents=True, exist_ok=True)
        write_new(destination, data)
