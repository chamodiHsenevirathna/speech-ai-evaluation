# Requirements

## Purpose

SpeakLab is a local-first, AI-assisted impromptu speaking practice application. V1 is a
**local web application** (React + TypeScript + Vite frontend, Python + FastAPI backend)
run on `localhost` during development — not a mobile app. The purpose of V1 is to validate
the product experience and speech-analysis pipeline before deciding whether a mobile app
is necessary.

## Target User (V1)

A single person practicing impromptu speaking independently on their own computer, in a
local development environment. No multi-user accounts, no authentication, no cloud
deployment.

## Core Product Loop

```text
Prompt → Preparation countdown → Record (~60s) → Transcribe → Calculate metrics
       → Show evidence → Generate evidence-grounded coaching → Provide one retry goal
       → Retry same prompt → Compare attempts
```

The product must help the user answer:

1. Where did I struggle?
2. What speaking behaviour caused the problem?
3. What should I focus on during my next attempt?
4. Did the retry improve?

## V1 Scope — In

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|----------------------|
| FR-01 | Local web interface served on `localhost` | Validate product experience without mobile complexity | App loads at `http://localhost:5173`; no native/Expo runtime required |
| FR-02 | Prompt display | User needs a speaking topic to begin practice | A prompt is visibly rendered on the Home/Practice screen before recording starts |
| FR-03 | Preparation countdown | Impromptu speaking requires a bounded prep window before speaking | A visible countdown defaulting to 15 seconds runs after prompt selection and before recording is enabled; user may skip the countdown to start recording immediately; user may cancel the countdown and return to Home (see DEC-008) |
| FR-04 | Microphone recording from the browser | Core input capture mechanism, avoids native app requirement | Browser `MediaRecorder`/`getUserMedia` captures audio; 60 seconds is the target practice duration but V1 does not hard-stop recording at 60s; elapsed recording time is shown to the user; recording is stopped manually by the user; permission-denied and device-unavailable states are handled (see `context.md`); a hard cap may be experimented with later (see DEC-009) |
| FR-18 | Unsupported browser handling | Some browsers/environments lack `MediaRecorder`/`getUserMedia` support; failing silently would strand the user with no explanation | On load (or on attempting to record), the app detects missing browser audio-recording support and shows an explicit "recording is not supported in this browser" state rather than a silent or generic failure (see `context.md`) |
| FR-19 | Retry coaching independently | Coaching (Gemini) may fail while transcript/metrics remain valid; the user should not have to re-record to retry only the coaching step | When coaching is marked unavailable, the Results screen offers a "retry coaching" action that re-runs only the coaching step against the existing transcript/metrics for that attempt |
| FR-20 | In-session attempt availability | Attempt 1's data must remain available through the retry and comparison flow without a database | `PracticeSession` and its `SpeechAttempt`s (including attempt 1) are held in frontend application memory for the duration of the session, so attempt 1 remains available while the user records attempt 2 and views the comparison (see DEC-010) |
| FR-05 | Audio playback | User should be able to review their own recording | Recorded audio can be played back in-browser after recording stops |
| FR-06 | Speech submission for processing | Recorded audio must reach the backend for analysis | Audio is uploaded to the FastAPI backend via HTTP; upload success/failure is surfaced to the user |
| FR-07 | Timestamped transcription | Evidence-grounded coaching requires knowing *when* things were said | Backend returns a transcript with segment-level timestamps (start/end) |
| FR-08 | Speaking duration | Deterministic input to WPM and pacing evidence | **Implemented at M6B.** Backend computes total recording duration from the audio (container-decoded duration, not the transcript), in seconds. Classified exact. |
| FR-09 | Word count | Deterministic input to WPM | **Implemented at M6B.** Backend computes total word count from the transcript (letters/digits/apostrophes tokenization). Classified approximate (inherits transcript error). |
| FR-10 | Words per minute (WPM) | Core pacing metric | **Implemented at M6B.** Backend computes WPM = word count / (total recording duration in minutes), deterministically, without LLM involvement. Classified approximate. |
| FR-11 | Basic filler detection | Identifies a known, measurable speaking behaviour | **Implemented at M6B** using the vocabulary/policy provisionally established at M6A (see decision-log.md DEC-015) — still classified EXPERIMENTAL, not upgraded by implementation; pending real-transcript validation |
| FR-12 | Long-pause detection | Pauses are concrete, measurable evidence of struggle points | **Implemented at M6B** using word-timestamp gap inference (DEC-014's "Approach A") with the provisional 1.0s threshold — still classified approximate/provisional, not upgraded by implementation; reports a detected event, not an exact duration (see decision-log.md DEC-014) |
| FR-13 | Evidence display | User needs to see the concrete data behind any feedback | **Implemented at M6B.** Results screen shows transcript, real measured metrics (duration, word count, WPM, pauses, fillers) with visible reliability labels |
| FR-14 | Evidence-grounded coaching | Coaching must be specific and defensible, not generic | Coaching output explicitly references at least one piece of structured evidence (e.g. a specific pause, filler count, or WPM value) |
| FR-15 | One retry goal | Directs the user's next attempt toward a single, actionable improvement | After coaching, exactly one concrete retry goal is presented, grounded in that attempt's evidence (e.g. "Reduce long pauses before your second point") |
| FR-16 | Same-prompt retry | Enables before/after comparison on a controlled variable (same prompt) | User can re-record a response to the identical prompt from the same session |
| FR-17 | Comparison between attempt 1 and attempt 2 | Answers "did the retry improve?" | Results screen shows attempt 1 and attempt 2 metrics side by side, highlighting deltas relevant to the retry goal |
| FR-21 | Completed practice is retained across browser sessions | A streak or a weekly practice total that resets when the tab closes is not a record of practice at all — the value of the habit modes depends on completed practice still being there tomorrow | The system retains completed Read Aloud and Tongue Twister practice metadata locally, so that completed practice can support practice history, current-streak, and weekly practice-duration calculations across browser sessions. Retained metadata is limited to what those calculations need (which mode, when it completed, how long it lasted, and the user's own optional note); no audio, transcript, or analysis output is retained. Derived figures are calculated from retained practice, not stored as figures. *(Mechanism is a separate decision — see DEC-027.)* |

## V1 Scope — Later (not built in V1)

- Stuck Map (interactive timestamp-linked evidence tied to audio playback)
- Historical progress tracking across many sessions
- Advanced disfluency detection (beyond basic filler words)
- CrisperWhisper experimentation
- Pronunciation analysis
- Richer speech-structure analysis
- Authentication
- Cloud persistence
- Mobile application

## Out of Scope for V1

- Speech disorder diagnosis
- Mental-health diagnosis
- Personality scoring
- Intelligence scoring
- Social networking
- Subscriptions
- Production cloud infrastructure
- Multi-user account system

## Non-Functional Notes

- **Local-first**: the core V1 application (recording, transcription, deterministic
  metrics, evidence, retry, comparison) runs and works entirely on the developer's machine
  without any external service. Gemini coaching is an optional external service layered on
  top — it is never required to run or use the core application. See `ai-boundaries.md`.
- **Deterministic core**: duration, word count, WPM, pause detection, and known filler counts must be computed by deterministic Python logic — never by an LLM. See `ai-boundaries.md`.
- **Graceful AI degradation**: if `GEMINI_API_KEY` is not set or the Gemini call fails, transcript and deterministic metrics must still be shown and fully usable; only the coaching section degrades.
- **In-session persistence only, for session data**: `PracticeSession` and `SpeechAttempt`
  data (audio, transcript, metrics, coaching, the current Impromptu attempt) are held in
  frontend application memory for V1 (no database, no server-side session store). A
  browser refresh may lose an unfinished session — this is an accepted V1 limitation, not
  a bug (see DEC-010).
- **Completed-practice history is the one exception** (added at UI-R4A, see DEC-027):
  small completion *metadata* for finished Read Aloud / Tongue Twister sessions is
  persisted in browser `localStorage` so a streak and a weekly total can outlive the tab.
  No speech or AI data is ever written there, and it remains browser- and device-local —
  clearing site data deletes it, and there is no account, backup, or cross-device sync.

## Deferred Decisions

The following are intentionally left undecided in V1 documentation and will be resolved at
the milestone noted, using real data rather than guesses:

| Item | Deferred to | Resolved using |
|---|---|---|
| Long-pause threshold (FR-12) | M6A gave a provisional value (1.0s, word-gap inference method), implemented in production at M6B; final value still pending | Real recorded practice samples — M6A/M6B only had synthetic TTS samples (see `decision-log.md` DEC-014) |
| Filler-word vocabulary (FR-11) | M6A gave a provisional vocabulary and context-sensitive policy, implemented in production at M6B; final precision/recall claim still pending | Real transcripts — M6A/M6B only had 8 hand-labelled synthetic examples (see `decision-log.md` DEC-015) |
| faster-whisper model size/device (DEC-004) | M5 | Latency/accuracy benchmarking |

Browser audio codec/format (FR-04) was resolved at M3 — see `decision-log.md` DEC-016.

See `decision-log.md` for the remaining deferred entries.
