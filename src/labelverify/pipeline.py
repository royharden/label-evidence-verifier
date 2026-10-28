"""Conservative F1 present-evidence path; no OCR, source fetching or model execution."""
import hashlib
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from .contracts import CHECKS, Box, Candidate, Finding, Job, Region, Report, RuleRef, SearchReceipt


def normalize(value: str, mode: str) -> str:
    if mode == "nfc_case_whitespace":
        value = unicodedata.normalize("NFC", value)
    if mode in ("nfc_case_whitespace", "case_whitespace"):
        value = value.casefold()
    return " ".join(value.split())


def admitted(rule: RuleRef) -> bool:
    """Documentary flags are input claims, not authentication of a human."""
    return bool(rule.ratified and rule.final_text_checked and rule.human_ratifier
                and all(rule.reader_ids) and rule.reader_ids[0] != rule.reader_ids[1]
                and rule.citation and rule.as_of and rule.version)


def supported(job: Job, candidate: Candidate, rule: RuleRef) -> tuple[Region | None, float | None, tuple[str, ...]]:
    region = candidate.proposed
    panels = {p.panel_id: (i, p) for i, p in enumerate(job.panels)}
    if region.panel_id not in panels:
        return None, None, ("INVALID_REGION",)
    index, panel = panels[region.panel_id]
    if (region.page_index != index or region.panel_sha256 != panel.original_sha256
            or region.transform_sha256 != panel.transform_sha256
            or (region.source_width, region.source_height) != (panel.width, panel.height)
            or region.box.x1 > panel.width or region.box.y1 > panel.height):
        return None, None, ("INVALID_REGION",)
    ocr = next((o for o in job.ocr if o.panel_id == panel.panel_id), None)
    if ocr is None or ocr.status != "ok":
        return None, None, ("OCR_FAILURE",)
    words = {w.word_id: w for w in ocr.words}
    ids = region.word_ids
    if len(set(ids)) != len(ids) or any(i not in words for i in ids):
        return None, None, ("INVALID_REGION",)
    word_positions = {w.word_id: i for i, w in enumerate(ocr.words)}
    positions = [word_positions[wid] for wid in ids]
    if positions != list(range(positions[0], positions[0] + len(positions))):
        return None, None, ("UNSUPPORTED_TEXT",)
    selected = [words[i] for i in ids]
    target = normalize(candidate.value, rule.normalization)
    if normalize(" ".join(w.text for w in selected), rule.normalization) != target:
        return None, None, ("UNSUPPORTED_TEXT",)
    # Search every panel: do not resolve repeated eligible occurrences by proximity.
    occurrences = 0
    span_len = len(selected)
    for other in job.ocr:
        if other.status != "ok":
            return None, None, ("OCR_FAILURE",)
        normalized_words = [normalize(w.text, rule.normalization) for w in other.words]
        target_words = target.split()
        for start in range(len(other.words) - span_len + 1):
            occurrences += normalized_words[start:start + span_len] == target_words
    if len(job.ocr) != len(job.panels):
        return None, None, ("OCR_FAILURE",)
    if occurrences != 1:
        return None, None, ("AMBIGUOUS_LOCATION",)
    for word in selected:
        b, p = word.box, region.box
        x_fraction = max(0, min(b.x1, p.x1) - max(b.x0, p.x0)) / (b.x1 - b.x0)
        y_fraction = max(0, min(b.y1, p.y1) - max(b.y0, p.y0)) / (b.y1 - b.y0)
        if x_fraction * y_fraction < .9:
            return None, None, ("INVALID_REGION",)
    tight = Box(x0=min(w.box.x0 for w in selected), y0=min(w.box.y0 for w in selected),
                x1=max(w.box.x1 for w in selected), y1=max(w.box.y1 for w in selected))
    if region.box.area > 4 * tight.area:
        return None, None, ("INVALID_REGION",)
    final = region.model_copy(update={"box": tight})
    reasons = ocr.hard_quality_reasons
    if ocr.contrast_quality is None or ocr.sharpness_quality is None:
        return final, None, (*reasons, "POOR_IMAGE_UNDEFINED")
    score = min(sum(w.confidence for w in selected) / (100 * len(selected)),
                ocr.contrast_quality, ocr.sharpness_quality)
    return final, score, reasons


def predicate(job: Job, rule: RuleRef, value: str) -> bool | None:
    """None means policy incomplete/ambiguous; never a negative determination."""
    check = rule.check_id
    if check in ("W-TEXT", "W-HEAD"):
        if rule.normalization != "whitespace" or not rule.expected_text:
            return None
        return normalize(value, "whitespace") == normalize(rule.expected_text, "whitespace")
    if check in ("B-MATCH", "C-MATCH"):
        required_mode = "nfc_case_whitespace" if check == "B-MATCH" else "case_whitespace"
        if rule.normalization != required_mode:
            return None
        intended = (job.application.intended_label_brand if check == "B-MATCH"
                    else job.application.intended_label_class_type)
        return normalize(value, required_mode) == normalize(intended, required_mode)
    if not rule.numeric_forms or rule.normalization != "whitespace":
        return None
    try:
        text = normalize(value, "whitespace")
        parsed = []
        for form in rule.numeric_forms:
            if not text.startswith(form.prefix) or not text.endswith(form.suffix):
                continue
            end = len(text) - len(form.suffix) if form.suffix else len(text)
            raw = text[len(form.prefix):end]
            if len(raw) <= 64 and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", raw):
                parsed.append((Decimal(raw), form.unit))
        if not parsed:
            # A-FORMAT can report a supported malformed statement; other numeric
            # checks cannot infer a mismatch when parsing failed.
            return False if check == "A-FORMAT" else None
        if len(set(parsed)) != 1:
            return None
        number, unit = parsed[0]
        if check == "A-FORMAT":
            return 0 <= number <= 100 if unit == "percent" else None
        if check == "A-MATCH":
            return number == job.application.intended_label_alcohol_percent if unit == "percent" else None
        if unit not in ("mL", "L") or number <= 0:
            return None
        # Decimal tuple construction shifts the exponent exactly without using
        # ambient arithmetic precision (multiplication could round a mismatch).
        sign, digits, exponent = number.as_tuple()
        millilitres = Decimal((sign, digits, exponent + 3)) if unit == "L" else number
        return millilitres == job.application.intended_label_net_ml
    except InvalidOperation:
        return None


def assess(job: Job) -> Report:
    rules = {r.check_id: r for r in job.rules}
    all_rules_ready = set(rules) == set(CHECKS) and all(admitted(r) for r in rules.values())
    findings = []
    for check in CHECKS:
        rule = rules.get(check)
        reasons: list[str] = []
        if job.admission != "admitted":
            reasons.append("ADMISSION_PENDING")
        if not all_rules_ready:
            reasons.append("RULE_UNRATIFIED")
        candidates = [c for c in job.candidates if c.check_id == check]
        if not candidates:
            reasons.append("MISSING_EVIDENCE")
        elif len(candidates) != 1:
            reasons.append("AMBIGUOUS_LOCATION")
        candidate = candidates[0] if len(candidates) == 1 else None
        evidence = score = normalized = None
        decision = None
        if candidate and rule and not reasons:
            evidence, score, support_reasons = supported(job, candidate, rule)
            reasons.extend(support_reasons)
            normalized = normalize(candidate.value, rule.normalization)
            if not reasons:
                decision = predicate(job, rule, candidate.value)
                if decision is None:
                    reasons.append("RULE_POLICY_REVIEW")
                if score is None or score < job.threshold:
                    reasons.append("BELOW_THRESHOLD")
        verdict = "needs_reviewer" if reasons or decision is None else ("supports" if decision else "does_not_support")
        findings.append(Finding(check_id=check, verdict=verdict,
                                observed=candidate.value if candidate else None, normalized=normalized,
                                rule=rule, proposed=candidate.proposed if candidate else None,
                                candidate_provenance=candidate.provenance if candidate else None,
                                evidence=evidence, score=score, reasons=tuple(dict.fromkeys(reasons))))
    receipt = tuple(SearchReceipt(panel_id=p.panel_id, panel_sha256=p.original_sha256,
                     recognition_status=next((o.status for o in job.ocr if o.panel_id == p.panel_id), "missing"),
                     word_count=next((len(o.words) for o in job.ocr if o.panel_id == p.panel_id), 0)) for p in job.panels)
    return Report(job_sha256=hashlib.sha256(job.model_dump_json().encode()).hexdigest(),
                  pins=job.pins, source=job, findings=tuple(findings), search_receipt=receipt)
