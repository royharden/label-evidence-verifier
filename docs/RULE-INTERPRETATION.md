# Rule interpretation and ratification forms

**PENDING - needs Roy. All seven checks are unratified.** This document contains
questionnaires, not law, adopted grammar, source text, expected verdicts or gold.
Trace: PLAN-M16-v1 sections 2-4, 7/P1 and 7/P3. Citations below are acquisition
targets from the frozen plan; their currency and meaning have not been verified.

## Source record (complete separately for each check)

| Field | Value |
|---|---|
| Check ID / RuleRef version | |
| Primary citation and exact source edition / section | |
| GovInfo final-text location or manually acquired eCFR location | |
| Exact retained source-byte artifact and SHA256 | |
| Retrieval date/time / as-of date | |
| Final-text status evidence / checker / date | |
| Amendment search scope/date, effective dates, evidence and unresolved changes | |
| Applicability/domain and exceptions excluded | |
| Proposed finite predicate/version/hash (only after blind responses) | |
| Allowed normalization and prohibited transformations | |
| Interpretation artifact/version/SHA256 | |
| Reader A/B identities, model families and response artifact hashes | |
| Human adjudicator appointment / identity / dated ratification | |

Pin official primary final text; mirrors or failed website access do not satisfy
admission. Pending proposals are not final rules. Do not fetch rules during evaluation.
Bind identical source bundles for both readers by digest; no acquisition is performed here.

## Blind-reader protocol

An operator appoints fresh A/B readers of different model families and records their
identities and eligibility. Each reads the identical pinned text independently,
before seeing predicates, product predictions or the other response. Keep answers
separate until both are sealed with artifact digests and completion times. Neither
two-model agreement nor a builder review substitutes for human adjudication.

Each reader completes the common questionnaire **for every row below**:
applicability and exclusions; finite interpretation in their own words; exact allowed
normalization; proof-only handling; application equality versus liquid tolerance;
metric forms/conversions; punctuation, case and glyph distinctions; definition of
absence; split-warning ambiguity; boundary examples and unresolved questions.
For irrelevant topics write a reasoned N/A for human review, not a silent omission.
These are questions, not builder-authored answers or adopted boundary cases.

| Check / kind | Planned finite boundary to interrogate | Specific questions for both readers |
|---|---|---|
| W-TEXT / regulation_text | Exact warning wording/punctuation; 27 CFR 16.21 target; whitespace/line-wrap normalization only | What exact final bytes apply? How do wrap, hyphenation, punctuation, case and digits affect matching? Which uncertainty requires review? |
| W-HEAD / regulation_text | Heading capitals; 16.22(a)(2) target; no boldness claim | What capital/case distinctions apply? Can the heading be isolated unambiguously? Which physical/bold attributes remain unassessed? |
| A-FORMAT / regulation_text | Finite alcohol grammar; 5.65(a),(b) targets | Which literal forms, abbreviations and spacing are admitted? Settle proof-only and near misses explicitly; do not assume proof conversion. |
| A-MATCH / application_consistency | Decimal equality to intended_label_alcohol_percent | How is observed ABV parsed and compared exactly? Confirm that liquid-versus-label tolerance under 5.65(c) is never application-match tolerance. |
| N-MATCH / application_consistency | Positive metric parse equals intended_label_net_ml; 5.70(a) informs parse | Which metric forms and L-to-mL conversion are admitted? How are nonmetric-only, zero and ambiguous units handled without fill/size/exemption inference? |
| B-MATCH / application_consistency | Exact intended_label_brand after ratified NFC/case/whitespace policy | Which Unicode/case/whitespace transformations are allowed? Preserve punctuation, accents, quotes and glyph distinctions unless individually ratified. No fuzzy identity. |
| C-MATCH / application_consistency | Exact intended_label_class_type after ratified case/whitespace policy | Which text transformations are allowed? How are ambiguity and mismatch handled without inferring legal class/type identity? |

All seven must clear admission; an uncleared check cannot be dropped to rescue M16.
Missing OCR evidence always requires default review, not a visual-absence conclusion.
Any experimental absence policy needs separate explicit finite ratification/calibration;
this form does not enable it. Split-warning policy ambiguity routes to needs_reviewer,
never a statutory-continuity determination.

## Response, boundary and human adjudication forms

Duplicate this unfilled block for each check and each reader A/B; no sample answers
or substantive expected verdicts have been supplied by builders.

| Response field | Value |
|---|---|
| Check / reader / source bundle hash / start and sealed times | |
| Applicability, normalization, proof, tolerance, metric, glyph/case/punctuation answers | |
| Absence and split-warning answers; unknowns / reasoned N/A | |
| Boundary example ID / proposed input / cited source / rationale | |
| Proposed outcome / evidence requirement / ambiguity escalation | |
| Response artifact path / SHA256 | |

Boundary slots per check (empty): ordinary form; edge/near miss; punctuation/case/digit
or unit/glyph variant; absent/ambiguous observation; out-of-scope form. Readers and
the appointed human fill applicable examples; builders do not manufacture oracle data.

| Human resolution field (repeat for all seven) | Value |
|---|---|
| Check / A response hash / B response hash | |
| Agreements / every disagreement / unknown requiring resolution | |
| Human decision and source-grounded rationale, including boundary decisions | |
| Final finite interpretation and allowed transformations / version / SHA256 | |
| Final boundary records / predicate revision binding | |
| Ratify / request revision / decline; human identity and appointment reference | |
| Written dated attestation binding exact source and interpretation artifacts | |

Preserve original responses. Roy or the named human adjudicator resolves every
disagreement and ratifies every check; do not prefill a signature. Unsettled policies
remain pending; interpretation failure yields SKIP_M16. Changed source, interpretation,
asset or config reopens affected admission (see DATA-ADMISSION.md). A rule flag/hash in
the existing foundation is documentary input, not authentication or ratification.

Unassessed scope includes bold weight, physical type size, characters per inch, same
field of vision, statutory warning separation/continuity, bottler/importer, origin,
5.63(c) disclosures, specialty/import exceptions, nutrition/allergens and legal
legibility/contrast. No form expands the fictional domestic plain-spirits domain.
