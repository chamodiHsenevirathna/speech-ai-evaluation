# AI Boundaries

## Principle

Measurable, verifiable values are computed deterministically. Generative AI (Gemini) is
used only for interpretation and coaching language, grounded in evidence it did not
produce itself. The LLM is never the authoritative source for a number, a timestamp, or a
detection.

## Responsibility Table

| Capability | Responsibility |
|---|---|
| Recording duration | Deterministic |
| Word count | Deterministic |
| WPM | Deterministic |
| Pause duration | Deterministic |
| Basic filler detection | Deterministic / validated detector |
| Transcript | STT model (faster-whisper) |
| Primary improvement issue | AI interpretation |
| Coaching explanation | AI interpretation |
| Retry recommendation | AI interpretation |

## AI Must Never

- Invent measurements (duration, WPM, counts, etc.)
- Invent timestamps
- Diagnose anxiety
- Diagnose speech disorders
- Infer intelligence
- Infer personality
- Make unsupported medical claims
- Overwrite measured values

## Insufficient Evidence

If the structured evidence passed to the coaching service is insufficient to support a
specific claim (e.g. very short/near-empty transcript, no detected pauses or fillers), the
coaching output should **abstain or explicitly state that there is insufficient evidence**
rather than generating generic filler feedback (e.g. "be more confident").

## Gemini Is Optional, Not Required

The core SpeakLab application — recording, transcription, deterministic metrics, evidence,
retry, and comparison — must run and be fully usable **locally with no `GEMINI_API_KEY`
configured at all**. Gemini coaching is an optional external service layered on top of the
core pipeline; it is never a dependency required to run or use the application.

If `GEMINI_API_KEY` is missing, or the Gemini call fails (network failure, API error,
timeout):

- The transcript is still shown.
- Deterministic metrics are still shown.
- Deterministic evidence (pauses, fillers) is still shown.
- The coaching section is clearly marked as unavailable — not silently omitted, not
  replaced with a fabricated fallback.
- The user can retry the coaching call later via an explicit "retry coaching" action,
  without re-recording or re-transcribing (see `requirements.md` FR-19, `context.md`
  "Gemini/coaching failure").

## Interface Isolation

The coaching service is implemented behind a service interface (see `context.md`).
It receives only structured evidence (transcript + `SpeechMetrics`) as input — never raw
audio — which both enforces the deterministic/generative boundary and keeps the provider
swappable.

## Model Provenance

**Transcription:** `faster-whisper`, model size `base.en`, `device=cpu`,
`compute_type=int8` — chosen via an evidence-based local benchmark, not a default or a
guess (DEC-004 for the library choice, DEC-017 for the specific size/device/compute
type, with the full experiment in `experiments/m5_transcription/`). Word-level
timestamps were evaluated separately and accepted at M6A (DEC-020,
`experiments/m6_speech_metrics/`).

**Coaching:** Gemini — planned (M8), not yet implemented. No model/version has been
selected yet; when it is, that choice should follow the same evidence-based pattern
below, and get its own decision-log entry the same way DEC-004/DEC-017 do for
transcription.

## Model-Change Policy

A production model or model-setting change that can materially affect user-facing
behavior — the transcription model or size, `device`/`compute_type`, timestamp
granularity (word vs. segment), a pause/filler threshold derived from experiments, or a
future coaching provider/model — must never be made silently. It requires:

```
Hypothesis / reason
  → Experiment or evaluation
    → Comparison (against current behavior, not evaluated in isolation)
      → Result (actually measured)
        → Documented decision (decision-log.md)
```

This is not a new rule — it is the pattern DEC-004, DEC-017, and DEC-020 already
followed, made explicit here so it's not accidentally skipped for a future change that
feels "small" (e.g. bumping a model size without re-benchmarking). See `docs/methodology.md` "Research-integrity rules" for the same policy stated as a general research rule.

## Human Responsibility

AI/tools in this project's workflow may: propose approaches, generate code, suggest
designs, run experiments, and summarize evidence.

The human remains responsible for: product goals and requirements (`requirements.md`),
approving any architecture change (the project's architecture-change rule),
interpreting evaluation evidence that is inherently limited (small synthetic sample
sizes, one-machine benchmarks — see `experiments/*/conclusions.md` "Limitations"
sections), deciding whether an experimental metric is promoted into a shipped product
feature (e.g. moving a metric's classification from EXPERIMENTAL to ACCEPTED, see
`experiments/m6_speech_metrics/conclusions.md` Step 14), and approving every commit —
no milestone in this project's history has been committed without explicit human
review, and that is a standing rule, not a one-off preference.
