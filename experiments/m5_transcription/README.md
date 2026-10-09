# M5 Transcription Model-Selection Experiment

Resolves DEC-017 (faster-whisper model size/device/compute type) with an evidence-based
local benchmark, per `docs/decision-log.md`. **Small and provisional** — see
`conclusions.md` for explicit caveats. Not a rigorous model evaluation.

## Hypothesis

A small local faster-whisper model can provide sufficiently useful transcription for
~60-second impromptu speaking samples while keeping latency acceptable for an
interactive practice workflow.

## Environment this ran on

- macOS 13.0 (Ventura), Apple M1 (arm64), 8 cores
- Python 3.12.14 (see `../../backend/README.md` for why — Python 3.14, the system
  default, cannot install this dependency chain here; full details below)
- faster-whisper 1.2.1, ctranslate2 4.8.1, onnxruntime 1.23.2
- Device: **CPU only**. No CUDA (no NVIDIA GPU on Apple Silicon). CTranslate2 has no
  Apple Metal/Neural-Engine backend as of this version — it runs CPU inference via
  Apple's Accelerate framework, not GPU-accelerated.

## Important limitation: no real microphone available

This is a sandboxed development environment with no microphone access. The evaluation
samples are **synthesized locally via macOS `say` (text-to-speech), not real human
recordings** — see `generate_samples.sh`. They let us exercise the real decode →
transcribe pipeline end-to-end and compute exact Word Error Rate (since we wrote the
script text ourselves, it *is* the ground truth), but:

- They cannot represent real accent, breath, background noise, or natural disfluency
  acoustics (only scripted filler *words*, not natural hesitation timing).
- A non-native-accented English sample was requested by the task but could not be
  produced — no such voice/proxy was available in this environment. This is an
  explicit, acknowledged gap, not a silent omission.
- The audio *is* real WebM/Opus (converted via `ffmpeg`), matching what
  `frontend/src/media/audioFormat.ts` actually produces, so the decode step is
  genuinely tested.

Real-speech validation should happen via the manual testing checklist in the M5 final
report / `backend/README.md` once a person actually uses the app.

## Files

- `generate_samples.sh` — regenerates `samples/*.webm` and `references/*.txt` (macOS +
  `ffmpeg` required; audio files are gitignored, script + text are not)
- `benchmark.py` — runs each candidate model against every sample, writes
  `results/results.json` and `results/results.csv`
- `results/` — actual measured output from the run described in `conclusions.md`
- `conclusions.md` — hypothesis → experiment → result → decision

## Running it

```bash
cd experiments/m5_transcription
./generate_samples.sh          # regenerate samples (optional if samples/ already exists)
source ../../backend/.venv/bin/activate
python benchmark.py
```

## Samples

| Sample | Purpose | Duration |
|---|---|---|
| `clear_speech` | Clean, unhesitant sentence | ~5.6s |
| `natural_fillers` | Scripted "um"/"uh" | ~7.4s |
| `hesitation_restart` | Scripted repeated/restarted phrase | ~8.9s |
| `conversational_pace` | Longer casual monologue (matches an actual SpeakLab prompt topic) | ~15.6s |
| `near_silent` | Pure digital silence (tests "no speech" handling) | 3.0s |

None are close to the full ~60s target duration — kept short deliberately so the
benchmark runs quickly and reference transcripts stay easy to verify by eye. Latency/RTF
still generalizes reasonably since faster-whisper processes audio in a streaming,
roughly linear-with-duration fashion (see `conclusions.md`).
