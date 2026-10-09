# EXP-M6-006 — Timestamp-Aware Filler Heuristic

> **Status: unfinished.** A candidate rule with 12 unit tests on designed, synthetic cases. It has
> **not** been evaluated on any recording, no precision/recall/F1 or other score exists, and it
> is not adopted anywhere.

## EXP-M6-006 IS NOT PRODUCTION CODE.

`candidate.py` is an **experimental, standalone candidate** implementation of
a filler-detection heuristic. It is not wired into the FastAPI backend, not
imported by `backend/app/` anywhere, and not called by anything in
`frontend/`. `backend/app/services/metrics/fillers.py` — the actual
production detector — is unmodified and remains the system of record.

## Purpose

Evaluate whether a deterministic candidate rule (adding pause/segment-boundary
discourse-position evidence to `like`/`actually`/`basically`, alongside the
existing punctuation-based signals) improves on the current heuristic's
documented downstream failure (see `design.md` "Evidence," from
`../real_human_validation_results.md` Test D) — **once EXP-M6-005's frozen
baseline annotations exist.** Full design, including known risks and known
unsolved cases: `design.md`.

## Status: implementation exists, evaluation does not

- `EXP-M6-005`'s pilot data collection is **not complete** (one Layer A event
  annotated as of this writing — see `../exp_m6_005_filler_evaluation/`).
- **No precision, recall, or F1 has been calculated for this candidate.**
- **No numeric comparison against production exists.**
- **No claim of improvement has been made or should be inferred** from this
  directory's existence.
- The only currently-true statement is: *the candidate implementation matches
  its specified behavior on the unit cases in `test_candidate.py`.* That is
  implementation verification, not evaluation evidence — see `design.md`
  "Evaluation plan" for what would actually be required before any
  performance claim.

## Nothing here changes DEC-015

`docs/decision-log.md` DEC-015 (filler vocabulary/policy, status:
Provisional/Experimental) is unaffected by this directory's existence.
Production's filler reliability tier stays `experimental` in `MetricCard`
regardless of what this candidate eventually shows — per the research-integrity rules in
`docs/methodology.md`, implementing a candidate does not itself justify upgrading anything.

## Files

- `candidate.py` — the candidate `detect_fillers_v2()` implementation, with
  frozen (not imported) copies of the production constants it's compared
  against, for reproducibility. See its module docstring and `design.md`
  "Threshold provenance."
- `test_candidate.py` — 12 unit cases (A–L) verifying the candidate's
  specified behavior, including that known false-positive risks and known
  unsolved cases behave exactly as documented, not as accidental gaps. Run
  with `pytest test_candidate.py` (no project dependency required —
  `candidate.py` has zero external imports beyond the standard library).
- `design.md` — the full approved design: problem, evidence, research
  rationale, baseline vs. candidate rule, expected benefit, known risks, known
  unsolved cases, threshold provenance, evaluation plan.
- `.gitignore` — ignores local `__pycache__/`/`.pytest_cache/` test-runner
  artifacts from running `test_candidate.py`.

## What happens next (not scheduled, not committed to by this document)

Once EXP-M6-005's pilot is complete and its Layer A/B annotations (and event-
matching timing tolerance) are frozen, both production's observed output
(Layer C) and this candidate's output can be scored against the same ground
truth using EXP-M6-005's already-defined metrics (`../exp_m6_005_filler_
evaluation/plan.md` §8). Only after that comparison exists would any of the
following become appropriate to consider — none of them are done here:
wiring `candidate.py` (or logic derived from it) into `backend/app/`, updating
DEC-015, or changing frontend filler copy.
