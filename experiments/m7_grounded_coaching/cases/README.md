# M7A Evaluation Set

`manifest.json` contains 16 fixture cases, each a self-contained bundle of `prompt`,
`transcript_text`, `duration_seconds`, `word_count`, `words_per_minute`, `long_pauses`,
`fillers`, `reliability`, `design_note`, and `source`.

All numeric fields (`word_count`, `words_per_minute`) are computed programmatically
from the transcript text and stated duration (see the build script referenced in
`../conclusions.md`), so they are internally consistent — not hand-typed
approximations that could drift from the transcript they describe.

## Why one `manifest.json` instead of 16 files

The task brief suggested a `cases/` directory; this implementation uses one structured
JSON file inside it rather than one file per case, since every case shares an identical
schema and cross-referencing them (e.g. in `results/`) is simpler against one file. This
is a deliberate structure choice, not a shortcut — each case is still fully
self-contained and independently addressable by `id`.

## Case index

| ID | Categories | Source |
|---|---|---|
| CASE-01 | strong_structure, clear_conclusion | synthetic |
| CASE-02 | high_wpm, rushed_delivery | synthetic |
| CASE-03 | slow_response, low_wpm | synthetic |
| CASE-04 | fillers_present | synthetic |
| CASE-05 | no_fillers, clean_delivery | synthetic |
| CASE-06 | long_pauses | synthetic |
| CASE-07 | wandering_answer, weak_focus | synthetic |
| CASE-08 | weak_conclusion | synthetic |
| CASE-09 | strong_conclusion | synthetic |
| CASE-10 | fragmented_thought, restarts | synthetic |
| CASE-11 | concise_clear | synthetic |
| CASE-12 | ambiguous_transcript, poor_stt | synthetic |
| CASE-13 | near_silence, insufficient_evidence | real-human (Test C transcript outcome) |
| CASE-14 | conflicting_signals | synthetic |
| CASE-15 | single_filler_only, experimental_evidence_only | synthetic |
| CASE-16 | real_human_scripted, controlled_fillers_and_pauses | real-human (Test B script + detections) |

CASE-13 and CASE-16 reuse content already committed and public in
`experiments/m6_speech_metrics/real_human_validation_results.md` (Test C and Test B
respectively) — no new real-human audio or transcript was captured for this milestone,
per `docs/privacy.md`'s experiment-privacy policy (no raw audio ever committed; written
observations only).

All other 14 cases are synthetic text fixtures authored for this milestone — invented
transcripts, not claims about any real speaker, and not audio (no synthesis/recording
was performed).

## Coverage against the task brief's requested categories

Strong structured response (CASE-01), high WPM (CASE-02), slow response (CASE-03),
fillers (CASE-04), no fillers (CASE-05), long pauses (CASE-06), wandering answer
(CASE-07), weak conclusion (CASE-08), strong conclusion (CASE-09), fragmented thought
(CASE-10), concise clear answer (CASE-11), ambiguous/poor transcript (CASE-12),
near-silence/insufficient evidence (CASE-13), conflicting signals (CASE-14),
experimental filler evidence only (CASE-15) — all 15 requested categories are covered,
plus CASE-16 as an additional real-human-grounded case.
