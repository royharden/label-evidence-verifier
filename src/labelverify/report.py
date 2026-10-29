"""Escaped local evidence views; synthetic observations are never OCR measurements."""
from __future__ import annotations
import json
import re
from html import escape
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Mapping

from .contracts import Report

if TYPE_CHECKING:
    from .contracts import DemoReport

DEMO_NOTICE = (
    "Synthetic authored observations; fictional assumptions. "
    "Not legal approval or OCR accuracy. Runtime unverified."
)


def safe_image_path(value: str) -> str:
    """Only literal relative PNG paths; reject URI, drive, escape and encoded paths."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_/-]+\.png", value):
        raise ValueError("unsafe artwork path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("unsafe artwork path")
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                *(f"lpt{i}" for i in range(1, 10))}
    if any(part.split(".")[0].casefold() in reserved for part in value.split("/")):
        raise ValueError("reserved artwork path")
    return value


def render_html(report: Report | DemoReport, *, images: Mapping[str, str] | None = None,
                annotations: object | None = None) -> str:
    # DemoReport deliberately has a distinct transport, but shares this display shape.
    is_demo = getattr(report, "kind", None) == "synthetic_demo_report"
    if images and not is_demo:
        raise ValueError("local artwork is restricted to the synthetic demo")
    rows = []
    for finding in report.findings:
        evidence = finding.evidence.model_dump_json() if finding.evidence else "No supported region"
        proposed = finding.proposed.model_dump_json() if finding.proposed else "No proposal"
        rows.append("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in (
            finding.check_id, finding.verdict, finding.observed or "", ", ".join(finding.reasons),
            str(finding.score) if finding.score is not None else "undefined",
            f"Tight supported region: {evidence}\nOriginal proposal: {proposed}",
        )) + "</tr>")
    artwork = []
    panels = {panel.panel_id: panel for panel in report.source.panels}
    for panel_id, filename in (images or {}).items():
        if panel_id not in panels:
            raise ValueError("unknown artwork panel")
        local = safe_image_path(filename)
        panel = panels[panel_id]
        artwork.append(
            f'<figure><img src="{escape(local, quote=True)}" alt="Synthetic panel {escape(panel_id, quote=True)}">'
            f'<figcaption>{escape(panel_id)} — full original artwork; {panel.width} × {panel.height}. '
            'Evidence coordinates above use original pixels. No crop or overlay is claimed.</figcaption></figure>'
        )
    demo = f"<p><strong>{escape(DEMO_NOTICE)}</strong></p>" if is_demo else ""
    annotation_view = ""
    if annotations is not None:
        annotation_view = (
            '<h2>Separate review annotations</h2><p>Supplied actor labels are unauthenticated. '
            'Annotations do not change machine findings or remove hard reasons.</p><pre>'
            + escape(json.dumps(annotations, ensure_ascii=True, indent=2, allow_nan=False)) + '</pre>'
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
        'img-src &#39;self&#39;; style-src &#39;unsafe-inline&#39;">'
        '<title>Label evidence review</title><style>body{font:16px system-ui;margin:2rem;max-width:90rem}'
        'td,th{border:1px solid #aaa;padding:.5rem;vertical-align:top;overflow-wrap:anywhere}'
        'table{border-collapse:collapse;width:100%;table-layout:fixed}pre{white-space:pre-wrap}'
        'img{max-width:100%;height:auto}</style></head><body>'
        f'<h1>Label evidence review</h1><p><strong>{escape(report.banner)}</strong></p>' + demo
        + f'<p>Runtime status: {escape(report.runtime_status)}. Scores are not probabilities.</p>'
        '<table><caption>Immutable machine findings</caption><thead><tr>'
        '<th>Check</th><th>Verdict</th><th>Observed</th><th>Reasons</th><th>Score</th><th>Evidence</th>'
        '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'
        + ''.join(artwork) + annotation_view
        + '<h2>Unassessed scope</h2><ul>'
        + ''.join(f'<li>{escape(scope)}</li>' for scope in report.unassessed_scope)
        + '</ul><h2>Machine record</h2><pre>' + escape(report.model_dump_json(indent=2))
        + '</pre></body></html>'
    )
