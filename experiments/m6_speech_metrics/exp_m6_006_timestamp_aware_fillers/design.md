# EXP-M6-006 — Timestamp-Aware Filler Heuristic: Design

Persists the approved design (2026-08-24). `candidate.py` implements exactly
what's described here. **Test D motivated this candidate but must not be used
as evidence that the candidate generalizes** — Test D is one transcript from
one recording; treating it as validation would repeat the exact overfitting
risk this project has already corrected against once (M7A's self-scoring
finding) and guarded against explicitly in EXP-M6-005's design (`plan.md`
§10/§13). The only claim this document or `candidate.py` makes is: *given the
observed failure pattern, here is a deterministic rule that would have handled
it, with its own new risks documented up front.*

## Problem

The current production filler detector (`backend/app/services/metrics/
fillers.py`) rejects real, Whisper-preserved discourse-marker tokens
(`like`/`actually`/`basically`) whenever the surrounding transcript lacks
punctuation — because its only positional signal is punctuation
(`preceded_by_comma`, `sentence_initial` via trailing `.`/`!`/`?`). Real
transcripts are not guaranteed to contain punctuation at all.

## Evidence

`experiments/m6_speech_metrics/real_human_validation_results.md`, **Test D**
(2026-08-21): the full transcript contains **zero punctuation** anywhere. *(The
verbatim transcript and the quoted surrounding words were removed from this file before
publication because they are real-voice content; the timestamps, verdicts and rule
traces below are unchanged. The original text is in the local-only recording data, not
in this repository.)* Three "like" tokens:
- first `like` token (5.68–7.14s) — clearly filler-like,
  rejected only for lacking punctuation.
- second `like` token (19.70–20.16s) — correctly suppressed
  (`comparison_verb_before`: a comparison verb immediately precedes it) — **not a
  failure**.
- third `like` token (33.68–35.08s) — clearly filler-like,
  immediately follows a **detected 5.38s pause**
  (`previous_word_end=28.30`, `next_word_start=33.68`,
  `observed_gap=5.38`) and is the first word of a new transcript segment —
  rejected because the rule has no awareness of pause/segment structure at
  all, only of punctuation.

## Research rationale

- `[PAPER]` Dinkar, Clavel, Vasilescu (2023): fillers occupy a genuine
  form/function ambiguity; ASR punctuation output cannot be assumed reliable
  — the structural reason a punctuation-only signal is incomplete, not a
  one-off unlucky transcript.
- `[PAPER]` Romana, Koishida, Mower Provost (2023): text-only methods inherit
  whatever the ASR layer lost or distorted — the reason this candidate is
  scoped strictly to *preserved*-token cases and makes no claim about
  recovering omitted tokens (see "Known unsolved cases" below).
- `[SPEAKLAB]` `docs/decision-log.md` DEC-014 already establishes a real,
  evidence-grounded (if Provisional) pause threshold for a related but
  distinct purpose (long-pause detection). This candidate reuses that exact
  value (frozen locally, see "Threshold provenance") rather than inventing a
  new number for "how long a pause counts as discourse-position evidence."

## Baseline rule (production, unchanged, restated for reference)

```
like:              flag if (preceded_by_comma OR sentence_initial)
                            AND NOT comparison_verb_before
actually/basically: flag if preceded_by_comma OR (sentence_initial AND followed_by_comma)
you know:          flag unconditionally on adjacent "you"+"know"
um/uh/ah/erm:      flag unconditionally if the token is present
```

`sentence_initial` is true only when the previous word's text ends in
`.`/`!`/`?`, or there is no previous word. No timestamp, gap, or segment
signal is used anywhere in production today.

## Candidate rule (`candidate.py`, this experiment)

New signal, defined once, reused across both extended tokens:

```
pause_boundary_signal(word, previous_word) =
    word.segment_start
    AND previous_word is not None
    AND word.start_time - previous_word.end_time >= PAUSE_DISCOURSE_THRESHOLD_SECONDS  # = 1.0
```

```
like:               flag if (preceded_by_comma OR sentence_initial OR pause_boundary_signal)
                             AND NOT comparison_verb_before
actually/basically:  flag if preceded_by_comma
                             OR (sentence_initial AND followed_by_comma)
                             OR pause_boundary_signal
you know:            UNCHANGED — unconditional, no context check added
um/uh/ah/erm:        UNCHANGED — unconditional given a preserved token
```

Everything else (vocabulary sets, `_COMPARISON_VERBS` suppression, the
`you know` adjacent-pair scan) is a frozen copy of production's current
behavior, not a reimplementation with new logic.

### Why `Word`/`FillerOccurrenceV2` aren't imported from production

`candidate.py` defines its own minimal `Word` (text, start_time, end_time,
segment_start) and `FillerOccurrenceV2` types rather than importing
`backend.app.services.transcription.base.TranscriptWordResult` /
`backend.app.services.metrics.base.FillerOccurrence`. Two reasons: (1) this
experiment has no dependency on the backend package or its import path,
keeping it runnable standalone; (2) `candidate.py` is proposing new
*candidate* logic to eventually be compared against production, not claiming
to explain or reuse production's own decision (contrast with EXP-M6-005's
`trace_current_filler_rules.py`, whose entire purpose is explaining an
already-final production result by importing its real helpers — a genuinely
different job from what this file does).

## Expected benefit

`[HYPOTHESIS]` — no numbers are claimed here, none are earned yet (see
"Evaluation plan"). If real pilot data confirms Test-D-style
pause-adjacent/punctuation-free cases recur, this rule should raise downstream
detector recall on the `like`/`actually`/`basically` subset without touching
`um`/`uh`/`ah`/`erm` or `you know` at all.

## Known false-positive risks (new, introduced by this rule)

- **Idiomatic pause-adjacent "like" constructions** — e.g. `"...incredible.
  [pause, new segment] Like I said, the results were..."`. `"Like I said"` is
  an idiomatic connective, not a hesitation filler, and has no comparison verb
  immediately before it to trigger suppression. **Not solved by this
  design** — an accepted, documented risk.
- **Segment splits that happen to clear the gap threshold for a non-discourse
  reason** (e.g. a breath, not a hesitation) — `pause_boundary_signal` is a
  proxy for discourse position, not a direct measurement of hesitation
  intent.

## Known unsolved cases

- **Punctuation-free, pause-free mid-clause fillers** — Test D occurrence 1's
  actual pattern (`test_j` in `test_candidate.py`). No signal in this design
  addresses it; documented as an intentional non-goal, not a test failure.
- **Semantic "you know"** (e.g. a genuine question) — deliberately left
  unaddressed; no observed failure motivates a specific fix, and inventing one
  without evidence would repeat the mistake this experiment exists to avoid.
  See `test_k` — it asserts *parity with baseline*, not correctness.
- **STT-omitted `um`/`uh`** (e.g. `controlled_01`) — see "Threshold
  provenance and scope" below; structurally out of reach for any
  `detect_fillers_v2`-shaped function.
- **Repetitions, restarts** — never in scope for this project's filler
  detection (`docs/decision-log.md`, `plan.md`); unaffected either way.

## Threshold provenance and scope

`PAUSE_DISCOURSE_THRESHOLD_SECONDS = 1.0` is a **frozen local copy** of
`pauses.py`'s `LONG_PAUSE_THRESHOLD_SECONDS`, inherited from DEC-014 as it
stood on 2026-08-24, not dynamically imported. This experiment does **not**
independently validate 1.0s as an optimal threshold for filler
discourse-position detection — reusing DEC-014's number avoids inventing a new
one, it does not endorse it as correct for this different purpose. If DEC-014
is revised later, `candidate.py`'s constant is updated only as a deliberate,
explicitly-logged new experiment run — never silently, so historical
EXP-M6-006 results remain reproducible against the value that actually
produced them.

**Why `um`/`uh` omission remains an STT-layer problem, out of this
candidate's scope:** `detect_fillers_v2`, like production's `detect_fillers`,
only ever receives a list of already-transcribed words. If "um" never becomes
a token at all (as in `controlled_01` — the pilot's own observed case), there
is no text, timestamp, gap, or segment boundary for *any* text-level rule to
inspect, because the absence occurs entirely upstream of this function's
input. No widening of context, no new signal, changes this. That problem is
tracked separately, as EXP-M6-007 (verbatim STT comparison) — a non-overlapping
track by construction, not by oversight.

## Evaluation plan

1. **Not scored yet.** EXP-M6-005's pilot annotation is incomplete (one Layer
   A event exists as of this writing). No precision/recall/F1 exists for
   either the baseline or this candidate.
2. **Never scored against Test D or `controlled_01` alone** — those are the
   two samples that motivated this design; scoring against them would be
   tuning on the same signal that produced the rule.
3. Once EXP-M6-005's baseline is complete and its Layer A/B annotations are
   frozen (including the timing tolerance, itself frozen before any scoring —
   `annotation_schema.md`), both the production heuristic (via its saved
   observed responses, Layer C) and this candidate (via a fresh
   `detect_fillers_v2` call over the same `transcription.words`, restructured
   into `Word` objects) are scored against the **same** frozen ground truth,
   using EXP-M6-005's already-defined event-level precision/recall/F1
   (`plan.md` §8).
4. This candidate must not be iteratively re-tuned by repeatedly checking its
   score against that same pilot set. A result — including a negative one —
   gets reported, not used to justify another rule tweak against the only
   data available.
5. Until step 3 happens, the only valid claim about `candidate.py` is:
   **it matches its specified behavior on the designed unit cases in
   `test_candidate.py`** — implementation verification, not evaluation
   evidence.
