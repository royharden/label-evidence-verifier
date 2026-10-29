"""Self-contained escaped report; no external resources or active image content."""
from html import escape

from .contracts import Report


def render_html(report: Report) -> str:
    rows = []
    for f in report.findings:
        region = f.evidence.model_dump_json() if f.evidence else "No supported region"
        rows.append("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in (
            f.check_id, f.verdict, f.observed or "", ", ".join(f.reasons),
            str(f.score) if f.score is not None else "undefined", region,
        )) + "</tr>")
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;">'
        '<title>Label evidence review</title><style>body{font:16px system-ui;margin:2rem;max-width:90rem}'
        'td,th{border:1px solid #aaa;padding:.5rem;vertical-align:top;overflow-wrap:anywhere}'
        'table{border-collapse:collapse;width:100%;table-layout:fixed}</style></head><body>'
        f'<h1>Label evidence review</h1><p><strong>{escape(report.banner)}</strong></p>'
        f'<p>Runtime status: {escape(report.runtime_status)}. Scores are not probabilities.</p>'
        '<table><caption>Immutable machine findings</caption><thead><tr>'
        '<th>Check</th><th>Verdict</th><th>Observed</th><th>Reasons</th><th>Score</th><th>Evidence</th>'
        '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'
        '<h2>Unassessed scope</h2><ul>' + ''.join(f'<li>{escape(s)}</li>' for s in report.unassessed_scope)
        + '</ul><h2>Machine record</h2><pre>' + escape(report.model_dump_json(indent=2))
        + '</pre></body></html>'
    )
