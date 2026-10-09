# M7A — Grounded Coaching Design & Evaluation

**Status: design and evaluation milestone. No production coaching code exists as a
result of this document.** Nothing here is wired into `backend/` or `frontend/`. No
Gemini call was made, from the app or otherwise. This mirrors M6A's role for speech
metrics: evidence and design work that later milestones (M7B+) implement from.


> **Note on the comparison.** The per-approach example outputs and their scores are withheld from
> this repository. Wherever `conclusions.md` or `experiment_plan.md` says how the approaches
> compared (for example that "Approach C" looked strongest), that refers to those hand-written,
> author-scored illustrations. It is a design sketch, **not a measured result**, and no model was run.

## Scope

Design and evaluate what a useful SpeakLab coach should do, given the deterministic
evidence already available after M6B: prompt, transcript, duration, word count,
approximate WPM, approximate pause evidence, experimental filler evidence.

Explicitly out of scope for M7A (see the task brief this milestone was scoped from):
production coaching implementation, calling Gemini from the app, frontend/backend
production behavior changes, retry comparison, Stuck Map, new practice modes.

## Important limitation, stated up front

**No live LLM comparison was run in this milestone.** This environment has no
`GEMINI_API_KEY` configured (`.env` does not exist, only `.env.example` with a blank
placeholder — consistent with `docs/ai-boundaries.md`) and no local Ollama installation
(`which ollama` found nothing). Per the project's explicit research-integrity rule (`docs/methodology.md`) — "Do not fabricate
metrics, benchmark numbers, or test results" — this document does **not** invent
Gemini/Ollama output or pretend a comparison ran that didn't.

Instead, `results/` (withheld from this repository) holds **illustrative outputs authored directly by Claude (the
agent doing this design work), clearly labeled as such** — not a Gemini API call, not
an Ollama call, not a benchmark. These illustrate what each *approach's prompt
contract* structurally produces (grounding discipline, one-improvement selection,
technique-library adherence, abstention behavior) when a capable LLM follows the
instructions faithfully. They are useful for evaluating **prompt/contract design**, but
they are **not evidence of Gemini's specific output quality, latency, or cost** — that
requires a real API-key-backed run, deferred to M7B/M8 (see `conclusions.md`
"Decisions deferred").

## Contents

- `experiment_plan.md` — EXP-M7-001 through EXP-M7-005 (hypothesis → experiment →
  result → decision), including which experiments could and could not actually run.
- `technique_library.md` — the curated TECH-001–008 coaching-technique library.
- `evaluation_rubric.md` — the 8-dimension, 0–3 scoring rubric.
- `failure_taxonomy.md` — "Ways the Coach Could Embarrass Us in Public."
- `cases/` — 16 synthetic/fixture evaluation cases (text only, no audio, no private
  human data — one case reuses the already-committed, already-public scripted sample
  from `experiments/m6_speech_metrics/real_human_validation_results.md` Test B, labeled
  as such).
- `results/` — per-approach illustrative outputs against a representative subset of
  cases, plus rubric self-scoring. **Not included in this repository**; see `results/README.md`.
- `conclusions.md` — the full M7A final report (all 23 items from the task brief).
- `research_review.md` — categorized literature survey (A/B/C/D) of real, web-verified
  papers relevant to grounded coaching, rubric-based evaluation, and future
  articulation work — includes a correction retracting an earlier, unjustified set of
  numeric experiment thresholds. Read this alongside `conclusions.md`'s Limitations
  and `experiment_plan.md`'s EXP-M7-004, both of which it amends in place.

## Relationship to M6

This design assumes M6B's shipped evidence contract exactly as implemented — see
`docs/context.md` "API Contract" (`MetricsResult`/`TranscriptionResult`) and
`docs/context.md` (`SpeechMetrics`, `PauseEvent`, `FillerOccurrence`). No new
metric is invented here; M7A only defines how an LLM may interpret metrics that already
exist, at the reliability tier each already carries (`docs/decision-log.md`
DEC-014/DEC-015).
