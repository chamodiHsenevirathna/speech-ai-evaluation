# Decision Log (excerpt)

This is an **excerpt** of the decision log kept for the SpeakLab application. It contains only the
13 decisions the experiments in this repository cite, copied verbatim apart from one redaction
(a speaker description was generalised to "non-native-accented"). Decisions about the UI,
design system, practice history and CI are omitted because nothing in the experiments depends
on them. File paths under `frontend/` or in backend modules not included here refer to the
SpeakLab application, not to this repository. Status labels such as **Provisional** and
**Accepted** are as recorded at the time and were not re-assessed.

---

## DEC-004

**Status:** Accepted

**Decision:** Use `faster-whisper` as the initial local STT baseline.

**Context:** Need timestamped transcription that runs locally without a paid API
dependency for the core V1 path.

**Alternatives considered:** OpenAI Whisper API (paid, network-dependent), CrisperWhisper
(research-only for now), cloud STT providers.

**Rationale:** Runs locally, no per-request cost, reasonably fast via CTranslate2, provides
segment-level timestamps.

**Trade-offs:** Local compute/model-download requirement; accuracy trade-offs vs. larger
cloud models, to be evaluated later (see `context.md` STT Evaluation).

**Consequences:** STT sits behind an interface (`context.md`) so alternatives can be
swapped/evaluated later without changing the rest of the pipeline.

---

## DEC-005

**Status:** Accepted

**Decision:** Keep deterministic analysis separate from generative AI coaching.

**Context:** Coaching must be evidence-grounded and must never fabricate measurable values
(see `ai-boundaries.md`).

**Rationale:** Separating layers (audio → transcription → deterministic analysis →
structured evidence → AI interpretation) makes it possible to guarantee the AI never
authors a number, and lets the app degrade gracefully when the AI layer fails.

**Trade-offs:** More structure/plumbing up front than piping audio straight into an LLM.

**Consequences:** Coaching service only ever receives structured evidence, never raw audio.

---

## DEC-006

**Status:** Accepted

**Decision:** Keep research-paper models (e.g. CrisperWhisper, advanced disfluency
detectors) optional and isolated in `experiments/` until evaluation justifies adoption.

**Context:** Research models are useful to explore but should not become undocumented,
unvetted dependencies of the normal V1 workflow.

**Rationale:** Keeps the core path stable and reproducible; experimentation is valuable but
must not silently become a production dependency.

**Trade-offs:** Slower path to adopting a potentially-better model, in exchange for
deliberate, evaluated adoption.

**Consequences:** Anything in `experiments/` must go through the evaluation described in
`context.md` and get an explicit decision-log entry before being promoted into
`backend/`.

---

## DEC-007

**Status:** Accepted

**Decision:** Use free/local-first infrastructure during initial portfolio development.

**Context:** This is currently a portfolio/validation project for a single user, not a
production service.

**Rationale:** Avoids unnecessary cost and cloud complexity while the product concept and
pipeline are still being validated.

**Trade-offs:** No persistence beyond a single local session in V1 until a storage
implementation is deliberately chosen (see `requirements.md`); not multi-user; not
deployed.

**Consequences:** No database implementation is committed to yet. No cloud accounts,
managed services, or paid infrastructure are required to run V1.

---

## DEC-009

**Status:** Accepted

**Decision:** 60 seconds is the target recording duration, but V1 does not hard-stop the
recording at 60s. Elapsed time is shown; the user stops recording manually. A hard cap may
be experimented with later.

**Context:** The original brief said "record approximately 60 seconds" without specifying
whether that's enforced.

**Alternatives considered:** Hard auto-stop at exactly 60s; no visible timer.

**Rationale:** A hard cutoff risks cutting a user off mid-sentence, which would corrupt the
practice experience and the evidence (e.g. an artificially truncated final segment).
Manual stop with a visible target keeps the user in control while still anchoring practice
around ~60s.

**Trade-offs:** Attempts may vary more in length than a hard cap would allow, which could
make attempt-1-vs-attempt-2 WPM comparisons slightly noisier if duration differs a lot
between attempts.

**Consequences:** `requirements.md` FR-04 and `context.md` reflect manual stop, no
auto-cutoff, and elapsed-time display. A future hard-cap experiment is not scoped in V1.

---

## DEC-014

**Status:** Provisional — resolved partially at M6A, final threshold pending
real-human validation

**Decision:** Long-pause detection uses **word-level timestamp gap inference**
("Approach A"), not VAD, with a **provisional** threshold of **1.0 second**.

**Context:** M0 review found conflicting placeholder values (2s in FR-12, 3s in a FR-15
example). M6A ran a controlled experiment (EXP-M6-002) comparing word-gap inference
against audio-level VAD, using synthetic samples with exactly-known injected pause
durations (0.5s/1.0s/2.0s/3.0s) plus a no-pause control.

**Experiment:** See `experiments/m6_speech_metrics/experiment_plan.md` EXP-M6-002 and
`results/pauses.json`.

**Result:** VAD (`vad_filter=True`) failed with the same onnxruntime/macOS ABI
incompatibility already found at M5 (DEC-017) — re-confirmed, not re-investigated for a
fix. Word-gap inference over `word_timestamps=True` output (see DEC-020) correctly
**flagged** every injected pause down to 0.5s, and produced zero false positives on the
control, at threshold values of 0.75s and 1.0s.

**Important correction (post-review re-check):** the detector flags a *threshold on the
observed word-gap*, not a direct measurement of true acoustic silence duration — these
are not the same number. Re-checking the raw data found the 0.5s injected pause
produced an observed word-gap of **1.00 seconds — exactly double the true silence**;
every other tested duration also overshot by a smaller relative amount. See
`experiments/m6_speech_metrics/conclusions.md` "What this detector actually measures"
for the full injected-vs-observed table. This does not change the flagging result
(both real pauses and the no-pause control were still classified correctly at every
tested threshold), but it means DEC-014 authorizes only a *presence/absence flag*
("a long pause was detected"), never a claimed duration ("you paused for exactly N
seconds").

**Rationale for provisional (not final) status:** the no-pause control's largest
natural gap (0.5s) is an artifact of macOS `say`'s sentence-boundary pausing behavior,
not representative of real human word-to-word or hesitation-pause timing — see
`experiments/m6_speech_metrics/conclusions.md` "Why DEC-014's threshold isn't a final
number." The **method** (word-gap inference, not VAD) is well-supported by this
evidence; the **specific 1.0s number** is not, until validated against real recorded
speech — and, per the correction above, even that validation must compare against
independently-measured true silence, not just against Whisper's own word-gap output.

**Consequences:** `requirements.md` FR-12 method is resolved (word-gap inference);
threshold remains provisional. `backend/app/services/transcription/
faster_whisper_service.py` will need `word_timestamps=True` enabled (DEC-020) before
this can be implemented. Not yet wired into production per M6A's explicit scope
(evidence-gathering only).

**M6B implementation note:** implemented in production as designed
(`backend/app/services/metrics/pauses.py`), still using the 1.0s threshold and
word-gap method with no changes. Implementation surfaced no contradiction with M6A's
evidence. **Status remains Provisional** — M6B did not add new real-human evidence, so
this is not upgraded to Accepted merely because it now ships in production code (see
`docs/methodology.md` "Research-integrity rules").

**M6B real-human validation note (2026-08-20):** a controlled real-human test (Test B,
see `experiments/m6_speech_metrics/real_human_validation_results.md`) with 2 scripted
pauses (~1s, ~2s) produced 3 detected word-gap events; the third had no known
intentional source and is treated as a possible false positive. This reinforces this
decision's existing framing — the detector flags a thresholded *word gap*, not a
measurement of acoustic silence — rather than contradicting it. One real-human sample
does not constitute the evaluation-set-scale evidence this decision still needs.
**Status remains Provisional.**

**M6 real-human validation note (2026-08-21, Test D):** a second controlled
real-human test (Test D, see `real_human_validation_results.md`) with one intentional
~3–5s pause produced exactly one detected event: `previous_word_end=28.30`,
`next_word_start=33.68`, `observed_gap=5.38` (33.68 − 28.30 = 5.38, arithmetically
confirmed) — a clean, unambiguous correct detection, with no extra/missed events.
This is a positive data point for the word-gap *method*, consistent with (not new
evidence beyond) the existing Provisional framing — still a single sample, and still
no independently-measured true-silence duration to compare `observed_gap` against
(per this decision's existing "Important correction"). **Status remains
Provisional.**

---

## DEC-015

**Status:** Provisional — resolved partially at M6A, final precision/recall claim
pending a larger evaluation set

**Decision:** Filler vocabulary: `um`, `uh` (normalizing for Whisper's observed `uh`→
`ah` rendering — see DEC-017/M5 — though M6B real-human testing also observed `uh`→
`um`, so more than one normalization form is possible and neither should be assumed
exclusive), `erm`, `like`, `you know`, `actually`, `basically`.
Detection policy: **context-sensitive matching**, not unconditional matching — "like",
"actually", and "basically" are only counted in discourse-marker position (comma/
sentence-boundary adjacent), not when used semantically/comparatively.

**Context:** V1 requires "basic filler detection" (FR-11) but the exact word list was
only ever illustrative ("um," "uh," "like"). M6A ran a controlled experiment
(EXP-M6-003) comparing unconditional matching against context-sensitive matching on 8
hand-labelled examples, including deliberately ambiguous uses of "like" and "actually."

**Experiment:** See `experiments/m6_speech_metrics/experiment_plan.md` EXP-M6-003 and
`results/fillers.json`.

**Result:** Unconditional matching: precision 0.667, recall 1.0, F1 0.8 (3 false
positives, all from semantic/comparative uses of ambiguous words, plus one from the
`uh`→`ah` normalization). Context-sensitive matching: precision 0.833, recall 0.833, F1
0.833 (1 false positive, 1 false negative from a rule that was too strict for a
mid-sentence hedge).

**Rationale for provisional (not final) status:** 8 examples is too small to support a
precision/recall claim shown to users as anything but experimental — see
`experiments/m6_speech_metrics/conclusions.md` Step 1 classification table (filler
detection is classified EXPERIMENTAL, not ACCEPTED). The vocabulary and policy
*direction* are decided with real evidence; the specific rule implementation has one
known documented gap (mid-sentence hedge case) not yet fixed.

**Consequences:** `requirements.md` FR-11 vocabulary/policy direction is resolved;
production-grade confidence is not yet established. Filler detection is shown to users
(once implemented) as "experimental," not "detected fillers" without qualification, per
`experiments/m6_speech_metrics/conclusions.md` Step 11 user-facing language guidance.
Not yet wired into production per M6A's explicit scope.

**M6B implementation note:** implemented in production
(`backend/app/services/metrics/fillers.py`) with the exact vocabulary above and the
**refined** context-sensitive rule DEC-015 already called for — comma-preceded OR
sentence-initial-and-comma-followed, not only sentence-initial — which closes the
mid-sentence-hedge gap EXP-M6-003 found (`filler_actually_hedge`). This closes a known
implementation gap, but does **not** constitute new precision/recall evidence at
scale (still one 8-example evaluation). **Status remains Provisional/EXPERIMENTAL** —
not upgraded by this fix, per `docs/methodology.md` "Research-integrity rules" (implementing a decision does
not itself justify upgrading it).

**M6B real-human validation note (2026-08-20):** three real-human tests (see
`experiments/m6_speech_metrics/real_human_validation_results.md`) produced mixed
evidence. Positive: initial "um" detected; spoken "uh" (transcribed as "um," not "ah")
still detected; semantic "looks like her sister" correctly suppressed (no false
positive); discourse "like" correctly detected even after Whisper altered surrounding
punctuation. Open questions: natural unscripted speech (Test A) appeared to contain two
untagged discourse uses of "like" with zero filler detections — a possible false
negative, not confirmed on a single unlabeled sample; "actually" fired exactly per this
decision's sentence-initial-and-comma-followed rule, but whether an adverb-of-degree
use of "actually" should count as a filler at all remains semantically ambiguous
regardless of rule-conformance. None of this evidence is at evaluation-set scale.
**Status remains Provisional/Experimental.**

**M6 real-human validation note (2026-08-21, Test D):** a fourth controlled
real-human test (Test D) with deliberately spoken "um"/"uh"/"like" and one
intentional pause produced an empty `fillers` array, traced to **two separable
failure modes**, not one:

- **Upstream:** neither "um" nor "uh" appears anywhere in `transcription.words` —
  consistent with (not newly contradicting) the possible-omission concern already
  raised by Test A. The detector had no token to act on either way.
- **Downstream, newly identified:** all three spoken "like" tokens *did* survive
  transcription, yet all three were rejected by `detect_fillers`'s context rule —
  traced in `fillers.py` to the rule's dependence on `preceded_by_comma`/
  `sentence_initial`, both of which require punctuation this specific transcript
  did not contain at all (zero commas or sentence-ending punctuation in the full
  output). This is a **previously undocumented structural gap**: DEC-015's original
  policy assumed faster-whisper reliably attaches punctuation to tokens (true in
  Test B's script), but Test D shows that assumption doesn't hold on all real
  speech. Per-occurrence tracing found one occurrence clearly filler-like and
  rejected only by this punctuation gap, one plausibly semantic and correctly
  suppressed by the existing `_COMPARISON_VERBS` rule regardless of punctuation
  ("feel like"), and one clearly filler-like and missed by a second, distinct gap —
  `_is_sentence_initial` has no awareness of a pause/segment boundary as a
  discourse boundary, even though this occurrence immediately followed a detected
  5.38s pause. Full per-occurrence reasoning is in
  `real_human_validation_results.md` Test D.

This is real evidence of an additional, specific failure mode beyond what M6A/Test A
found — not a scale-level precision/recall claim, and not yet a scoped fix (see the
follow-up experiment recommended in `real_human_validation_results.md`, which is
designed to separate upstream STT recall from downstream rule precision/recall
before any rule change is made). **Status remains Provisional/Experimental** — this
finding argues for further evidence-gathering, not for immediately patching the
punctuation-dependent rule without knowing how much of the problem it actually
explains.

---

## DEC-016

**Status:** Accepted (resolved at M3)

**Decision:** Select the recording MIME type at runtime via
`MediaRecorder.isTypeSupported`, preferring `audio/webm;codecs=opus`, falling back
through `audio/webm`, `audio/ogg;codecs=opus`, `audio/mp4`, and finally the browser's own
default (no `mimeType` passed to `MediaRecorder`) if none of those are supported. See
`frontend/src/media/audioFormat.ts`.

**Context:** Recording format affects both the frontend `MediaRecorder` configuration and
what the backend/faster-whisper needs to accept or transcode. M3 required inspecting
actual `MediaRecorder` support rather than assuming a format.

**Alternatives considered:**
- Hard-coding `audio/webm;codecs=opus` unconditionally — rejected: Safari does not
  support WebM at all, so a hard-coded value would throw in `new MediaRecorder(stream, {
  mimeType })` on Safari with no fallback.
- Recording as WAV/PCM directly in the browser (e.g. via `AudioWorklet`) to sidestep
  container/codec questions entirely — rejected as unnecessary complexity for V1; adds a
  custom encoding pipeline in the browser for a problem `MediaRecorder` already solves.

**Rationale:**
- `audio/webm;codecs=opus` is broadly supported (Chrome, Firefox, Edge), compact, and
  good quality for speech at low bitrates — a good default for a browser-recorded
  practice clip.
- `audio/webm` (no explicit codec) and `audio/ogg;codecs=opus` are close fallbacks for
  browsers that recognize the container but not the exact codec string.
- `audio/mp4` is included specifically for Safari, which supports neither WebM nor Ogg
  containers for `MediaRecorder`.
- Feature-detecting via `MediaRecorder.isTypeSupported` (rather than hard-coding) means
  the app degrades gracefully instead of throwing in `new MediaRecorder()` on an
  unsupported combination; the final fallback (no `mimeType` option at all) still lets
  `MediaRecorder` pick its own working default when none of the candidates match, so
  recording never hard-fails purely over format selection.
- The actual runtime-negotiated MIME type (`MediaRecorder.mimeType`, not just our
  candidate string) is what gets stored, since the browser may resolve our requested type
  to something slightly different.

**Trade-offs:**
- The captured container/codec is not fully predictable ahead of time — it depends on the
  user's browser. The backend (M4/M5) must accept whichever of the above containers
  arrives, rather than assuming a single format.
- No sample-rate/bitrate control is exercised at this layer; `MediaRecorder` uses its
  defaults.

**Implications for later faster-whisper ingestion (M5):** faster-whisper's typical input
path relies on `ffmpeg`/`av`-based decoding, which handles WebM/Opus, Ogg/Opus, and MP4
containers natively — so any of the four candidates above should be decodable without
frontend involvement. The FastAPI backend will still need an explicit
decode/normalize-to-PCM step before handing audio to faster-whisper; the exact mechanism
(ffmpeg subprocess vs. a Python decoding library) is a backend decision for M4/M5, not
resolved here.

**Consequences:** `frontend/src/media/audioFormat.ts` implements the selection;
`frontend/src/media/useAudioRecorder.ts` uses it when constructing `MediaRecorder` and
stores the negotiated MIME type on `AudioRecording.mimeType`. `requirements.md` FR-04 no
longer lists this as deferred.

---

## DEC-017

**Status:** Accepted (resolved at M5)

**Decision:** Default faster-whisper configuration is **`base.en`, `device=cpu`,
`compute_type=int8`**, overridable via `WHISPER_MODEL_SIZE`/`WHISPER_DEVICE`/
`WHISPER_COMPUTE_TYPE` environment variables (see `.env.example`,
`backend/app/config.py`).

**Context:** DEC-004 chose faster-whisper as the STT baseline but did not pick a
specific model size/device. M5 required resolving this with an evidence-based local
benchmark rather than an arbitrary choice.

**Experiment:** See `experiments/m5_transcription/` (hypothesis → experiment → result →
decision, with `results/results.csv` and `results/results.json`). Compared `tiny.en` vs
`base.en` (both CPU, int8) on 5 short local samples. `small.en` was deliberately not
downloaded — both smaller candidates already had ample latency headroom and
near-identical accuracy on the (too-clean, synthetic) samples available, so a third,
~3x-larger download wouldn't have added evidence the samples could actually reveal.

**Environment finding (also applies beyond this decision):** no CUDA (Apple Silicon has
no NVIDIA GPU) and CTranslate2 has no Apple Metal/Neural-Engine backend as of the
version tested — CPU is the only viable device on this class of machine, not a choice
made for convenience. Separately, this sandboxed environment's default Python (3.14) and
macOS version (13.0) could not install faster-whisper's dependency chain at all — see
`backend/README.md` for the Python-version constraint this imposes locally, and
`experiments/m5_transcription/conclusions.md` for a further onnxruntime/VAD-specific
ABI incompatibility discovered on this exact machine (macOS 13.0 vs. the wheel's 13.4
baseline) that disables VAD filtering here specifically (not a reason for the model
choice itself, but relevant to anyone reproducing this experiment).

**Rationale:** Both candidates comfortably clear the latency bar for an interactive
~60s clip (RTF 0.08–0.23 measured). Since latency isn't the constraint either way, the
more accurate option is preferred for real (non-synthetic, potentially accented) speech
— the actual product need. `base.en`'s ~141 MB download is still appropriately small for
a local-first single-user tool (DEC-007).

**Quality vs. latency trade-off:** `base.en` measured up to ~1.8x `tiny.en`'s
transcription time in this data, but both stay well under 15s for a full ~60s clip —
acceptable for a non-real-time practice workflow.

**Limitations:** Evidence is from 5 short TTS-synthesized samples (no real microphone
was available in this environment — see `experiments/m5_transcription/README.md`), one
machine, no accented speech (a non-native-accented English sample was requested by the
M5 task but could not be produced here). This is treated as sufficient to unblock M5 with
a reasoned, evidence-based default — not as a definitive model benchmark. If real-user
recordings later suggest a different trade-off, that should be a new decision entry, not
a silent change.

**Consequences:** `backend/app/config.py` reads `WHISPER_MODEL_SIZE`/`WHISPER_DEVICE`/
`WHISPER_COMPUTE_TYPE` from the environment with these resolved defaults; `.env.example`
values are no longer placeholders.

---

## DEC-018

**Status:** Accepted

**Decision:** Set a provisional maximum audio upload size of **25 MiB** (25 × 1024 × 1024
bytes) at `POST /api/v1/attempts/audio`. Uploads over this limit are rejected with
`413 Payload Too Large` and error code `AUDIO_TOO_LARGE`, enforced twice: a fast-path
check of the declared `Content-Length` header before the body is parsed
(`backend/app/middleware.py`), and an authoritative check of the actually-read byte count
after upload (`backend/app/services/audio_validation.py`).

**Context:** M4 needed a concrete, conservative safety limit for local-development audio
uploads appropriate for a browser recording of roughly one minute of speech (per FR-04's
~60s target, with no hard stop per DEC-009, so recordings can run somewhat longer).

**Alternatives considered:**
- A tight limit close to the expected clip size (e.g. 5 MiB) — rejected: too little margin
  for browsers/codecs that negotiate a higher-bitrate fallback (see DEC-016), or for a user
  who keeps talking well past 60s since there's no hard stop.
- No limit at all — rejected: an unbounded upload is an easy way to exhaust local
  memory/disk for no product benefit at V1's single-user local scale.
- A large "production-scale" limit (e.g. 500 MiB+) — rejected per this task's explicit
  instruction not to invent infrastructure-scale limits; V1 has exactly one use case
  (a short spoken clip), not general file upload.

**Rationale:** `audio/webm;codecs=opus` (DEC-016's preferred format) typically encodes
speech at well under 128 kbps, so even several minutes of audio stays in the low
single-digit megabytes. 25 MiB gives generous headroom — roughly 25-40x a realistic
~60-90 second clip at typical Opus bitrates, or several minutes of audio even at a
higher-bitrate MP4/AAC fallback — while still being a small, clearly-bounded number
appropriate for a local single-user dev tool, not a production media-upload service.

**Trade-offs:** The limit is a guess bounded by reasoning about typical bitrates, not
measured against real recordings. It may need revisiting once real usage (or the M12
CrisperWhisper/model experiments) shows different audio characteristics.

**Consequences:** `backend/app/config.py` defines `MAX_UPLOAD_BYTES`. Rejections return a
structured `{"error": {"code": "AUDIO_TOO_LARGE", "message": "..."}}` body, never a raw
framework/server error page. See `docs/context.md` for the full endpoint contract.

---

## DEC-019

**Status:** Accepted

**Decision:** `POST /api/v1/attempts/audio` (the existing M4 upload endpoint) now also
runs transcription synchronously and returns it embedded in the same response, rather
than adding a second endpoint. Upload-level failures (missing/empty/oversized/
unsupported file) still reject the whole request as before; once the upload itself is
valid, a transcription failure is reported inside the response body
(`transcription.status: "failed"`) without rejecting the request.

**Context:** M5 needed to decide whether to extend the existing endpoint or add a
dedicated transcription endpoint, and explicitly to avoid a duplicate upload if the
current request can reasonably transcribe the audio during the same operation.

**Alternatives considered:**
- A separate `POST /api/v1/attempts/{id}/transcribe` endpoint operating on
  already-uploaded audio — rejected: since no audio is persisted server-side (DEC-018),
  this would require either re-uploading the bytes anyway (no real benefit over
  extending the existing endpoint) or introducing server-side audio caching keyed by
  attempt id (new persistence/state complexity not justified for V1).
- Making transcription failure also fail the whole HTTP request (e.g. a non-2xx status)
  — rejected: this would force the frontend to treat "upload succeeded, transcription
  failed" the same as "upload failed," which the M5 task explicitly says not to do (the
  UI must distinguish these).

**Rationale:** One request/response covers both stages the frontend needs to observe.
The per-stage `ProcessingStatus` (`upload`, `transcription`) already models these as
independent concerns at the domain level (see `context.md`); this decision is about
the wire-level request shape, not the domain model, which is unaffected.

**Trade-offs:** "Retry transcription" (per M5 requirement 9) is implemented by
re-POSTing the same in-memory audio Blob to this same endpoint — which re-runs upload
validation too, not literally "transcription only." This still satisfies the actual
requirement (**no re-recording is needed** — the frontend still has the Blob in memory
per DEC-010/FR-20), just not via a narrower "transcription-only" request.

**Consequences:** See `docs/context.md` "API Contract" for the full request/response
shape. `frontend/src/screens/ProcessingScreen.tsx`'s retry action re-calls the same
upload function for both upload and transcription failures.

---

## DEC-020

**Status:** Accepted (revised at M6A — supersedes the M5 "not enabled" decision below)

**Decision:** Word-level timestamps (`word_timestamps=True`) **are now enabled** for
M6+, now that pause detection (DEC-014) is a real consumer of them.

**Context (M5):** M5 required investigating whether to enable faster-whisper's
word-level timestamp option (useful for M6's future pause detection) versus deferring
it. At M5, nothing yet consumed word-level timing, so it was left off — see the
original M5 rationale below, preserved for history.

**Context (M6A):** M6A re-ran this experiment (EXP-M6-001) now that pause detection
(DEC-014) actually needs word-level granularity, and additionally verified timestamp
*plausibility* against known injected pauses, not just latency cost.

**Experiment:** See `experiments/m6_speech_metrics/experiment_plan.md` EXP-M6-001 and
`results/word_timestamps.json`. Ran `base.en`/cpu/int8 against 10 samples (5 from M5, 5
new pause samples with exactly-known silence intervals), with and without
`word_timestamps=True`.

**Result:** Latency overhead ranged -3.0% to +27.1% across samples, average +7.5% —
consistent with M5's single-sample ≈11% estimate. Transcript text was identical with
the flag on or off in every case (the flag only adds metadata). On all 4 real injected
pauses, the largest detected inter-word gap correctly overlapped the known pause
interval; on the no-pause control, it correctly did not.

**Rationale:** The original M5 rationale (don't enable an unused flag) no longer
applies — DEC-014 (pause detection) is a real, scoped consumer as of M6A. The measured
cost remains small in absolute terms, and this experiment additionally confirmed the
timestamps are plausible enough to be useful, not just cheap enough to afford.

**Trade-offs:** The response contract will need to expose word-level data when pause
detection is actually implemented in production code (not yet done — M6A is
evidence-gathering only, see `experiments/m6_speech_metrics/README.md`).

**Consequences:** `backend/app/services/transcription/faster_whisper_service.py` does
not yet pass `word_timestamps=True` in production code — this decision authorizes doing
so when pause detection is implemented (M6B or later), not immediately at M6A.

**M6B implementation note:** `word_timestamps=True` is now passed in production
(`faster_whisper_service.py`), and `TranscriptWordResult`/`TranscriptWordSchema` expose
`{text, start_time, end_time}` to the frontend. Re-measured overhead on a real local
request (`conversational_pace`, ~15.6s): 1.897s → 1.924s, **~1.4%** — on the low end
of, and consistent with, the ~7.5% average measured at M6A. **Status remains
Accepted** (unchanged; this is the decision's intended implementation, not a new
decision).

---

### Original M5 decision (superseded, preserved for history)

**Status:** Accepted (M5) — see revision above

**Decision:** Word-level timestamps (`word_timestamps=True`) are **not** enabled in M5.
Transcription continues to return segment-level timestamps only.

**Context:** M5 required investigating whether to enable faster-whisper's word-level
timestamp option now (useful for M6's future pause detection) versus deferring it.

**Experiment:** Measured cost on a ~15.6s sample:  ≈11% additional transcription time
(2.02s vs. 1.82s) when enabled — see `experiments/m5_transcription/conclusions.md`.

**Rationale:** M5's scope explicitly excludes pause/filler detection, so nothing in this
milestone would consume word-level timing if it were enabled now. Turning on an unused
flag would add latency and API-contract surface with no observable benefit today,
contrary to this project's established practice of adding fields/capabilities only when
justified by actual implementation (see `context.md`'s design notes).

**Trade-offs:** M6 will need to flip this on and extend the response contract to expose
word-level data — this is a known, small, already-measured future cost, not a surprise.

**Consequences:** `backend/app/services/transcription/faster_whisper_service.py` does not
pass `word_timestamps=True`. Revisit when M6 (pause detection) is scoped; the ~11%
overhead measured here should inform that decision rather than being re-measured from
scratch.

---

## DEC-021

**Status:** Accepted

**Decision:** The authoritative recording-duration source for speech metrics (FR-08,
and the WPM denominator for FR-10) is **the decoded duration of the actual audio
artifact that was transcribed** (`TranscriptionSuccess.duration_seconds`, sourced from
faster-whisper/PyAV's container decode) — **not** the frontend's client-observed
`MediaRecorder` elapsed-time timer (`AudioRecording.durationSeconds`).

**Context:** M6A's design work (`experiments/m6_speech_metrics/conclusions.md` Step 2)
already reasoned that duration should come from the audio itself, not the transcript —
but didn't explicitly compare it against the frontend's own elapsed-time timer as an
alternative candidate, since M6A did no implementation. M6B's implementation used the
decoded-audio value without stating this comparison as a decision, which read (in the
M6B report) as an unresolved gap rather than an intentional choice. This entry corrects
that framing and formalizes the choice as a decision, matching the project's practice
of giving every implemented architectural choice affecting a requirement its own entry
(cf. DEC-014 for pause method, DEC-015 for filler policy).

**Alternatives compared** (A: client-observed `MediaRecorder` elapsed duration, vs. B:
decoded audio-container duration). **No paired side-by-side numeric measurement of A
vs. B was captured for this comparison** — both are architecturally well-understood
quantities and the reasoning below is based on how each is produced, not on a
measurement run that didn't happen; no comparison numbers are fabricated here.

- **Correspondence to the exact audio actually transcribed:** B is *by construction*
  the duration of the exact bytes that were decoded and transcribed — the word count
  (FR-09) and the duration denominator both describe the same analyzed artifact. A is
  produced independently, client-side, before encoding/upload, and is not guaranteed to
  equal the final encoded artifact's duration.
- **Measurement consistency / timer drift:** A is a `setInterval`-driven whole-second
  counter (`frontend/src/media/useAudioRecorder.ts`) — `setInterval` is not guaranteed
  to fire precisely on schedule if the main thread is busy, and the counter has
  1-second resolution. B is derived from the container's own sample count/sample rate
  at decode time — a property of the encoded media, not a wall-clock measurement, so it
  has no comparable drift/resolution concern.
- **Recorder startup/shutdown effects:** A starts counting when `recorder.start()` is
  called and stops when the `onstop` callback fires — both are async browser
  operations with their own (unmeasured, browser-dependent) latency, which could
  introduce a small, variable offset between "the timer's idea of duration" and
  "the audio actually captured." B has no such concern, since it measures the audio
  container after the fact, once fully formed.
- **Implementation complexity:** B requires no new plumbing — `duration_seconds` was
  already returned by the transcription service since M5. A would require adding a new
  form field, wiring it through the upload request, extending the API contract, and
  deciding a fallback/reconciliation rule for when the two values disagree — real
  added complexity for a value B already provides for the one thing it's needed for
  (the WPM denominator).
- **Future portability:** B is already part of the `TranscriptionService` Protocol's
  contract (`TranscriptionOutcome.duration_seconds`), so any future STT backend swap
  (e.g. a CrisperWhisper evaluation, M12) must already provide it — no new coupling is
  introduced by depending on it. A would add a second, independent duration source that
  every future STT backend swap would still need to be reconciled against.

**Rationale:** B is the more defensible authoritative source specifically because it
keeps the WPM numerator (word count, from the transcript) and denominator (duration)
referring to the *same analyzed artifact* — using A would introduce a second,
unrelated source of measurement noise (timer granularity, async start/stop latency)
into a metric that is already labeled approximate for transcript-accuracy reasons,
conflating two different kinds of imprecision under one "approximate" label.

**What A remains useful for:** `AudioRecording.durationSeconds` is still exactly right
for its existing purpose — the live elapsed-time display during Recording (DEC-009) —
which is session/UI timing, not a metrics input. No change to that usage.

**Trade-offs:** Duration remains unavailable if transcription itself fails (decode
failure), same as before this decision — M6A's Step 2 conclusion (an independent
decode-duration probe decoupled from transcription success) is not implemented here;
this decision only resolves *which* duration source is authoritative when metrics do
run, not the separate question of decoupling duration availability from transcription
success. That remains an open item, not silently dropped.

**Consequences:** `docs/context.md` "Speech Metrics Engine" updated to state this
as an intentional design choice, not a gap. No code change required — the M6B
implementation already used decoded-audio duration; this entry formalizes why.

---

