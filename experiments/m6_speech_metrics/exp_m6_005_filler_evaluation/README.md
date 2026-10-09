# EXP-M6-005 — Real-Human Filler Detection Evaluation

**Status: in progress / partial. Experiment design is complete; one pilot recording
(`controlled_01`) has been collected and partially annotated — this is not yet a
scored baseline.** Specifically: Layer A (manual ground truth) and Layer B
(Whisper-output mapping) are complete for `controlled_01`'s one annotated event.
Layer C intentionally has **no row** for that event — the event's `whisper_outcome`
is `omitted`, so per the schema (`annotation_schema.md` "Layer C population") the
detector never received a token to evaluate, and no Layer C row should exist for it.
The timing-calibration step (`collection_checklist.md`) has not yet been done. No
precision/recall/F1 has been computed, and none should be inferred from this
directory yet — a single annotated event is a pilot data point, not an evaluation
set. See `plan.md` for the full experiment design and `research_review.md` for the
literature grounding it.

## Purpose

Determine whether the current filler-detection pipeline (`backend/app/services/
metrics/fillers.py`, DEC-015, EXPERIMENTAL) is reliable enough to improve, replace,
or keep as-is — by separating three sources of error that a single end-to-end
"fillers detected" count currently conflates:

1. a filler is genuinely spoken in the audio,
2. `faster-whisper` preserves or drops/normalizes it,
3. the current contextual detector correctly classifies whatever token survives.

## Why Test D triggered this

`real_human_validation_results.md` "Test D" (2026-08-21) is a single controlled
real-human recording where the speaker deliberately said "um," "uh," and "like"
multiple times, plus one intentional ~3–5s pause. The pause detector correctly
flagged the pause (`observed_gap=5.38s`, arithmetically confirmed). The filler
detector produced an **empty** `fillers` array, traced by hand to **two distinct,
separable causes**: "um"/"uh" never appeared in `transcription.words` at all
(upstream STT omission), and all three surviving "like" tokens were rejected by
`detect_fillers()`'s context rule because this specific transcript contained **zero
punctuation** anywhere, and the rule's `discourse_position` check is structurally
dependent on punctuation (`preceded_by_comma` / `sentence_initial`). One sample
cannot establish how common either failure mode is, or which dominates — that
requires the structured evaluation this directory designs.

## Baseline-first sequencing

EXP-M6-005 evaluates **only** the current heuristic (Alternative A) against
manually annotated ground truth. Alternatives B (improved text/timestamp
heuristic) and C (acoustic/disfluency model) are **not implemented or tuned**
here — see `plan.md` "Alternatives" and "Decision criteria." This is deliberate:
tuning an alternative against the same tiny dataset that surfaced the original
problem (Test D) would risk overfitting the "improvement" to that one sample. A
possible **EXP-M6-006** — evaluating Alternative B — is only in scope after
EXP-M6-005's baseline results exist and are reviewed. Alternative D (conservative
product/copy approach — e.g. "Detected fillers" → "Possible fillers detected") does
not depend on this experiment at all and can be decided independently at any time.

## Privacy / local-only raw-data policy

Raw audio and full API-response JSON (which embeds complete transcript text) are
**not committed**. `data/raw/` is gitignored (see `.gitignore` in this directory,
which contains exactly `data/raw/`) — the same per-experiment-directory pattern
already used by `../.gitignore` and `../../m5_transcription/.gitignore` for their
`samples/`, extended here to a materially different case: those directories hold
synthetic, regenerable TTS audio; `data/raw/` here holds **real human voice**,
which cannot be regenerated and may be identifiable. What *is* committed:
`plan.md`, `annotation_schema.md`, `research_review.md`, this `README.md`,
de-identified annotation records (`data/annotations/` — timestamps, classifications,
short illustrative fragments only, never full transcripts), derived/aggregated
tables (`data/derived/`), and eventual aggregate metrics/`conclusions.md` — never
raw audio, never a full verbatim transcript.

## Reproducibility limitation

External reviewers of this repository can reproduce the experiment **protocol** —
the annotation schema, the metric formulas, the tracing/evaluation approach — but
**cannot** reproduce the exact recordings or their full transcripts, since those
never enter version control. This mirrors the same limitation already accepted for
M6B's real-human validation tests (Tests A–D in `../real_human_validation_results.md`).

## Evidence-type discipline

Every claim in this directory's documents (`plan.md`, `research_review.md`) is one
of exactly three kinds, and they are never blended without saying so:

- **`[PAPER]`** — a finding directly attributable to one of the four reviewed
  sources (see `research_review.md`), cited to that source.
- **`[SPEAKLAB]`** — something actually observed from SpeakLab's own code or real
  recordings (e.g. Test D's data, or a fact read from `fillers.py`).
- **`[HYPOTHESIS]`** — a reasoned expectation not yet confirmed by either of the
  above, stated as such, not as a conclusion.
- **`[VERIFIED-EXTERNAL]`** — a fact checked directly against a third-party
  source (a repository, model card, or license file) that isn't one of the four
  reviewed papers — e.g. whether pretrained weights exist, what license they
  carry, whether CPU inference is documented. See `research_review.md` "Fix-design
  review" for the first use of this tag.

Published benchmark numbers (e.g. PodcastFillers' or the semi-CRF paper's reported
F1 scores) are never treated as predictions of SpeakLab's own performance — see
`research_review.md` for why (different domain, different ASR model, different
recording conditions).

## Relationship to possible EXP-M6-006 / EXP-M6-007

Locked 2026-08-24, after a fix-design review of two real observed failures
(controlled_01's upstream STT omission; Test D's downstream rule miss) —
see `plan.md` §12 for the full decision tree:

- If EXP-M6-005's baseline results show **downstream rule logic** (not upstream
  STT omission) is the dominant, reproducible error source, a follow-up
  **EXP-M6-006** could evaluate `plan.md` Alternative B (an improved
  text/timestamp heuristic) against the *same* annotated ground truth, without
  re-tuning the evaluation criteria themselves.
- If baseline results show **upstream STT omission** is the dominant,
  reproducible error source, a follow-up **EXP-M6-007** could compare
  Alternative B′ (verbatim STT, e.g. CrisperWhisper, or an
  `initial_prompt`-seeded `base.en`) against the current transcription service
  — see `plan.md` "EXP-M6-007 provisional design."
- If both matter, a combined architecture is evaluated only **after** both
  EXP-M6-006 and EXP-M6-007 have real results — it is explicitly not
  pre-selected now.
- A standalone acoustic filler-detection model (`plan.md` Alternative C) is
  **already rejected for V1**, independent of what EXP-M6-005/006/007 find —
  see `research_review.md` "Fix-design review" for the verified reasons
  (no released pretrained weights, CUDA-only training path, no CPU inference
  documented, non-commercial dataset license).

Neither EXP-M6-006 nor EXP-M6-007 is scoped, scheduled, or committed to by this
document — both are named here only so the sequencing intent is traceable from
this experiment forward.
