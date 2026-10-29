"""Fictional demo assumptions and authored observations, not legal/OCR accuracy.

Pure source construction; runtime unverified. Decisions are delegated, not
personally signed by the owner. No legal RuleRef or admission flags are created.
"""
import hashlib
import json

from .contracts import CHECKS, DemoJob, DemoPolicyRef

# These exact original bytes define software assumptions, not statutory text.
# The hash is calculated from the canonical local pack, never a fabricated pin.
DEMO_POLICY_BYTES = json.dumps({
    "version": "demo-assumptions-v1",
    "scope": "demo_only",
    "legal_sources": "not_acquired",
    "legal_validity": "not_assessed",
    "authority": "delegated_not_personally_signed_by_owner",
    "observation_provenance": "synthetic_authored",
    "runtime_status": "unverified_source_milestone",
    "threshold": 0.5,
    "threshold_basis": "fixed_demo_value_not_calibrated_or_probabilistic",
    "missing_evidence_policy": "review",
    "split_warning_policy": "review",
    "checks": [
        {"check_id": "W-TEXT", "normalization": "whitespace",
         "expected_text": "DEMO NOTICE: FICTIONAL ARTWORK. REVIEW EVIDENCE ONLY."},
        {"check_id": "W-HEAD", "normalization": "whitespace", "expected_text": "DEMO NOTICE:"},
        {"check_id": "A-FORMAT", "normalization": "whitespace", "numeric_forms": [
            {"prefix": "", "suffix": " percent", "unit": "percent"}]},
        {"check_id": "A-MATCH", "normalization": "whitespace", "numeric_forms": [
            {"prefix": "", "suffix": " percent", "unit": "percent"}]},
        {"check_id": "N-MATCH", "normalization": "whitespace", "numeric_forms": [
            {"prefix": "", "suffix": " mL", "unit": "mL"},
            {"prefix": "", "suffix": " L", "unit": "L"}]},
        {"check_id": "B-MATCH", "normalization": "nfc_case_whitespace"},
        {"check_id": "C-MATCH", "normalization": "case_whitespace"},
    ],
}, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
DEMO_POLICY_SHA256 = hashlib.sha256(DEMO_POLICY_BYTES).hexdigest()


def demo_policies() -> tuple[DemoPolicyRef, ...]:
    """Fresh frozen fictional references; no ratifier, readers or real sources."""
    pack = json.loads(DEMO_POLICY_BYTES)
    policies = tuple(DemoPolicyRef.model_validate_json(json.dumps({
        **record, "assumption_pack_sha256": DEMO_POLICY_SHA256,
    }, allow_nan=False)) for record in pack["checks"])
    if tuple(policy.check_id for policy in policies) != CHECKS:
        raise ValueError("incomplete fictional assumption pack")
    return policies


def demo_job_from_payload(payload: dict) -> DemoJob:
    """Normalize JSON-shaped authored input; do not consume any expected outcomes.

Only the omitted pack digest is filled, from these actual authored bytes. The
manifest digest, code/config pins and panel hashes must be supplied by the caller
from its real local artifacts. Digests bind reproducibility, not authenticity.
"""
    if not isinstance(payload, dict):
        raise ValueError("expected a demo payload object")
    document = dict(payload)
    raw_context = document.get("context")
    if not isinstance(raw_context, dict):
        raise ValueError("expected explicit demo context")
    document["context"] = dict(raw_context)
    document["context"].setdefault("assumption_pack_sha256", DEMO_POLICY_SHA256)
    job = DemoJob.model_validate_json(json.dumps(document, allow_nan=False))
    if job.context.assumption_pack_sha256 != DEMO_POLICY_SHA256:
        raise ValueError("fictional assumption pack digest mismatch")
    return job
