# M5 Transcription Experiment — Conclusions

**Status: small, provisional, local benchmark.** 5 short synthetic (TTS) samples, 2
model candidates, one machine. This resolves DEC-017 with real evidence rather than a
guess, but it is not a rigorous or generalizable model evaluation — see "Limitations"
below.

## Hypothesis

A small local faster-whisper model can provide sufficiently useful transcription for
~60-second impromptu speaking samples while keeping latency acceptable for an
interactive practice workflow.

## Experiment

Compared `tiny.en` and `base.en` (both `device=cpu`, `compute_type=int8`) against 5
locally-generated samples (see `README.md`). Measured latency, Real-Time Factor (RTF =
transcription_seconds / audio_duration_seconds), transcript output, filler-word
preservation, and Word Error Rate against hand-written references. Full raw output in
`results/results.csv` / `results/results.json`.

`small.en` was **not** downloaded. Both smaller candidates already showed ample latency
headroom (RTF well under 0.25 — see below) and near-identical accuracy on this sample
set, so a third, ~3x-larger download wouldn't have taught us anything the TTS samples
could actually reveal (see "Why the samples can't differentiate accuracy" below). Per
the M5 instructions, a model shouldn't be downloaded "merely for appearance."

## Results

| Model | Sample | Duration | Transcribe time | RTF | WER | Fillers (ref/hyp) |
|---|---|---|---|---|---|---|
| tiny.en | clear_speech | 5.61s | 1.06s | 0.189 | 0.0 | 0/0 |
| tiny.en | conversational_pace | 15.59s | 1.30s | 0.083 | 0.035 | 0/0 |
| tiny.en | hesitation_restart | 8.88s | 1.09s | 0.123 | 0.0 | 0/0 |
| tiny.en | natural_fillers | 7.35s | 0.87s | 0.119 | 0.091 | 2/1 |
| tiny.en | near_silent | 3.00s | 0.49s | 0.164 | n/a | 0/0 |
| base.en | clear_speech | 5.61s | 1.08s | 0.192 | 0.0 | 0/0 |
| base.en | conversational_pace | 15.59s | 1.93s | 0.124 | 0.035 | 0/0 |
| base.en | hesitation_restart | 8.88s | 1.15s | 0.130 | 0.0 | 0/0 |
| base.en | natural_fillers | 7.35s | 1.12s | 0.152 | 0.091 | 2/1 |
| base.en | near_silent | 3.00s | 0.69s | 0.229 | n/a | 0/0 |

Model load time (one-time, first request only — see "Lazy loading" in
`backend/app/services/transcription/faster_whisper_service.py`): tiny.en 40.1s,
base.en 68.2s (dominated by first-time download from Hugging Face Hub, not
inference — a cached second run loads in a few seconds).

Approximate download footprint (measured via the Hugging Face cache directory, not the
in-script estimator which returned `None` — see "Limitations"): **tiny.en ≈ 74 MB**,
**base.en ≈ 141 MB**.

### Notable qualitative findings (not fabricated metrics — direct observations)

- **"uh" → "ah"**: both models transcribed the scripted "uh" as "ah" in
  `natural_fillers`, while correctly preserving "um" verbatim. This is a real,
  repeatable finding relevant to M6's filler-vocabulary decision (DEC-015): a
  filler-detection pass matching only `{"um", "uh"}` literally against Whisper output
  would miss this. Worth revisiting when DEC-015 is resolved.
- **Repetition smoothing**: `hesitation_restart`'s scripted "I wanted to talk about, I
  wanted to talk about..." was transcribed faithfully (both models kept the repeat) —
  but `natural_fillers`' doubled "the the" was **not** preserved by either model (both
  output "the" once). Whisper's decoder appears to sometimes normalize word-level
  stutters away. This matters for any future repetition/restart detection: it cannot
  assume the transcript reliably preserves every disfluency.
- **Silence hallucination**: the pure-silence `near_silent` sample was **not**
  transcribed as empty by either model — both produced the single word "You". This is a
  known Whisper behavior on low-energy/silent audio. See "VAD investigation" below for
  why we can't easily fix this in the current environment, and
  `docs/context.md`/`docs/context.md` for how this is handled at the product
  level regardless (a short spurious transcript, not a crash).

### VAD (voice activity detection) investigation

faster-whisper supports `vad_filter=True` to suppress exactly this kind of
silence/hallucination artifact, using a bundled Silero VAD model via `onnxruntime`.
**In this specific environment it crashes**:

```
ImportError: dlopen(.../onnxruntime_pybind11_state.so, ...): Symbol not found:
__ZNSt3__18to_charsEPcS0_d
... built for macOS 13.4 which is newer than running OS ...
```

`onnxruntime==1.23.2` is the newest version with a macOS-arm64 wheel compatible with
this machine's Python (3.12) *and* declared minimum OS version (13.0) — but that wheel's
actual binary was built against macOS 13.4's libc++, one point release newer than what's
actually running here (13.0). The wheel installs successfully (pip's platform-tag
matching doesn't catch this), but crashes at dlopen time.

**Consequence:** `vad_filter` is left at its default (`False`) in
`FasterWhisperTranscriptionService`. Since it's off by default, `onnxruntime` is never
actually imported during normal transcription (faster-whisper imports it lazily, only
when VAD is requested) — so this crash never occurs in the running application, only in
this diagnostic probe. This is documented here so a future milestone doesn't
re-introduce VAD without knowing this machine (and possibly others on an older point
release of the same major macOS version) needs an OS update or a different onnxruntime
build first.

### Why the samples can't differentiate accuracy meaningfully

TTS-generated audio is about as clean as speech gets — no accent, no background noise,
consistent pacing, no breath artifacts. Both models scored identically or
near-identically here, but that says more about the samples than the models: a harder,
real-accented sample would likely separate them further (tiny.en is generally documented
elsewhere as noticeably less robust than base.en on accented/noisy real speech — we are
not fabricating a number for that here, just noting the direction, since our own data
can't measure it).

## Decision (resolves DEC-017)

**Default: `base.en`, `device=cpu`, `compute_type=int8`.**

**Reasoning:**
- Both candidates comfortably meet the latency bar for an interactive ~60s practice
  clip (RTF 0.08–0.23, i.e. transcription finishes in well under a third of the
  recording's own length even on `base.en`).
- Since latency isn't the limiting factor for either model at this size, we lean toward
  the more accurate one for real (non-synthetic, potentially accented) speech, since
  that's the actual product need — a speaker practicing impromptu English, not
  necessarily with studio-clean pronunciation.
- `base.en`'s ~141 MB footprint is still a small, one-time local download appropriate
  for a local-first single-user dev tool (see DEC-007).

**Quality vs. latency trade-off:** `base.en` is measurably slower per sample (up to
~1.8x tiny.en's transcription time in this data), but both remain fast in absolute
terms for a single ~60s clip in an interactive flow — a user waiting under 15s for
transcription of a full-length recording is acceptable for a practice tool that isn't
real-time-streaming.

**Limitations of this evidence:**
- 5 short synthetic samples, one machine, one CPU, no real human speech, no accented
  speech went into the model-selection decision above (the decision itself predates
  and does not rely on real-human input). A separate small qualitative real-human,
  non-native-accented check was performed afterward (see "Real-human validation"
  below) but was not a comparative benchmark and did not re-run the tiny.en/base.en
  comparison — it only validates the already-chosen configuration.
- If real-recording evaluation later shows `base.en` insufficient (or more than
  sufficient, favoring `tiny.en` for speed on lower-end hardware), this decision should
  be revisited with a new decision-log entry, not silently overridden.

## Word-level vs. segment-level timestamps

Measured cost of `word_timestamps=True` on `conversational_pace` (base.en): 2.02s vs.
1.82s without — **≈11% overhead** on this sample, producing precise per-word start/end
times (e.g. `("Last", 0.0, 0.2)`, `("year", 0.2, 0.42)`).

**Decision: not enabled in M5.** Segment-level timestamps (already returned by every
model regardless of this flag) are sufficient for M5's actual scope — M5 does not do
pause or filler detection, so nothing in this milestone consumes word-level timing.
Enabling an unused flag now would add latency and complexity with zero observable
benefit today, which cuts against this project's "add only what's justified by actual
implementation" approach used consistently elsewhere (see `docs/context.md`).

**For M6:** pause detection fundamentally needs finer-than-segment granularity — a
single Whisper segment can span many seconds and multiple words, hiding an internal
pause entirely. When M6 is scoped, `word_timestamps=True` should be enabled at that
point; the ~11% overhead measured here is small enough not to be a blocker. This is
recorded so M6 doesn't have to re-derive it.

## Real-human validation (qualitative, not a benchmark)

**This is a separate, small qualitative check — not part of the synthetic benchmark
above, not a formal evaluation, and not a source of WER.** Unlike the 5 TTS samples
above, this used one real recording of real human speech, with no manually-aligned
reference transcript created for it. No WER is reported here, and none should be
inferred or estimated from this note.

- ~100 seconds of natural spoken response, real human speech, non-native-accented
  English — the accent gap explicitly flagged as unavailable earlier in this document
  was subsequently closed for this one qualitative check.
- Model: `base.en`, `device=cpu`, `compute_type=int8` (the configuration resolved by
  the synthetic benchmark above, validated here rather than re-decided).
- Transcription latency: 8.3s. Approximate RTF: 0.083 — consistent with (in fact
  slightly better than) the RTF range measured on the synthetic samples, suggesting
  the synthetic benchmark's latency numbers are a reasonable proxy for real speech at
  this length.
- Overall spoken content was broadly captured.
- Several meaningful lexical transcription errors were observed (words the model got
  wrong, not merely stylistic differences) — consistent with `tiny.en`/`base.en` being
  the smaller end of the Whisper family, and with the synthetic benchmark's own
  caveat that clean TTS samples cannot reveal accent-related accuracy loss.
- Segment timestamps appeared broadly plausible against the audio, on informal
  listening (not frame-accurate verification).
- Some discourse markers such as "like" were preserved in the output, though not
  exhaustively verified against every occurrence in the source audio.

**Why this doesn't produce a WER figure:** computing WER requires a manually
word-aligned reference transcript, which was not created for this recording. Reporting
a WER here would mean either fabricating one or silently skipping the alignment step
that gives the number meaning — neither is acceptable, so none is reported.

**Implication:** this reinforces that the transcript must not be treated as perfect
ground truth for downstream filler, repetition, or speech-quality metrics (M6+) — the
lexical errors observed here are exactly the kind of noise those metrics will need to
tolerate, not assume away.

## Limitations of this experiment overall

- The synthetic benchmark used no real microphone/human speech (see README.md). A
  separate, small qualitative real-human, non-native-accented check was later
  performed — see "Real-human validation" above — but it is not a WER-scored
  benchmark and does not replace a proper accented-speech evaluation.
- `small.en` not evaluated (reasoning above).
- The benchmark script's `approx_model_footprint_mb` field returned `None` for both
  candidates - the private attribute it probed doesn't exist in this faster-whisper
  version. Footprint was measured manually instead via the Hugging Face cache directory
  (see Results above). Not fixed in `benchmark.py` since it's a one-off measurement, not
  something the running application needs.
- Only one hardware/OS configuration tested (Apple M1, macOS 13.0). Results on other
  machines (especially Linux/x86 with CUDA available) were not measured.
