"""Strict real transport and synthetic authored demo contracts; runtime unverified."""
import hashlib
import math
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Check = Literal["W-TEXT", "W-HEAD", "A-FORMAT", "A-MATCH", "N-MATCH", "B-MATCH", "C-MATCH"]
CHECKS: tuple[Check, ...] = ("W-TEXT", "W-HEAD", "A-FORMAT", "A-MATCH", "N-MATCH", "B-MATCH", "C-MATCH")
Verdict = Literal["supports", "does_not_support", "needs_reviewer"]
Unit = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
BANNER = "Evidence review only. Not a label approval or agency determination."
UNASSESSED = (
    "bold weight", "physical type size", "characters per inch", "same field of vision",
    "legal warning separation/continuity", "bottler/importer", "origin", "5.63(c) disclosures",
    "specialty/import exceptions", "nutrition/allergens", "legal legibility/contrast",
)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)


class Box(Contract):
    x0: float
    y0: float
    x1: float
    y1: float

    @model_validator(mode="after")
    def ordered(self):
        if not (0 <= self.x0 < self.x1 and 0 <= self.y0 < self.y1):
            raise ValueError("expected positive half-open box")
        if self.x1 - self.x0 < 1e-6 or self.y1 - self.y0 < 1e-6:
            raise ValueError("box sides below supported original-pixel precision")
        if self.area <= 0 or not math.isfinite(self.area):
            raise ValueError("box area must be representable, positive and finite")
        return self

    @property
    def area(self) -> float:
        return (self.x1 - self.x0) * (self.y1 - self.y0)


class Panel(Contract):
    panel_id: Annotated[str, Field(min_length=1, max_length=80)]
    original_sha256: Digest
    transform_sha256: Digest
    width: Annotated[int, Field(gt=0)]
    height: Annotated[int, Field(gt=0)]
    byte_length: Annotated[int, Field(gt=0, le=10 * 1024 * 1024)]
    media_type: Literal["image/png", "image/jpeg"]
    complete: Literal[True]
    orientation_applied: Literal[True]
    static_image: Literal[True]

    @model_validator(mode="after")
    def pixels(self):
        if self.width * self.height > 20_000_000:
            raise ValueError("panel decoded pixel cap exceeded")
        return self


class Application(Contract):
    intended_label_brand: Annotated[str, Field(min_length=1, max_length=500)]
    intended_label_class_type: Annotated[str, Field(min_length=1, max_length=500)]
    intended_label_alcohol_percent: Annotated[Decimal, Field(ge=0, le=100, max_digits=20, decimal_places=8)]
    intended_label_net_ml: Annotated[Decimal, Field(gt=0, max_digits=20, decimal_places=8)]
    domain: Literal["fictional_domestic_plain_distilled_spirits"]
    complete_flat_front_back: Literal[True]


class Word(Contract):
    word_id: Annotated[str, Field(min_length=1)]
    text: Annotated[str, Field(min_length=1, max_length=1000, pattern=r"^\S+$")]
    box: Box
    confidence: Annotated[float, Field(ge=0, le=100)]

    @model_validator(mode="after")
    def canonical_token(self):
        # Match Python split() semantics exactly, including U+001C-U+001F
        # which the transport regex engine may classify differently.
        if any(char.isspace() for char in self.text):
            raise ValueError("OCR word must contain exactly one whitespace-free token")
        return self


class OCRResult(Contract):
    panel_id: str
    words: Annotated[tuple[Word, ...], Field(max_length=10_000)]
    status: Literal["ok", "failed", "timeout"]
    engine_sha256: Digest
    traineddata_sha256: Digest
    # Already normalized construction-frozen quality measures, never probabilities.
    contrast_quality: Unit | None
    sharpness_quality: Unit | None
    hard_quality_reasons: tuple[Literal["POOR_IMAGE_BLUR", "POOR_IMAGE_CONTRAST", "HIGHLIGHT_OVER_EVIDENCE", "LOW_PIXEL_DENSITY", "SKEW"], ...] = ()


class Region(Contract):
    panel_id: str
    panel_sha256: Digest
    transform_sha256: Digest
    page_index: Annotated[int, Field(ge=0, le=1)]
    source_width: int
    source_height: int
    box: Box
    word_ids: Annotated[tuple[str, ...], Field(min_length=1, max_length=256)]


class Candidate(Contract):
    check_id: Check
    value: Annotated[str, Field(min_length=1, max_length=20_000)]
    proposed: Region
    provenance: Literal["code", "model_claimed"]


class NumericForm(Contract):
    """Literal affixes around an ASCII decimal; authority is bound separately."""
    prefix: Annotated[str, Field(max_length=80)]
    suffix: Annotated[str, Field(max_length=80)]
    unit: Literal["percent", "mL", "L"]


class RuleRef(Contract):
    check_id: Check
    version: str
    source_sha256: Digest
    predicate_sha256: Digest
    interpretation_sha256: Digest
    citation: str
    as_of: str
    final_text_checked: bool
    reader_ids: tuple[str, str]
    human_ratifier: str | None
    ratified: bool = False
    normalization: Literal["whitespace", "nfc_case_whitespace", "case_whitespace"]
    numeric_forms: Annotated[tuple[NumericForm, ...], Field(max_length=20)] = ()
    expected_text: str | None = None
    split_warning_policy: Literal["review"] = "review"


class Pins(Contract):
    code_sha256: Digest
    config_sha256: Digest
    quality_transforms_sha256: Digest
    method_sha256: Digest


class Job(Contract):
    application: Application
    panels: Annotated[tuple[Panel, ...], Field(min_length=1, max_length=2)]
    ocr: Annotated[tuple[OCRResult, ...], Field(max_length=2)]
    candidates: Annotated[tuple[Candidate, ...], Field(max_length=70)]
    rules: Annotated[tuple[RuleRef, ...], Field(max_length=7)]
    pins: Pins
    threshold: Annotated[float, Field(ge=0, le=1.01, allow_inf_nan=False)]
    admission: Literal["pending", "admitted"] = "pending"

    @model_validator(mode="after")
    def unique(self):
        for values in ([p.panel_id for p in self.panels], [o.panel_id for o in self.ocr], [r.check_id for r in self.rules]):
            if len(set(values)) != len(values):
                raise ValueError("duplicate identity")
        if sum(p.width * p.height for p in self.panels) > 40_000_000:
            raise ValueError("total pixel cap exceeded")
        panel_ids = {p.panel_id for p in self.panels}
        if any(o.panel_id not in panel_ids for o in self.ocr):
            raise ValueError("unknown OCR panel")
        for o in self.ocr:
            if len({w.word_id for w in o.words}) != len(o.words):
                raise ValueError("duplicate OCR word identity")
            p = next(p for p in self.panels if p.panel_id == o.panel_id)
            if any(w.box.x1 > p.width or w.box.y1 > p.height for w in o.words):
                raise ValueError("OCR word outside panel")
        return self


class Finding(Contract):
    check_id: Check
    verdict: Verdict
    observed: str | None = None
    normalized: str | None = None
    rule: RuleRef | None = None
    proposed: Region | None = None
    candidate_provenance: Literal["code", "model_claimed"] | None = None
    evidence: Region | None = None
    reasons: tuple[str, ...]
    score: Unit | None = None
    assessment_scope: Literal["image_evidence_only"] = "image_evidence_only"


class SearchReceipt(Contract):
    panel_id: str
    panel_sha256: Digest
    recognition_status: Literal["ok", "failed", "timeout", "missing"]
    word_count: Annotated[int, Field(ge=0, le=10_000)]
    search_policy: Literal["present-only-v1; tiled absence search not implemented"] = "present-only-v1; tiled absence search not implemented"


class Report(Contract):
    kind: Literal["real_evidence_report"] = "real_evidence_report"
    banner: Literal["Evidence review only. Not a label approval or agency determination."] = BANNER
    unassessed_scope: tuple[str, ...] = UNASSESSED
    runtime_status: Literal["unverified_source_milestone"] = "unverified_source_milestone"
    job_sha256: Digest
    pins: Pins
    source: Job
    findings: tuple[Finding, ...]
    # This is a search observation, never a span or a verified absence claim.
    search_receipt: tuple[SearchReceipt, ...]

    @model_validator(mode="after")
    def complete_record(self):
        if self.unassessed_scope != UNASSESSED:
            raise ValueError("unassessed scope must be retained")
        if tuple(f.check_id for f in self.findings) != CHECKS:
            raise ValueError("all seven ordered findings required")
        if self.pins != self.source.pins:
            raise ValueError("source pins mismatch")
        if self.job_sha256 != hashlib.sha256(self.source.model_dump_json().encode()).hexdigest():
            raise ValueError("source digest mismatch")
        return self


DEMO_BANNER = (
    "Synthetic demo: original generated artwork and authored observations; fictional assumptions. "
    "Not legal approval or OCR accuracy. Runtime unverified."
)


class DemoContext(Contract):
    scenario_id: Literal["DEMO-01", "DEMO-02", "DEMO-03"]
    assumption_pack_sha256: Digest
    manifest_sha256: Digest
    scope: Literal["demo_only"] = "demo_only"
    observation_provenance: Literal["synthetic_authored"] = "synthetic_authored"
    legal_sources: Literal["not_acquired"] = "not_acquired"
    legal_validity: Literal["not_assessed"] = "not_assessed"
    authority: Literal["delegated_not_personally_signed_by_owner"] = "delegated_not_personally_signed_by_owner"
    notice_layout: Literal["unsplit", "split_or_ambiguous"] = "unsplit"


class DemoObservation(Contract):
    """Authored values/geometry/quality, never measurements from an OCR engine."""
    panel_id: str
    words: Annotated[tuple[Word, ...], Field(max_length=10_000)]
    status: Literal["ok", "failed", "timeout"]
    contrast_quality: Unit | None
    sharpness_quality: Unit | None
    hard_quality_reasons: tuple[Literal["POOR_IMAGE_BLUR", "POOR_IMAGE_CONTRAST", "HIGHLIGHT_OVER_EVIDENCE", "LOW_PIXEL_DENSITY", "SKEW"], ...] = ()


class DemoCandidate(Contract):
    check_id: Check
    value: Annotated[str, Field(min_length=1, max_length=20_000)]
    proposed: Region
    provenance: Literal["synthetic_authored"]


class DemoPolicyRef(Contract):
    """Fictional assumptions; deliberately has no human/legal ratification fields."""
    check_id: Check
    version: Literal["demo-assumptions-v1"] = "demo-assumptions-v1"
    assumption_pack_sha256: Digest
    scope: Literal["fictional_demo_assumption"] = "fictional_demo_assumption"
    normalization: Literal["whitespace", "nfc_case_whitespace", "case_whitespace"]
    numeric_forms: Annotated[tuple[NumericForm, ...], Field(max_length=20)] = ()
    expected_text: str | None = None
    split_warning_policy: Literal["review"] = "review"


class DemoJob(Contract):
    kind: Literal["synthetic_demo_job"] = "synthetic_demo_job"
    context: DemoContext
    application: Application
    panels: Annotated[tuple[Panel, ...], Field(min_length=1, max_length=2)]
    observations: Annotated[tuple[DemoObservation, ...], Field(max_length=2)]
    candidates: Annotated[tuple[DemoCandidate, ...], Field(max_length=70)]
    pins: Pins
    threshold: Annotated[float, Field(ge=0.5, le=0.5, allow_inf_nan=False)] = 0.5

    @model_validator(mode="after")
    def valid_observations(self):
        panel_ids = [p.panel_id for p in self.panels]
        observation_ids = [o.panel_id for o in self.observations]
        if len(set(panel_ids)) != len(panel_ids) or len(set(observation_ids)) != len(observation_ids):
            raise ValueError("duplicate demo panel/observation identity")
        if sum(p.width * p.height for p in self.panels) > 40_000_000:
            raise ValueError("total pixel cap exceeded")
        panels = {p.panel_id: p for p in self.panels}
        for observation in self.observations:
            if observation.panel_id not in panels:
                raise ValueError("unknown authored-observation panel")
            if len({w.word_id for w in observation.words}) != len(observation.words):
                raise ValueError("duplicate authored word identity")
            panel = panels[observation.panel_id]
            if any(w.box.x1 > panel.width or w.box.y1 > panel.height for w in observation.words):
                raise ValueError("authored word outside panel")
        return self


class DemoFinding(Contract):
    check_id: Check
    verdict: Verdict
    observed: str | None = None
    normalized: str | None = None
    policy: DemoPolicyRef
    proposed: Region | None = None
    candidate_provenance: Literal["synthetic_authored"] | None = None
    evidence: Region | None = None
    reasons: tuple[str, ...]
    score: Unit | None = None
    assessment_scope: Literal["synthetic_authored_evidence_only"] = "synthetic_authored_evidence_only"


class DemoSearchReceipt(Contract):
    panel_id: str
    panel_sha256: Digest
    recognition_status: Literal["ok", "failed", "timeout", "missing"]
    word_count: Annotated[int, Field(ge=0, le=10_000)]
    observation_provenance: Literal["synthetic_authored"] = "synthetic_authored"
    search_policy: Literal["present-only-v1; no measured OCR or verified absence"] = "present-only-v1; no measured OCR or verified absence"


class DemoReport(Contract):
    kind: Literal["synthetic_demo_report"] = "synthetic_demo_report"
    banner: Literal["Evidence review only. Not a label approval or agency determination."] = BANNER
    demo_banner: Literal["Synthetic demo: original generated artwork and authored observations; fictional assumptions. Not legal approval or OCR accuracy. Runtime unverified."] = DEMO_BANNER
    unassessed_scope: tuple[str, ...] = UNASSESSED
    runtime_status: Literal["unverified_source_milestone"] = "unverified_source_milestone"
    job_sha256: Digest
    pins: Pins
    source: DemoJob
    findings: tuple[DemoFinding, ...]
    search_receipt: tuple[DemoSearchReceipt, ...]

    @model_validator(mode="after")
    def complete_demo_record(self):
        if self.unassessed_scope != UNASSESSED:
            raise ValueError("unassessed scope must be retained")
        if tuple(f.check_id for f in self.findings) != CHECKS:
            raise ValueError("all seven ordered demo findings required")
        if self.pins != self.source.pins:
            raise ValueError("demo source pins mismatch")
        if self.job_sha256 != hashlib.sha256(self.source.model_dump_json().encode()).hexdigest():
            raise ValueError("demo source digest mismatch")
        for finding in self.findings:
            if (finding.policy.check_id != finding.check_id
                    or finding.policy.assumption_pack_sha256 != self.source.context.assumption_pack_sha256):
                raise ValueError("demo policy binding mismatch")
        return self
