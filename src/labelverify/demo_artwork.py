"""Original synthetic artwork and authored observations; runtime unverified.

Fictional assumptions only, not legal approval or OCR accuracy. No external fonts,
assets, randomness, product/eval imports or expected-outcome consumption.
"""
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path, PurePosixPath

WIDTH, HEIGHT = 960, 480
SCALE = 3
ADVANCE = 12
LINE_HEIGHT = 18
NOTICE = "DEMO NOTICE: FICTIONAL ARTWORK. REVIEW EVIDENCE ONLY."
DISCLAIMER = (
    "Synthetic authored observations; fictional assumptions; not legal approval "
    "or OCR accuracy; runtime unverified."
)
# Original compact 3x5 drawing controls authored for this demo, not a system font.
# Every row is a three-bit mask; these are not independently audited glyph truth.
GLYPHS = {
    "A": (2, 5, 7, 5, 5), "B": (6, 5, 6, 5, 6),
    "C": (3, 4, 4, 4, 3), "D": (6, 5, 5, 5, 6),
    "E": (7, 4, 6, 4, 7), "F": (7, 4, 6, 4, 4),
    "G": (3, 4, 5, 5, 3), "H": (5, 5, 7, 5, 5),
    "I": (7, 2, 2, 2, 7), "J": (1, 1, 1, 5, 2),
    "K": (5, 5, 6, 5, 5), "L": (4, 4, 4, 4, 7),
    "M": (5, 7, 7, 5, 5), "N": (5, 7, 7, 7, 5),
    "O": (2, 5, 5, 5, 2), "P": (6, 5, 6, 4, 4),
    "Q": (2, 5, 5, 3, 1), "R": (6, 5, 6, 5, 5),
    "S": (3, 4, 2, 1, 6), "T": (7, 2, 2, 2, 2),
    "U": (5, 5, 5, 5, 7), "V": (5, 5, 5, 5, 2),
    "W": (5, 5, 7, 7, 5), "X": (5, 5, 2, 5, 5),
    "Y": (5, 5, 2, 2, 2), "Z": (7, 1, 2, 4, 7),
    "0": (7, 5, 5, 5, 7), "1": (2, 6, 2, 2, 7),
    "2": (6, 1, 2, 4, 7), "3": (6, 1, 2, 1, 6),
    "4": (5, 5, 7, 1, 1), "5": (7, 4, 6, 1, 6),
    "6": (3, 4, 6, 5, 2), "7": (7, 1, 2, 2, 2),
    "8": (2, 5, 2, 5, 2), "9": (2, 5, 3, 1, 6),
    "-": (0, 0, 7, 0, 0), ".": (0, 0, 0, 0, 2),
    ":": (0, 2, 0, 2, 0), " ": (0, 0, 0, 0, 0),
}
# Lowercase glyphs are explicit same-shape display aliases; observation text retains
# exact case (not OCR output). The finite set accepts no other Unicode characters.
GLYPHS.update({key.lower(): value for key, value in tuple(GLYPHS.items())
               if "A" <= key <= "Z"})


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_artifact_name(name):
    """Reject absolute, parent, Windows drive/ADS and nonportable artifact paths."""
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", name):
        raise ValueError("unsupported artifact name")
    path = PurePosixPath(name)
    if (path.is_absolute() or str(path) != name
            or any(part in ("", ".", "..") for part in name.split("/"))):
        raise ValueError("unsafe artifact path")
    return name


def _box(x0, y0, x1, y1):
    if any(type(n) is not int for n in (x0, y0, x1, y1)):
        raise ValueError("integer drawing controls required")
    if not (0 <= x0 < x1 <= WIDTH and 0 <= y0 < y1 <= HEIGHT):
        raise ValueError("drawing outside canvas")
    return dict(x0=float(x0), y0=float(y0), x1=float(x1), y1=float(y1))


def _rectangle(pixels, x0, y0, x1, y1, color):
    _box(x0, y0, x1, y1)
    if len(color) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in color):
        raise ValueError("RGB color required")
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        start = (y * WIDTH + x0) * 3
        pixels[start:start + len(row)] = row


def _line(pixels, words, text, x, y, panel_id):
    if not text or text != " ".join(text.split()) or any(c not in GLYPHS for c in text):
        raise ValueError("unsupported or noncanonical text")
    _box(x, y, x + len(text) * ADVANCE - SCALE, y + 5 * SCALE)
    first = len(words)
    cursor = x
    for token in text.split(" "):
        start = cursor
        for char in token:
            for row, mask in enumerate(GLYPHS[char]):
                for column in range(3):
                    if mask & (1 << (2 - column)):
                        left, top = cursor + column * SCALE, y + row * SCALE
                        _rectangle(pixels, left, top, left + SCALE, top + SCALE, (20, 35, 50))
            cursor += ADVANCE
        words.append({
            "word_id": panel_id + "-w" + str(len(words)),
            "text": token, "box": _box(start, y, cursor - SCALE, y + 5 * SCALE),
            "confidence": 99.0,
        })
        cursor += ADVANCE
    return words[first:]


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(
        ">I", zlib.crc32(kind + data) & 0xffffffff)


def _png(pixels):
    if len(pixels) != WIDTH * HEIGHT * 3:
        raise ValueError("invalid RGB buffer")
    scanlines = b"".join(b"\x00" + pixels[y * WIDTH * 3:(y + 1) * WIDTH * 3]
                         for y in range(HEIGHT))
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(scanlines, level=9))
            + _chunk(b"IEND", b""))


def _region(panel, page_index, words):
    return {
        "panel_id": panel["panel_id"], "panel_sha256": panel["original_sha256"],
        "transform_sha256": panel["transform_sha256"], "page_index": page_index,
        "source_width": WIDTH, "source_height": HEIGHT,
        "box": {
            "x0": min(w["box"]["x0"] for w in words),
            "y0": min(w["box"]["y0"] for w in words),
            "x1": max(w["box"]["x1"] for w in words),
            "y1": max(w["box"]["y1"] for w in words),
        },
        "word_ids": [w["word_id"] for w in words],
    }


def _scenario(scenario_id):
    if scenario_id not in ("DEMO-01", "DEMO-02", "DEMO-03"):
        raise ValueError("unknown demo scenario")
    panels, observations, artifacts, spans = [], [], {}, {}
    for index, side in enumerate(("front", "back")):
        panel_id = scenario_id + "-" + side
        pixels = bytearray([245, 246, 240]) * (WIDTH * HEIGHT)
        _rectangle(pixels, 12, 12, WIDTH - 12, 18, (70, 100, 120))
        words = []
        if side == "front":
            spans["B-MATCH"] = (index, _line(pixels, words, "ZUVEXA-77", 40, 60, panel_id))
            spans["C-MATCH"] = (index, _line(pixels, words, "FICTIONAL SPIRIT", 40, 110, panel_id))
            alcohol = "41.0 percent" if scenario_id == "DEMO-02" else "40.0 percent"
            selected = _line(pixels, words, alcohol, 40, 160, panel_id)
            spans["A-FORMAT"] = (index, selected)
            spans["A-MATCH"] = (index, selected)
            if scenario_id != "DEMO-03":
                spans["N-MATCH"] = (index, _line(pixels, words, "750 mL", 40, 210, panel_id))
            if scenario_id == "DEMO-03":
                _line(pixels, words, "ZUVEXA-77", 40, 280, panel_id)
        else:
            selected = _line(pixels, words, NOTICE, 40, 60, panel_id)
            spans["W-TEXT"] = (index, selected)
            spans["W-HEAD"] = (index, selected[:2])
            # These disclosed captions are image content but not observation tokens:
            # observations are a deliberately authored subset, not OCR completeness.
            _line(pixels, [], "SYNTHETIC DEMO ONLY", 40, 300, panel_id + "-caption")
            _line(pixels, [], "NOT LEGAL APPROVAL", 40, 330, panel_id + "-caption2")
        image = _png(pixels)
        name = safe_artifact_name("artwork/" + panel_id + ".png")
        artifacts[name] = image
        transform = {"kind": "identity", "width": WIDTH, "height": HEIGHT,
                     "coordinate_convention": "half_open_source_pixels"}
        panel = {
            "panel_id": panel_id, "original_sha256": digest(image),
            "transform_sha256": digest(canonical_bytes(transform)), "width": WIDTH,
            "height": HEIGHT, "byte_length": len(image), "media_type": "image/png",
            "complete": True, "orientation_applied": True, "static_image": True,
        }
        panels.append(panel)
        observations.append({
            "panel_id": panel_id, "words": words, "status": "ok",
            "contrast_quality": 1.0, "sharpness_quality": 1.0,
            "hard_quality_reasons": [],
        })
    candidates = []
    for check in ("W-TEXT", "W-HEAD", "A-FORMAT", "A-MATCH", "N-MATCH", "B-MATCH", "C-MATCH"):
        if check not in spans:
            continue
        index, words = spans[check]
        region = _region(panels[index], index, words)
        if scenario_id == "DEMO-03" and check == "W-TEXT":
            # Deliberately invalid support, still a schema-valid in-canvas box.
            region["box"] = _box(40, 200, 400, 220)
        candidates.append({"check_id": check, "value": " ".join(w["text"] for w in words),
                           "proposed": region, "provenance": "synthetic_authored"})
    payload = {
        "context": {"scenario_id": scenario_id},
        "application": {
            "intended_label_brand": "ZUVEXA-77",
            "intended_label_class_type": "FICTIONAL SPIRIT",
            "intended_label_alcohol_percent": "40.0", "intended_label_net_ml": "750",
            "domain": "fictional_domestic_plain_distilled_spirits",
            "complete_flat_front_back": True,
        },
        "panels": panels, "observations": observations,
        "candidates": candidates, "threshold": 0.5,
    }
    return payload, artifacts


def build_demo_bundle():
    """Build in memory only when later execution is authorized.

    Returns artifacts: safe path -> PNG bytes; scenarios: plain source payloads;
    manifest: actual content hashes and authored-provenance statements.
    Expected maps remain completely separate from this producer/prediction path.
    """
    source = Path(__file__)
    if source.is_symlink() or source.suffix != ".py" or not source.is_file():
        raise ValueError("producer requires its regular local Python source file")
    for parent in source.parents:
        if parent.is_symlink():
            raise ValueError("symlink source ancestry refused")
    source_digest = digest(source.read_bytes())
    pins = {
        "code_sha256": source_digest,
        "config_sha256": digest(canonical_bytes({"threshold": 0.5, "width": WIDTH,
                                                "height": HEIGHT, "scale": SCALE})),
        "quality_transforms_sha256": digest(canonical_bytes({
            "provenance": "synthetic_authored", "contrast": 1.0, "sharpness": 1.0})),
        "method_sha256": digest(canonical_bytes({
            "method": "original-tiny-glyph-v1", "glyphs": GLYPHS})),
    }
    scenarios, artifacts, manifest_items = [], {}, []
    for scenario_id in ("DEMO-01", "DEMO-02", "DEMO-03"):
        payload, images = _scenario(scenario_id)
        payload["pins"] = dict(pins)
        scenarios.append(payload)
        artifacts.update(images)
        manifest_items.append({
            "scenario_id": scenario_id, "payload_core_sha256": digest(canonical_bytes({
                key: value for key, value in payload.items() if key != "context"})),
            "artifacts": [{"path": path, "sha256": digest(data), "byte_length": len(data)}
                          for path, data in sorted(images.items())],
        })
    manifest_body = {
        "format": "labelverify-synthetic-artwork-v1", "demo_only": True,
        "disclaimer": DISCLAIMER, "observations": "synthetic_authored_observations",
        "confidence_quality": "authored constants, not OCR measurements or calibrated probabilities",
        "geometry": "drawing controls, not independently audited final-pixel truth",
        "originality": "builder-authored tiny glyphs and geometry; no external fonts or assets",
        "identity_verified": False, "independent_truth": False,
        "render_status": "generated_on_invocation_runtime_not_validated",
        "producer_source_sha256": source_digest,
        "code_pin_scope": "producer module source only; not whole installed product",
        "payload_core_digest_scope": "all payload fields except context; avoids manifest self-reference",
        "scenarios": manifest_items,
    }
    manifest = dict(manifest_body, manifest_sha256=digest(canonical_bytes(manifest_body)))
    for payload in scenarios:
        payload["context"]["manifest_sha256"] = manifest["manifest_sha256"]
    return {"artifacts": artifacts, "scenarios": scenarios, "manifest": manifest}
