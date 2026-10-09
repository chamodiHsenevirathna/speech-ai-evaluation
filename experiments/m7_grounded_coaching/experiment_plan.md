# M7A Experiment Plan

Hypothesis → Experiment → Result → Decision, matching the pattern already used in
`experiments/m5_transcription/` and `experiments/m6_speech_metrics/`
(`docs/methodology.md` "Research-integrity rules"). Every "Result" below states plainly whether it is a real
measurement or an illustrative design exercise — none of the numbers here are presented
as a benchmark of a production model.

---

## EXP-M7-001 — Generic coach baseline

**Status: DESIGNED, NOT RUN.** Illustrative outputs only — see below.

**Hypothesis:** An unconstrained instruction ("give useful speaking feedback" + prompt
+ transcript + metrics) produces feedback with material groundedness, safety, and
prioritization problems — generic advice, invented claims, too many suggestions — even
when the underlying model is capable.

**Experiment (as actually run):** Not run against a live model — no `GEMINI_API_KEY`
or local Ollama installation was available in this environment (see `README.md`).
Instead, Claude authored 6 illustrative Approach-A outputs (`results/
approach_a_generic.json`) against a representative case subset, then self-scored them
against `evaluation_rubric.md`.

**Result:** Illustrative only (not a real model measurement). Across the 6 illustrated
cases: groundedness scored 0 on 3/6 (invented "nervousness" on a strong response,
confabulated an entire narrative on near-silence, mis-cited an observed pause gap as an
almost-exact duration); uncertainty handling scored 0 on 5/6; the model never abstained
even once, including on the near-silent case. See `results/summary.md` for the full
breakdown.

**Decision:** The hypothesis is *consistent with* this illustrative exercise, but not
confirmed by real measurement. **Do not ship Approach A as designed.** A real
Gemini-backed repeat of this experiment is deferred to M7B/M8 (see `conclusions.md`
"Decisions deferred") before this can move from "illustrative" to "measured."

---

## EXP-M7-002 — Evidence-grounded structured coach

**Status: DESIGNED, NOT RUN.** Illustrative outputs only — see below.

**Hypothesis:** Requiring a structured output contract (strength+evidence, main
improvement+evidence, technique, retry goal) with every claim tied to a supplied
evidence field materially reduces groundedness and safety failures versus Approach A,
even without a curated technique library.

**Experiment (as actually run):** Illustrative, same method as EXP-M7-001 —
`results/approach_b_structured.json` against the same 6 cases.

**Result:** Illustrative only. Groundedness and safety scored 3/3 on all 6 cases (zero
zeros, versus 3 and 1 zeros respectively for Approach A). The contract correctly
produced an explicit abstention on the near-silence case (CASE-13) and correctly
declined to escalate a single filler detection into the main improvement (CASE-15).
Residual weakness: prioritization averaged 2.17/3, with one case (CASE-16) citing two
evidence types as "the" main improvement rather than one, since nothing in the contract
forces a single selection.

**Decision:** The structured-output requirement is a clear design improvement over
Approach A on the dimensions this milestone cares most about (groundedness, safety,
uncertainty handling), on this illustrative evidence. Prioritization remains an open
gap that Approach C is designed to close — proceed to EXP-M7-003 rather than treating B
as sufficient on its own.

---

## EXP-M7-003 — Evidence-grounded + technique-library coach

**Status: DESIGNED, NOT RUN.** Illustrative outputs only — see below.

**Hypothesis:** Constraining technique selection to the curated `technique_library.md`
(with explicit per-technique evidence bars and exclusion rules) further improves
prioritization and eliminates specific named contradiction failure modes (e.g.
recommending more pausing to someone who already paused too long) that structure alone
does not guarantee.

**Experiment (as actually run):** Illustrative, same method — `results/
approach_c_technique_library.json` against the same 6 cases.

**Result:** Illustrative only. Matched Approach B everywhere B was already strong (no
new zeros), and specifically improved prioritization (2.17 → 2.83 average) and
retry-goal quality (1.83 → 2.17). CASE-06's technique-exclusion rule (TECH-001 must not
be recommended when pause evidence already exists) mechanically prevented the exact
contradiction named in `failure_taxonomy.md`, rather than merely happening not to
occur. CASE-16's prioritization ambiguity (fillers vs. pauses) was resolved by
TECH-004's explicit "3+ detections" bar, with the reasoning made auditable in the
`technique.reason` field.

**Decision:** This is the **leading architecture hypothesis**, and the candidate for
M7A-2 real-model validation, based on this illustrative comparison (see
`conclusions.md` section 17) — **not an experimentally proven winner.** Consistent with
the task brief's own framing that this is "the likely preferred architecture," this
milestone adds a design-level (not yet measured) reason to favor it. Not confirmed
against a real model; validation deferred to M7A-2, production adoption deferred
further to M7B/M8.

---

## EXP-M7-004 — Consistency across repeated runs (deferred, not run)

**Status: NOT RUN.** Requires real, temperature-controlled repeated model calls — not
attempted, not simulated. When run, must also score groundedness/correctness per run
(see "Correction added post-review" below) so consistency is never treated as quality
on its own.

**Hypothesis:** A structured, technique-library-constrained prompt (Approach C)
produces more consistent output across repeated runs on identical input than an
unconstrained prompt (Approach A), reducing the "inconsistent advice across identical
inputs" failure mode (`failure_taxonomy.md`).

**Experiment:** Not run. This experiment requires calling a real, temperature-
controlled model multiple times on the same input and comparing outputs — Claude
authoring "multiple illustrative runs" of its own single-pass reasoning would not
produce meaningful sampling variance and would risk looking like fabricated evidence of
consistency. Per the project's explicit research-integrity rule (`docs/methodology.md`) against fabricating results, this
experiment is left **not run**, not simulated.

**Result:** None. No claim of consistency (or inconsistency) is made for any approach
in this milestone.

**Decision:** Deferred to whenever real model access exists (M7B/M8). Until then,
consistency remains a hypothesis, not a measured property of any approach.

**Correction added post-review (`research_review.md` B5, "The Consistency Dilemma in
LLMs: Generator-Evaluator Agreement and Vulnerability to Mistakes," arXiv 2606.30653):**
when this experiment does run, inter-run agreement must **not** be treated as a
standalone quality signal. That paper found higher self-consistency correlated with
*increased* vulnerability to confidently-repeated mistakes in its own (clinical)
domain — a model can be perfectly consistent and consistently wrong. Whoever runs
EXP-M7-004 must score each individual repeated run's **Groundedness** dimension
(`evaluation_rubric.md`) independently, in addition to measuring agreement across
runs — never report consistency alone as evidence the coach is reliable.

---

## EXP-M7-005 — Abstention / insufficient-evidence behavior (partially illustrated)

**Status: NOT RUN.** Illustrated via one case (CASE-13) across the three illustrative
approaches — not a live-model run.

**Hypothesis:** An explicit abstention instruction ("if evidence is insufficient, set
`abstained: true` and do not generate strength/improvement/technique") prevents
confabulation on near-empty or corrupted evidence, where an unconstrained prompt tends
to fabricate plausible-sounding feedback anyway.

**Experiment (as actually run):** Illustrated via CASE-13 (near-silence) across all
three approaches, already included in EXP-M7-001/002/003 above and `results/
summary.md`. Not run against a live model.

**Result:** Illustrative only. Approach A confabulated a full narrative on CASE-13's
empty transcript. Approaches B and C both correctly abstained. This is the single
starkest quality delta observed anywhere in this milestone's illustrative comparison.

**Decision:** Abstention must be an explicit, first-class field in the output contract
(`abstained: boolean`, `abstention_reason: string | null`), not an emergent behavior
left to the model's judgment under an unconstrained prompt — see `conclusions.md`
"Abstention policy" for the full trigger-condition list. Confirming this holds under a
real model, and testing the other abstention triggers (corrupted transcript, conflicting
signals, weak experimental-only evidence) beyond near-silence, is deferred to M7B/M8.
