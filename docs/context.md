# Research Context

A short, research-specific description of the system the experiments evaluate: the pipeline,
the data contract the experiments consume, the failure semantics, and the evaluation criteria.
Everything below is copied **verbatim** (apart from repointed cross-references to the other documents) from the SpeakLab application's design documents
(architecture, domain model, user flows and test plan); only the sections that bear on the
experiments are kept. Terms such as "M4" or "M6B" refer to the application's internal build
stages. Paths under `frontend/` or in backend modules not included here (for example `app/main.py`), and to application documents such as `design-system.md`, refer to the SpeakLab application, not to this repository.

## From the architecture document

### Layering Principle

```text
Audio → transcription → deterministic analysis → structured evidence → AI interpretation
```

Each stage consumes only the output of the stage before it. **The diagram above draws the
STT Layer and Speech Metrics Engine as side-by-side boxes for visual layout only — this
does not imply they run in parallel or independently.** Metrics that depend on the
transcript (word count, WPM, pause detection) cannot run until transcription has produced
that transcript; transcription strictly precedes transcript-dependent metrics. The AI
interpretation stage (coaching) is the only stage that is optional and allowed to fail
without invalidating earlier stages. See `ai-boundaries.md` for what the LLM is and is not
allowed to determine.

### Processing Status → UI

The frontend tracks four independent per-stage statuses for a `SpeechAttempt` — upload
(M4), transcription (M5), metrics (M6), coaching (M8) — each one of `pending` / `success`
/ `failed` (see `context.md`). The Processing and Results screens render directly
from these statuses (e.g. via the `LoadingState`/`ErrorState`/`ProcessingStageList`/
`CoachingCard` components in `design-system.md`), so a failed stage can be shown alongside
succeeded earlier stages without the UI treating the whole attempt as failed. `upload`
success only means the backend received and validated the audio bytes — it does not imply
anything about transcription, metrics, or coaching, which remain `pending` ("not started")
until their respective milestones land.

### API Contract

Implemented endpoints (M4). All error responses share one envelope shape:

```json
{ "error": { "code": "MACHINE_READABLE_CODE", "message": "Human-readable, UI-safe text" } }
```

Error messages are always curated for display — the backend never returns a raw Python
exception/traceback to the client (`app/main.py` installs handlers for `ApiError`,
`RequestValidationError`, and any uncaught `Exception` that each produce this envelope).

#### `POST /api/v1/attempts/audio`

Accepts a recorded audio clip, validates it, transcribes it (since M5), and (since M6B)
**computes deterministic speech metrics** — all in the same request, see
`docs/decision-log.md` DEC-019 for why this isn't a second endpoint (the same reasoning
now extends to metrics). Still does not persist the audio (DEC-018) or compute
coaching (M8).

**Request:** `multipart/form-data`

| Field | Required | Notes |
|---|---|---|
| `file` | Yes | The recorded audio `Blob`; content type must be `audio/*` |
| `session_id` | No | Frontend-generated identifier, echoed back if provided |
| `attempt_id` | No | Frontend-generated identifier, echoed back if provided |

**Response `200`** (upload accepted — this is independent of whether transcription
itself succeeded, see below):
```json
{
  "status": "accepted",
  "filename": "attempt-audio.webm",
  "content_type": "audio/webm",
  "byte_size": 48213,
  "session_id": "s1",
  "attempt_id": "a1",
  "transcription": {
    "status": "success",
    "text": "So, um, I think the best way to explain this is...",
    "language": "en",
    "segments": [
      { "start_time": 0.0, "end_time": 2.4, "text": "So, um, I think the best way..." }
    ],
    "words": [
      { "start_time": 0.0, "end_time": 0.3, "text": " So," },
      { "start_time": 0.3, "end_time": 0.6, "text": " um," }
    ],
    "model": "base.en",
    "duration_seconds": 12.3,
    "transcription_seconds": 1.9,
    "error": null
  },
  "metrics": {
    "status": "success",
    "duration_seconds": 12.3,
    "word_count": 24,
    "words_per_minute": 117.1,
    "long_pauses": [
      {
        "previous_word_end": 5.2,
        "next_word_start": 6.3,
        "observed_gap": 1.1,
        "threshold": 1.0,
        "method": "whisper_word_gap"
      }
    ],
    "fillers": [
      { "text": "um", "category": "um", "start_time": 0.3, "end_time": 0.6 }
    ],
    "reliability": {
      "duration_seconds": "exact",
      "word_count": "approximate",
      "words_per_minute": "approximate",
      "long_pauses": "approximate",
      "fillers": "experimental"
    },
    "error": null
  }
}
```

`transcription.status` is `"success"` or `"failed"`, independent of the top-level
`status`. An empty `segments`/`text` with `status: "success"` means no speech was
detected — not a failure (see `docs/context.md` "No speech detected"). On failure,
`transcription.error` carries a structured `{code, message}` (never a raw
CTranslate2/PyAV exception) and `text`/`segments`/`words` are empty.

`metrics.status` is `"success"` or `"failed"`, independent of both `transcription.status`
and the top-level `status`. Metrics are computed only from a successful transcript — if
transcription failed, `metrics.status` is `"failed"` with error code
`TRANSCRIPT_UNAVAILABLE` (see M6B; this single-request architecture has no separate
metrics-only retry — retrying re-POSTs the same in-memory audio Blob and re-runs
transcription too, extending DEC-019's existing trade-off). `metrics.reliability` maps
each field name to one of `"exact" | "approximate" | "experimental"`
(`docs/decision-log.md` DEC-014/DEC-015) — the frontend must render the corresponding
label tier, never presenting an approximate/experimental value as exact.
`long_pauses[].observed_gap` is the gap between two Whisper word timestamps, **not a
measured acoustic silence duration** — see DEC-014.

**Upload-level validation errors** (reject the whole request — transcription never runs):

| Status | Code | Trigger |
|---|---|---|
| 400 | `AUDIO_FILE_MISSING` | No `file` field, or it has no filename |
| 400 | `AUDIO_EMPTY` | `file` has zero bytes |
| 415 | `UNSUPPORTED_CONTENT_TYPE` | Content type missing or not `audio/*` |
| 413 | `AUDIO_TOO_LARGE` | Upload exceeds `MAX_UPLOAD_BYTES` (25 MiB — DEC-018); may be
  caught either before parsing (declared `Content-Length`) or after reading the actual
  bytes |
| 422 | `VALIDATION_ERROR` | Malformed multipart request (e.g. `file` field absent
  entirely — FastAPI's own request validation) |
| 500 | `INTERNAL_ERROR` | Any unexpected server-side failure |

**Transcription-level failure codes** (embedded in `transcription.error.code`, HTTP
status stays `200` since the upload itself succeeded):

| Code | Trigger |
|---|---|
| `AUDIO_EMPTY` | Nothing to transcribe (defensive — upload validation already excludes this) |
| `MODEL_UNAVAILABLE` | The faster-whisper model failed to load |
| `TRANSCRIPTION_FAILED` | Audio decode failure (PyAV) or any other transcription/inference error |

**Metrics-level failure codes** (embedded in `metrics.error.code`, HTTP status stays
`200`):

| Code | Trigger |
|---|---|
| `TRANSCRIPT_UNAVAILABLE` | Transcription itself failed — metrics cannot be computed without a transcript |
| `INVALID_DURATION` | Recording duration is missing or negative (defensive — normal transcription always provides a valid duration) |
| `METRICS_CALCULATION_FAILED` | Any unexpected error in metrics computation (never a raw exception) |

#### STT Layer

- Defined behind an interface/abstraction (`backend/app/services/transcription/base.py`'s
  `TranscriptionService` Protocol) so the concrete implementation can be swapped, and so
  the API layer never touches model-loading/inference code directly.
- V1 default implementation (M5): `faster-whisper`
  (`backend/app/services/transcription/faster_whisper_service.py`), running locally,
  CPU-only (`base.en`/`cpu`/`int8` — see `decision-log.md` DEC-017 for why, resolved via
  a local benchmark in `experiments/m5_transcription/`).
- The model is loaded lazily (first real request, not at FastAPI startup) and reused
  across requests via a module-level singleton — never reconstructed per request.
- Audio is decoded directly from in-memory bytes via faster-whisper's own PyAV-based
  decoder — no ffmpeg subprocess, no temp files (WebM/Opus, WebM, Ogg/Opus, and MP4, per
  DEC-016, all decoded successfully in local testing).
- Segment-level timestamps in M5; word-level timestamps were evaluated and deliberately
  deferred at M5, re-evaluated and accepted at M6A (DEC-020), and **enabled in
  production code at M6B** (`word_timestamps=True` in
  `faster_whisper_service.py`). Measured overhead on a real local request: ~1.4%
  (1.897s → 1.924s on a ~15.6s real sample) — consistent with, and on the low end of,
  M6A's synthetic-sample average of ~7.5%.
- Alternative/experimental STT implementations (e.g. CrisperWhisper) must conform to the
  same interface but live in `experiments/`, not in the core backend path.

#### Speech Metrics Engine

- Pure deterministic Python logic. No LLM calls.
- **Implemented at M6B** (`backend/app/services/metrics/`), turning M6A's
  evidence-gathering (`experiments/m6_speech_metrics/`) into production behavior.
  Deliberately generic name (`SpeechMetricsService`, not "impromptu-specific") — see
  "Shared vs. mode-specific split" below.
- Computes: word count (`word_count.py`), approximate WPM (`wpm.py`), long-pause
  detection (`pauses.py`), filler detection (`fillers.py`), all orchestrated by
  `service.py`. **Does not compute repetition/restart detection** (still DEFERRED, per
  DEC/M6A — see below).
- **Duration** is **intentionally** sourced from `TranscriptionSuccess.duration_seconds`
  — the decoded duration of the actual audio artifact that was transcribed (via
  faster-whisper/PyAV) — not the browser's `MediaRecorder` elapsed timer, and not
  derived from transcript word content. See DEC-021 for the full A-vs-B reasoning.
  Metrics only run after a successful transcription in this architecture (see "API
  Contract" above — `metrics.status` is `"failed"` with `TRANSCRIPT_UNAVAILABLE` when
  transcription itself failed), so there is currently no scenario where duration is
  needed but transcription failed. The frontend's own client-measured
  `AudioRecording.durationSeconds` remains useful as **recording-session UI timing**
  (the live elapsed-time display during Recording, per DEC-009) but is **not**
  authoritative for metrics and is deliberately not sent to the backend for that
  purpose — this is a considered design choice (DEC-021), not an unresolved gap.
- **Pause detection** (`pauses.py`) uses word-level timestamp gaps (DEC-014's
  "Approach A"), threshold provisionally 1.0s. This is a **flag on Whisper's observed
  word-gap**, not a direct measurement of acoustic silence duration — `PauseEvent` has
  no `duration_seconds` field by design, only `observed_gap`, `previous_word_end`,
  `next_word_start`, `threshold`, and `method` (see `experiments/m6_speech_metrics/
  conclusions.md` "What this detector actually measures"). The Results UI shows
  "Long pause detected around M:SS", never a claimed duration.
- **Filler detection** (`fillers.py`) uses the exact DEC-015 vocabulary and
  context-sensitive policy (um/uh/ah/erm always filler; like/actually/basically only
  in discourse-marker position; "you know" as a phrase) — classified EXPERIMENTAL,
  never presented to the user without that qualification.
- **Reliability/provenance**: `MetricsSuccess.reliability` is a flat
  `{field_name: "exact"|"approximate"|"experimental"}` dict (`metrics/base.py`) —
  deliberately minimal, matching `experiments/m6_speech_metrics/conclusions.md` Step
  10's "do not over-engineer" guidance. The frontend (`MetricCard`) renders a visible
  badge for any non-`exact` reliability tier.
- **Shared vs. mode-specific split**: duration/transcript/word count/WPM/pauses are
  mode-independent "shared speech evidence"; filler detection is impromptu-speaking-
  specific "mode-specific evaluation." Reflected in the code only by naming
  (`SpeechMetricsService`, not `ImpromptuSpeechMetricsEngine`) — no mode-abstraction
  layer exists yet, since only impromptu speaking exists (see `experiments/
  m6_speech_metrics/conclusions.md` Step 9).
- Repetition/advanced disfluency detection remains **DEFERRED from V1** — not
  implemented, not planned until either a smarter restart heuristic or a different STT
  model is evaluated (`experiments/m6_speech_metrics/conclusions.md` EXP-M6-004).

### Experimental Models

Research-only models (e.g. CrisperWhisper, advanced disfluency detectors) live under
`experiments/` and are never imported by the core backend request path. They are promoted
into the core path only via an explicit decision recorded in `decision-log.md`, after
evaluation (see `context.md`).

### Current Performance Characteristics

Measured evidence lives in the experiment folders, not duplicated here — this section
is a pointer plus the current architectural implication, not a restatement of the
numbers.

- **Transcription latency:** `experiments/m5_transcription/conclusions.md` — RTF
  0.08–0.23 on synthetic samples, RTF≈0.083 on one real ~100s human recording
  (8.3s transcription time). **Implication:** no queueing/async job system is needed at
  V1's scale — the current synchronous request/response pattern (`POST
  /api/v1/attempts/audio` transcribes inline, DEC-019) stays well within an interactive
  budget.
- **Word-level timestamp overhead:** `experiments/m6_speech_metrics/conclusions.md`
  EXP-M6-001 measured average +7.5% across synthetic samples; re-measured on a real
  local request at M6B (~15.6s real audio, `conversational_pace` sample): 1.897s
  segment-only vs. 1.924s with word timestamps, **~1.4% overhead** — on the low end of,
  and consistent with, the M6A range. **Implication:** confirmed cheap enough for
  production (DEC-020).
- **Metrics-computation latency:** measured directly at M6B —
  `SpeechMetricsService.compute()` averaged **0.064ms** over 100 runs on real
  transcript/word data (58 words, 1 pause check, filler check). **Implication:**
  metrics add no meaningful latency beyond transcription itself; the ~1.9s
  end-to-end request time on a real local request is essentially all transcription.

**Future scaling triggers** (not implemented, named so they're recognizable if they
occur): concurrent multi-user processing would require replacing the current
in-process lazy-singleton model (see `docs/assumptions.md` ASSUMP-009) with a queue or
worker pool; a cloud deployment would need either GPU provisioning or a hosted STT API
to keep CPU-only latency acceptable at scale; recordings materially longer than the
~60–100s range actually measured so far would need fresh RTF evidence rather than
assuming linear scaling holds. See `docs/risks.md` for the risk-register framing of
related concerns.

## From the domain model

#### Transcript
The STT output for one `AudioRecording`. Composed of an ordered list of
`TranscriptSegment`s, plus the full joined text and measured metadata about the
transcription itself (`language`, `model`, `transcriptionSeconds` — added at M5).
Represents "what was said and when," produced by the STT layer — never authored or
altered by the coaching AI. The metadata is measured fact about the STT run (which model,
how long it took), not generated interpretation — kept alongside the segments rather than
on a separate entity since it describes this same transcription, not a different concept.
An empty `segments` list is a valid, successful `Transcript` — it means no speech was
detected (see `context.md` "No speech detected"), not a failure.

#### TranscriptWord
A single word-level timestamp: text, start time, end time. Segment-level timestamps
were the only granularity through M5; word-level timestamps were evaluated at M5
(deferred, no consumer yet), accepted at M6A (`decision-log.md` DEC-020), and **enabled
in production at M6B**, since pause detection (below) is now a real consumer. Word count
and filler detection also operate over this list, not the raw segment text.

#### SpeechMetrics
The deterministic analysis result for one `SpeechAttempt`, derived from its `Transcript`
(and `AudioRecording` duration). Includes: total duration, word count, WPM, a list of
`PauseEvent`s, and a list of `FillerOccurrence`s. Computed entirely by deterministic
Python logic — see `ai-boundaries.md`. **Implemented at M6B**
(`backend/app/services/metrics/`), turning M6A's design/experiment work
(`experiments/m6_speech_metrics/`) into production behavior. Not every metric here
carries equal confidence: duration is exact; word count and WPM are approximate
(inherit transcript error); pauses are approximate with a provisional threshold;
fillers are experimental; repetition/restart is not included at all (still deferred) —
see `experiments/m6_speech_metrics/conclusions.md` Step 1 and Step 14 for the full
per-metric classification and rationale, unchanged by the M6B implementation. Each
metric result carries a `reliability` map (`exact` | `approximate` | `experimental` per
field name) rather than being shown to the user without qualification (see that
document's Step 10-11).

#### PauseEvent
A candidate long pause inferred from a gap between two word timestamps, exceeding the
configured threshold. Has `previousWordEndSeconds`, `nextWordStartSeconds`,
`observedGapSeconds`, `thresholdSeconds`, and `method` — deliberately **no**
`durationSeconds` field, because the gap between Whisper word timestamps is **not a
verified measurement of true acoustic silence** (M6A's EXP-M6-002 found a 0.5s true
pause read as a 1.0s observed gap). Used as concrete evidence of a detected long pause
(e.g. "a long pause was detected before your second point"), not as an exact-duration
claim (never "you paused for exactly 3.4 seconds"). Detected via word-level timestamp
gaps, not audio-level VAD (VAD is blocked on this development machine — see
`decision-log.md` DEC-017/DEC-014). Threshold is provisional (1.0s), pending
real-human validation — see `experiments/m6_speech_metrics/conclusions.md`. (Named
`PauseEvent`, not `Pause`, specifically to avoid implying a measured duration.)

#### FillerOccurrence
A single detected instance of a known filler word/phrase (e.g. "um," "uh," "like"). Has
the matched `text`, the matched vocabulary `category`, and a start/end timestamp.
Aggregated counts feed into `SpeechMetrics`; individual occurrences feed into evidence
display. Detection uses context-sensitive matching (not every occurrence of an
ambiguous word like "like" or "actually" is a filler — see `decision-log.md` DEC-015)
and is classified experimental, not authoritative, pending a larger evaluation set than
M6A's 8 hand-labelled examples. **Implemented at M6B** exactly to DEC-015's
vocabulary/policy — not expanded during implementation.

#### ProcessingStatus
The state of a `SpeechAttempt`'s pipeline progression, modeled as **four independent
per-stage statuses**: `upload` (M4), `transcription` (M5), `metrics` (M6), and `coaching`
(M8). Each stage status is one of `pending` / `success` / `failed`, tracked independently.
This is deliberately coarser than a single combined pipeline state, because it must
represent partial failure — e.g. `upload: success`, `transcription: pending`,
`metrics: pending`, `coaching: pending` (the M4 state: audio received, nothing analyzed
yet) or `transcription: success`, `metrics: success`, `coaching: failed` (later
milestones) — without discarding or invalidating the earlier successful stages. This is
what makes the recovery principle in `context.md` representable in the domain, and what
the Processing/Results UI renders directly from (see `context.md`, "Processing Status
→ UI"). `upload` was added at M4 as a clean extension of this existing model rather than
inventing a new pipeline concept — see `decision-log.md` DEC-018.

### Design Notes

- `SpeechMetrics`, `PauseEvent`, and `FillerOccurrence` are always derived deterministically —
  they are never produced or modified by `CoachingFeedback`.
- `CoachingFeedback` and `RetryGoal` are the only entities in this model produced by AI
  interpretation; every other entity is either raw capture (audio), STT output
  (transcript), or deterministic computation (metrics).
- Absence is meaningful: a `SpeechAttempt` may legitimately have a `Transcript` and
  `SpeechMetrics` but no `CoachingFeedback` (coaching failed/unavailable) — this must be
  representable, not treated as an error state for the whole attempt.
- `AttemptComparison` is intentionally not a stored entity in V1 — treating it as a
  computed view avoids implying any persistence guarantee beyond the current in-memory
  session.
- `PracticeHistoryRecord` is the one persisted entity, and the boundary is deliberate:
  live session state (audio, transcript, metrics, coaching) stays in memory per DEC-010,
  while a completed session leaves behind only the small scalars a streak, a weekly total,
  and a future Practice History actually need (DEC-027).

## From the user flows

### Recovery Principle

**A failure in optional coaching must not destroy valid transcription or measured speech
results.** Transcript and deterministic metrics are computed and displayed independently
of whether the coaching (Gemini) call succeeds. Processing is treated as three
independently-failable stages — transcription, metrics, coaching — each with its own
pending/success/failed status (see `context.md`), not one atomic operation.

#### No speech detected
- Trigger: transcription returns an empty/near-empty transcript (e.g. silence, mic muted
  at the OS level).
- Behaviour: Results screen explains that no speech was detected and offers a direct
  re-record action; deterministic metrics are not computed on empty input (avoid
  divide-by-zero WPM etc.), and coaching is skipped with a clear "not enough evidence"
  message rather than being fabricated.

#### Transcription failure
- Trigger: STT service/process errors or times out.
- Behaviour: Audio remains available (playback still works). Results screen shows a
  transcription-failed state with a retry-processing action. Metrics and coaching, which
  depend on the transcript, are not computed and are clearly marked unavailable.

#### Metrics failure
- Trigger: deterministic metrics computation throws on otherwise-valid transcript data.
- Behaviour: Transcript is still shown. Metrics section shows a failure state distinct
  from "no speech detected." Coaching is not run against incomplete/invalid metrics.

## From the test plan

### AI Evaluation (future)

Once coaching is implemented (M8+), evaluate on:

- Groundedness (does feedback reference actual evidence?)
- Specificity (is feedback concrete, not generic?)
- Usefulness
- Actionability
- Clarity
- Unsupported-claim rate (rate of claims not backed by evidence — target: zero)

No scores or results exist yet; this section defines the evaluation dimensions only. Do
not fabricate results before evaluation is actually run.

### STT Evaluation (future, experimental)

For experiments comparing STT options (e.g. faster-whisper vs. CrisperWhisper, M12):

- Word Error Rate (WER)
- Filler preservation (does the STT model retain filler words, or clean them out?)
- Timestamp accuracy
- Latency

No scores or results exist yet for this M12 CrisperWhisper comparison; this section
defines the evaluation dimensions only. (M5 ran a small, provisional benchmark using
these same dimensions — WER, filler preservation, latency/RTF — to choose a
faster-whisper model size, not to compare against CrisperWhisper; see
`experiments/m5_transcription/conclusions.md` and `decision-log.md` DEC-017. That
benchmark's small local sample is not a substitute for the CrisperWhisper comparison
described here.)
