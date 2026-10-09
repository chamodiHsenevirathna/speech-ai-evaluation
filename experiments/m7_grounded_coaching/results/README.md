> **Not included in this repository.** The example outputs this page describes
> (`approach_a_generic.json`, `approach_b_structured.json`, `approach_c_technique_library.json`
> and `summary.md`) are withheld. They are hand-written design illustrations, scored by their
> own author, and will be published only after an independent re-score. The disclosure below
> explains why they must not be read as model results.

# M7A Results — Illustrative Approach Comparison

**Read `../README.md`'s "Important limitation" section before using anything in this
directory.** These are not Gemini/Ollama outputs. No live model call was made — no
API key or local model was available in this environment. Every output file below is
an **illustrative, hand-authored design example** — written directly by Claude (the
agent performing this design milestone), following each approach's prompt contract as
faithfully as an LLM plausibly would. **None of this is model-generated experimental
evidence.**

The rubric scores attached to each output (`rubric_self_score` in the JSON files) are
**rubric sanity checks, not independent model-quality evidence.** They were assigned by
the same agent that wrote the outputs being scored — a setup documented as biased in
the literature (see `../research_review.md` B4, "Self-Preference Bias in Rubric-Based
Evaluation of Large Language Models," arXiv 2604.06996: LLM judges score their own
output more favorably than an independent judge would). Treat every score in this
directory as **subject to self-preference/evaluator bias** until an independent
re-scoring pass (a different session/agent or a human, with no authorship stake in the
outputs) is run.

## What this evidence is useful for

Comparing **prompt/contract design** — does requiring structured evidence citations
(Approach B) and a constrained technique library (Approach C) visibly change output
quality versus an unconstrained instruction (Approach A), when the same underlying
capability (an LLM instructed to write coaching) is asked to follow each contract.

## What this evidence is NOT

- Not a benchmark of Gemini's actual output quality, latency, or cost.
- Not evidence of consistency across repeated runs (EXP-M7-004, deferred).
- Not a blind third-party evaluation — the same agent authored the outputs and scored
  them, which is a conflict of interest for objectivity. Treat scores as a rough
  self-check that the contracts behave as designed, not as a validated quality claim.
- Not run against all 16 cases — a representative subset of 6 was used (see below) to
  keep this illustration proportionate; the full 16-case set is intended for the real
  model comparison once API access exists (see `../conclusions.md` "Decisions
  deferred").

## Case subset used (6 of 16)

Chosen to cover the highest-stakes design questions:

- **CASE-01** (strong structure) — does the coach avoid inventing a problem where the
  attempt is genuinely good?
- **CASE-06** (long pauses) — does the coach avoid the TECH-001 contradiction (see
  `../failure_taxonomy.md`)?
- **CASE-10** (fragmented thought) — does the coach hedge appropriately about imperfect
  STT rather than stating restarts as fact?
- **CASE-13** (near-silence) — does the coach abstain?
- **CASE-15** (single filler only) — does the coach avoid overreacting to one
  experimental detection?
- **CASE-16** (real-human scripted) — how does each approach perform on evidence that
  is not synthetic-fixture-clean?

## Files

- `approach_a_generic.json` — Approach A (generic instruction) outputs.
- `approach_b_structured.json` — Approach B (evidence-grounded structured) outputs.
- `approach_c_technique_library.json` — Approach C (structured + curated technique
  library) outputs.
- `summary.md` — side-by-side comparison, rubric scores, and the qualitative pattern
  observed across cases.
