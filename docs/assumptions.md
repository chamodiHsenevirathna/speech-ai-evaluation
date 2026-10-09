# Assumptions

Important assumptions this project currently rests on, extracted from scattered
mentions across `docs/requirements.md` and `docs/decision-log.md` into one place. These
are **assumptions, not requirements** — do not promote one into `requirements.md`
without an explicit product decision; do not treat "Status: holds" as permanent proof,
only as "not yet contradicted by evidence."

---

### ASSUMP-001

**Assumption:** SpeakLab runs for a single local user at a time, with no concurrent
requests to the backend.

**Reason:** V1 is explicitly scoped as a local single-user tool (`docs/requirements.md`
"Target User"), not a hosted multi-user service.

**Impact if wrong:** The backend's module-level lazy-singleton model
(`backend/app/services/transcription/faster_whisper_service.py`) has no locking —
concurrent requests during model load could race. No queue or worker pool exists.

**Validation method:** Would surface immediately as a bug report or crash under any
real concurrent load; not proactively tested.

**Status:** Holds — no concurrent-access code path exists to contradict it.

**Relevant decisions:** DEC-007, DEC-010.

---

### ASSUMP-002

**Assumption:** V1 is English-first — the configured Whisper model (`base.en`) is
English-only.

**Reason:** `WHISPER_MODEL_SIZE=base.en` (`backend/app/config.py`, `.env.example`),
resolved by the DEC-017 benchmark, which only evaluated English samples.

**Impact if wrong (i.e. if multilingual support is needed):** Would require re-running
DEC-017's benchmark against a multilingual model variant (e.g. `base` instead of
`base.en`), since accuracy/latency trade-offs may differ.

**Validation method:** Not tested against any non-English input.

**Status:** Holds — no non-English requirement exists in `docs/requirements.md`.

**Relevant decisions:** DEC-004, DEC-017.

---

### ASSUMP-003

**Assumption:** A browser refresh or tab close during an unfinished practice session is
an acceptable data loss, not a bug to prevent.

**Reason:** No backend database or session store exists (DEC-007); `PracticeSession`
state lives only in frontend memory (DEC-010).

**Impact if wrong (i.e. if users find this unacceptable):** Would require a persistence
decision (backend session store, `localStorage`, or a real database) — explicitly
deferred, not accidental.

**Validation method:** Would surface as user complaints/feedback once real users exist;
not something automated tests can validate (it's a deliberate design trade-off, not a
defect).

**Status:** Holds, explicitly accepted — see `docs/context.md`
(the failure semantics) for how an unfinished session is handled.

**Relevant decisions:** DEC-010. **Relevant requirement:** FR-20.

---

### ASSUMP-004

**Assumption:** The backend runs on laptop-class CPU hardware, with no GPU required or
assumed available.

**Reason:** Apple Silicon (the only hardware tested, per DEC-017) has no CUDA, and
CTranslate2 has no Metal/Neural-Engine backend as of the version used — CPU inference
is the only option on this hardware, not a convenience choice.

**Impact if wrong (i.e. deployed to a lower-power device, or a device where CPU
inference is too slow):** Transcription RTF could exceed what's usable in an
interactive workflow; would need a device/compute-type re-evaluation (already
overridable via `WHISPER_DEVICE`/`WHISPER_COMPUTE_TYPE` env vars without a code
change).

**Validation method:** Only one machine tested (Apple M1, macOS 13.0) — see
`experiments/m5_transcription/README.md` "Environment this ran on."

**Status:** Holds for the one environment tested; unverified elsewhere.

**Relevant decisions:** DEC-017.

---

### ASSUMP-005

**Assumption:** `base.en`/`cpu`/`int8` is provisionally sufficient accuracy/latency for
real (non-synthetic) speech, including accented speech.

**Reason:** DEC-017's benchmark used only synthetic TTS samples; one ad hoc real-human
non-native-accented recording (M5) partially supports this (RTF≈0.083, content broadly
captured) but also found "several meaningful lexical transcription errors."

**Impact if wrong:** DEC-017 would need revisiting with broader real-user evidence,
potentially favoring a larger model despite the latency cost.

**Validation method:** `experiments/m6_speech_metrics/real_human_validation_checklist.md`
exists specifically to gather more of this evidence.

**Status:** Provisional — one supporting data point, not conclusive.

**Relevant decisions:** DEC-017.

---

### ASSUMP-006

**Assumption:** Synthetic (TTS-generated, `ffmpeg`-injected-silence) audio is an
adequate proxy for real human speech timing when evaluating pause/filler/repetition
detection.

**Reason:** No microphone is available in the sandboxed development environment used
for M5/M6A experiments.

**Impact if wrong:** DEC-014's provisional 1.0s pause threshold and DEC-015's filler
vocabulary/policy could both be miscalibrated for real speech — already explicitly
flagged as the reason both remain "Provisional," not "Accepted."

**Validation method:** `experiments/m6_speech_metrics/real_human_validation_checklist.md`.

**Status:** Known-imperfect proxy, explicitly acknowledged, not yet validated against
real speech.

**Relevant decisions:** DEC-014, DEC-015.

---

### ASSUMP-007

**Assumption:** The user's browser supports `MediaRecorder`/`getUserMedia` and at least
one of the negotiated audio containers (WebM/Opus, WebM, Ogg/Opus, MP4, or the
browser's own `MediaRecorder` default).

**Reason:** DEC-016's format-negotiation logic assumes at least one candidate (or the
browser's own fallback) works; FR-18/DEC-011 handle the case where none of
`MediaRecorder`/`getUserMedia` exist at all, but not a browser that has them yet
supports zero usable audio containers (currently believed to not exist among major
browsers).

**Impact if wrong:** A browser with `MediaRecorder` present but no usable container
would likely throw inside `new MediaRecorder()` uncaught, since DEC-016's fallback
chain assumes the final "no explicit mimeType" option always works.

**Validation method:** Manual testing across major browsers (Chrome, Firefox, Safari,
Edge) — see `docs/decision-log.md` DEC-016; not automated/continuously verified.

**Status:** Holds for the major browsers implicitly targeted; not exhaustively tested.

**Relevant decisions:** DEC-016. **Relevant requirement:** FR-04, FR-18.

---

### ASSUMP-008

**Assumption:** ~60 seconds is the expected/typical recording length; no hard cap is
enforced, so recordings could run materially longer.

**Reason:** DEC-009 (manual stop, no auto-cutoff at 60s, to avoid cutting a user off
mid-sentence).

**Impact if wrong (i.e. users routinely record much longer than 60s):** M5/M6A's
latency evidence (RTF measured on samples up to ~100s) may not generalize; the 25 MiB
upload limit (DEC-018) assumes typical Opus bitrates for a roughly-minute-scale clip
and could become binding for much longer recordings.

**Validation method:** Not enforced or monitored; would need real usage data.

**Status:** Holds as a target, not a constraint — genuinely unbounded in practice.

**Relevant decisions:** DEC-009, DEC-018.

---

### ASSUMP-009

**Assumption:** No production-scale concurrency is required, so a single in-process,
lazily-loaded model singleton is an adequate architecture.

**Reason:** Same single-user premise as ASSUMP-001, stated separately here because it
specifically shapes the transcription service's implementation
(`faster_whisper_service.py`'s module-level `_model` global), not just general backend
behavior.

**Impact if wrong:** Would need a queue, worker pool, or per-request model isolation —
a genuine architecture change requiring the project's architecture-change rule (see `docs/methodology.md`).

**Validation method:** None — not load-tested.

**Status:** Holds; no evidence against it.

**Relevant decisions:** DEC-007.

---

### ASSUMP-010

**Assumption:** All callers of the backend are trusted local processes (the Vite dev
server's origin specifically) — no authentication or rate limiting is needed.

**Reason:** CORS is a small explicit allowlist (`localhost:5173`/`127.0.0.1:5173`), not
a wildcard, and the backend is never exposed beyond `localhost` in V1.

**Impact if wrong (i.e. the backend is ever exposed on a network or deployed):** Would
need authentication, rate limiting, and a production CORS policy; none of that is in scope for this research repository.

**Validation method:** None needed while true; the CORS allowlist itself is the
enforcement mechanism, not a separately-tested assumption.

**Status:** Holds by construction — the backend is not bound to any non-localhost
interface in current configuration.

**Relevant decisions:** DEC-007.
