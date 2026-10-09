# EXP-M6-005 — Collection Checklist

Practical per-recording steps. Full rationale for each step lives in
`annotation_schema.md` (Layer A/B/C definitions, observed-vs-reproduced
distinction, timing-tolerance rule) and `plan.md` (controlled-case matrix,
natural-speech design, stopping signals). This file is the short, practical
version to follow while actually collecting a recording — not a replacement for
those documents.

## Per-recording steps

1. **Record through SpeakLab** — use the app's normal flow end to end
   (Home → Prompt/skip → Preparation → Recording → manual stop). Controlled cases
   follow the scripted line for that `plan.md` §5 case; natural-speech recordings
   use a real prompt, answered unprepared, unscripted.
2. **Save the raw audio locally** — the exact `.webm` blob uploaded, into
   `data/raw/{recording_id}.webm` (gitignored, never committed).
3. **Save the full API response locally** — the complete `POST
   /api/v1/attempts/audio` response body (Network tab), into
   `data/raw/{recording_id}_response.json` (gitignored, never committed). This is
   the file Layer C will later read `metrics.fillers` from as the **observed
   production output** — see `annotation_schema.md`.
4. **Assign a `recording_id`** immediately (`controlled_01`…`controlled_11`, or
   `natural_01`…), and log it plus `type`/`case_id`/date in `data/raw/index.csv`
   (not yet created — created alongside the first real recording, not in this
   file-preparation step).
5. **Complete Layer A without viewing the transcript** — listen to the saved
   `.webm` only, blind to `_response.json`, and fill one row per audible
   filler-candidate into `data/annotations/layer_a.csv`
   (`annotator_timestamp_sec`, `manually_heard_token`, `filler_type`,
   `classification`, `annotator_confidence`, `context_note`, optional
   `confounder_note`). Finish all of a recording's Layer A — ideally all
   recordings' Layer A in a batch — before opening any `_response.json`.
6. **Reveal the response and complete Layer B** — open
   `data/raw/{recording_id}_response.json`, match each Layer A event to the
   nearest `transcription.words[]` entry, and fill `data/annotations/layer_b.csv`
   (`whisper_outcome`, `whisper_token`, `normalized_token_in_vocabulary`,
   `matched_word_start`/`_end`, `punctuation_context`, `segment_boundary`,
   `previous_word_gap_sec`).
7. **Use the saved `metrics.fillers` for Layer C** — read the filler events
   already present in that recording's own `_response.json` (the exact result
   SpeakLab actually returned for that attempt), match them to Layer A/B events,
   and fill `data/annotations/layer_c.csv` (`detector_flagged` with
   `detector_source=observed_production_response`, `manual_classification`,
   `agreement` where not ambiguous, optional `rule_branch_reason` for
   failure-analysis cases only). **Do not** re-run `detect_fillers()` in a REPL
   as this row's source — that is a separate, later reproducibility check only
   (see `annotation_schema.md` "Observed vs. reproduced").
8. **Update the stopping log** — append one row to
   `data/derived/pilot_stopping_log.csv` for this recording
   (`new_failure_category`, `stt_omission_pattern`, `detector_failure_pattern`,
   `ambiguous_event_count`, `qualitative_understanding_still_changing`).

## Timing-calibration steps (done once, separately from individual recordings)

Not tied to a single recording — done against 5 already-annotated, clearly
audible events, at least one listening session apart from their original
annotation:

1. Pick 5 unambiguous Layer A events.
2. Re-listen and independently re-timestamp each one twice (two fresh
   timestamps per event, not compared against the original Layer A value).
3. Record all 5 pairs in `data/derived/calibration_timestamps.csv`
   (`first_timestamp_sec`, `second_timestamp_sec`, `abs_diff_sec`).
4. If one pair is a clear outlier, flag it (`outlier_flag`, `notes`) rather than
   silently dropping it, and reconsider the annotation procedure before
   proceeding (see `annotation_schema.md`).
5. Compute the tolerance as the **maximum** `abs_diff_sec` across the full
   calibration set (predeclared formula, `annotation_schema.md` "Event matching
   rule and timing tolerance") — before looking at any detector precision,
   recall, or F1 number.

## What this checklist deliberately does not cover

Running `evaluate.py` (not built), computing precision/recall/F1 (no scoring
until the tolerance above is frozen and enough recordings exist per `plan.md`
§10's stopping signals), or touching `backend/app/services/metrics/fillers.py`
(never modified by this experiment).
