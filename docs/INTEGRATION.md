# OCR-to-report seam

This first milestone implements the **present evidence F1 path** over normalized
records. `Job.model_validate_json` is the strict JSON boundary. Unknown fields,
nonfinite numbers, duplicate identities, invalid boxes and oversized declared
panels are refused. Decimal application numbers are JSON strings. Arrays become
immutable tuples; other unexpected coercions are refused.
Box sides below 0.000001 original pixels are refused; area must be finite and
representable. Containment uses per-axis fractions to avoid area underflow.

An eventual image adapter must independently decode allowlisted static PNG/JPEG,
enforce actual byte/pixel limits, apply EXIF orientation, retain original hashes
and invertible coordinate transforms, strip distributable metadata, and reject
out-of-domain requests. Current panel declarations are **not verification of
image bytes**. No image adapter exists in this milestone.

An eventual OCR adapter supplies ordered Tesseract words (one non-whitespace token
per word), original-coordinate boxes, engine/traineddata hashes, status and
construction-frozen contrast/sharpness scores plus hard quality reasons. Confidence
always comes from cited OCR words, including model-proposed candidates. No measured
confidence can be asserted by a proposer. Undefined quality forces review.
Adapters must enforce the 30-second deadline and 10,000-word cap per panel. Current
contracts enforce the word cap, but do not run or time OCR. A field may cite at
most 256 words; longer fields are refused at the seam.

The operator supplies all seven immutable `RuleRef`s after human ratification,
source and interpretation acquisition. No legal text, legal grammar, approved
rule pack or signatures are bundled. Rule flags and hashes are documentary input
claims; this code cannot authenticate a ratifier or establish legal correctness.
Missing/unratified rules hold **all seven** findings at review. Admission defaults
to pending. Admission must remain pending until the operator verifies the actual
documentary gates; changing its string is not an admission procedure.

Warning predicates require whitespace-only normalization and pinned expected
text. Brand uses NFC/case/whitespace; class/type uses case/whitespace only. Numeric
rules require ratified literal prefix/suffix forms enclosing an ASCII decimal
(at most 64 characters), and exact `unit` (`percent`, `mL` or `L`). No forms are
shipped. Net-content L-to-mL scaling shifts the Decimal exponent exactly without
ambient-context rounding. No proof conversion, fill tolerance,
liquid tolerance or legal class inference is implemented. Literal forms are trusted,
operator-reviewed local configuration, never extracted from an image/model.
Caller-supplied executable regex is forbidden. An incomplete policy forces review.

Candidates are untrusted value/region proposals. A single exact normalized span
must exist across all supplied panels. Word IDs must be ordered and contiguous;
each word must lie at least 90% in the proposed box. Proposals above 4x the tight
supporting union are refused. Original/proposed geometry and final tight region
are preserved. No relocation, fuzzy match or absence verdict is available. Unknown
OCR on any panel prevents the unique-occurrence claim. Every missing field is
`MISSING_EVIDENCE` with a bounded observation receipt, not verified visual absence.

`assess(Job) -> Report` has no I/O. It emits every check, original job, pins, rule
refs, observed/normalized values, proposals, evidence, reasons and empirical score.
Scores are not probabilities; the threshold includes 1.01 for answer-none. The
caller supplies frozen thresholds/transforms; calibration is not implemented.
`render_html(Report) -> str` escapes every data string, includes the required banner
and exclusions, and has no remote resources/scripts. It currently displays region
coordinates; image crops/overlays are deferred. CLI outputs use exclusive creation
to preserve existing records. Machine JSON is immutable by convention and frozen
objects. Report import checks the source hash, pin agreement, fixed exclusions and
all seven ordered findings, then recomputes the source assessment before rendering;
it is not a signed tamper-proof audit store. Reviewer annotations, SQLite
CAS/idempotence, provider/ledger ports, generator and evaluator are later packages.

Later validation must cover punctuation/case/digit mismatches, wrong-panel and
duplicate spans, giant/invalid regions, zero confidence/quality, parse failures,
unratified rules, answer-none thresholds, HTML injection and malformed JSON.
No boundary fixtures, held-out gold or independent evaluations are authored here.
