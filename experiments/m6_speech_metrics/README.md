# M6A — Speech Metrics & Evidence Design Experiment

**M6A is an experiment and decision milestone, not an implementation milestone.** No
production speech-metrics code is wired into the backend/frontend yet — see
`conclusions.md` for what was decided and `../../docs/decision-log.md` for the
resulting DEC-014/DEC-015/DEC-020 status.

## Environment this ran on

Same as M5 (`../m5_transcription/README.md`): macOS 13.0 (Ventura), Apple M1 (arm64),
Python 3.12.14, faster-whisper 1.2.1 / ctranslate2 4.8.1 / onnxruntime 1.23.2, CPU-only
(`base.en`, `device=cpu`, `compute_type=int8` — DEC-017).

## Important limitation: synthetic samples only, no real-human recording

Like M5, this sandboxed environment has no microphone. All samples in `samples/` are
synthesized via macOS `say` (text-to-speech), with pause samples using `ffmpeg`-injected
silence of an *exactly known* duration, so ground truth is fully controlled. Unlike M5,
this experiment has **no real-human recording at all** — M5's one ad hoc real-human
qualitative check was, per that experiment's own "keep raw audio gitignored, don't
commit private recordings" rule, never saved to disk, so there was nothing to reuse
here. This is flagged explicitly wherever it affects a conclusion, rather than
implied away — see `conclusions.md` "Limitations."

## Files

- `generate_samples.py` — regenerates `samples/*.webm` and `references/*.json`
  (macOS `say` + `ffmpeg`/`ffprobe` required; audio files are gitignored, script +
  JSON references are not)
- `evaluate_word_timestamps.py` — EXP-M6-001 (word- vs segment-level timestamps,
  revisits DEC-020)
- `evaluate_pauses.py` — EXP-M6-002 (word-gap inference vs VAD, informs DEC-014)
- `evaluate_fillers.py` — EXP-M6-003 (unconditional vs context-sensitive matching,
  informs DEC-015)
- `evaluate_repetitions.py` — EXP-M6-004 (repetition/restart heuristics, experimental)
- `references/` — hand-written ground truth (pause intervals, expected fillers,
  expected repetitions) written when the samples were scripted
- `results/` — actual measured output from the runs described in `conclusions.md`
- `experiment_plan.md` — hypothesis → experiment → result → decision structure for
  each EXP-M6-00N
- `conclusions.md` — full findings, metric reliability classification, and the
  resulting decisions

## Running it

```bash
cd experiments/m6_speech_metrics
python3 generate_samples.py                 # regenerate samples (optional if samples/ exists)
source ../../backend/.venv/bin/activate
python3 evaluate_word_timestamps.py
python3 evaluate_pauses.py
python3 evaluate_fillers.py
python3 evaluate_repetitions.py
```

## Samples

| Sample group | Purpose |
|---|---|
| `pause_0_5s` / `pause_1_0s` / `pause_2_0s` / `pause_3_0s` | Two phrases separated by an exactly-known injected silence |
| `pause_control_0s` | Same two phrases with **no** injected silence — false-positive check |
| `filler_um_uh` | Scripted "um"/"uh" (reused pattern from M5 `natural_fillers`) |
| `filler_like_discourse` / `filler_like_semantic` | Ambiguous "like" — discourse marker vs. genuine comparison |
| `filler_actually_hedge` / `filler_actually_semantic` | Ambiguous "actually" — hedge vs. semantic assertion |
| `filler_basically` / `filler_you_know` | Additional candidate vocabulary |
| `filler_none_clean` | Clean control — no fillers, false-positive check |
| `repetition_immediate` | Immediate exact phrase repeat ("I think, I think") |
| `repetition_restart` | Restart with partial overlap ("The main reason... the reason is") |
| `repetition_word_stutter` | Single-word stutter ("the the") — reuses `filler_um_uh`'s script |
| `repetition_none_clean` | Clean control — no repetition |

Also reuses `../m5_transcription/samples/*.webm` (`clear_speech`, `conversational_pace`,
`hesitation_restart`, `natural_fillers`, `near_silent`) for the word-timestamp latency
comparison, so results are directly comparable to the M5 benchmark's own latency figures.
