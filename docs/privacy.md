# Privacy & Data Handling

What SpeakLab currently does with a user's voice and speech data. Local-first and
in-memory where practical (`docs/decision-log.md` DEC-010) — this document states that
plainly rather than as enterprise privacy boilerplate, since there is currently no
multi-user system, no account, and no persistence layer for any of this data.

> Paths under `frontend/` in the tables below refer to the SpeakLab application, which is not
> part of this repository.

## What SpeakLab currently handles

| Data | Persists? | Where | Sent outside the machine? |
|---|---|---|---|
| Microphone audio | Only in-memory, for the browser tab's lifetime | A browser `Blob` + transient object URL (`frontend/src/types/domain.ts` `AudioRecording`); the backend never writes it to disk (see `docs/security.md`) | No — travels once, over `localhost` HTTP, from the frontend to the local backend, and nowhere else |
| Transcript | Only in-memory (frontend `PracticeSession` state) | Not persisted server-side; lost on browser refresh (DEC-010, accepted) | No |
| Speech metrics | Only in-memory (frontend `PracticeSession` state) — implemented at M6B (`backend/app/services/metrics/`), computed entirely locally from the already-in-memory transcript | Computed server-side per-request, not persisted server-side; returned in the same response as transcription | No — computed and consumed entirely on `localhost`, never sent to any external service |
| Practice-session state (prompt, attempt history, retry goal) | Only in-memory, for the browser tab's lifetime | `frontend/src/state/PracticeSessionContext.tsx` | No |
| Completed practice history (Read Aloud / Tongue Twister) — mode, completion time, duration, optional note, which focus was practised | **Yes — browser `localStorage`**, key `speaklab.practiceHistory.v1` (UI-R4A, DEC-027) | `frontend/src/history/practiceHistoryStorage.ts`; browser- and device-local, cleared when the user clears site data | No — never sent to the backend or to any AI service |
| Experiment results (`experiments/*/results/*.json`) | Yes — committed to git | Numbers and (synthetic) transcript text only, no audio | Not by the application. Published only if included in this repository; see the README |
| Experiment audio samples (`experiments/*/samples/`) | No — explicitly gitignored in both `experiments/m5_transcription/.gitignore` and `experiments/m6_speech_metrics/.gitignore` | Local disk only, regenerable via each experiment's `generate_samples.*` script | No |

## What does not persist

Per DEC-010: the entire `PracticeSession` (prompt, attempts, audio, transcript,
metrics, coaching, retry goal) lives in frontend application memory only. Closing the
tab or refreshing the browser during an unfinished session loses that state — this is
an accepted V1 limitation (`docs/context.md` "User refreshes during an unfinished
session"), not a bug, and not something privacy-motivated — it's simply that no
persistence layer has been built yet (DEC-007).

**Audio, transcripts, metrics, coaching output, and word/pause timestamps are never
written to browser storage.** UI-R4A added `localStorage` persistence for *completed
practice metadata only* (DEC-027) — the storage adapter writes a fixed set of fields
(id, mode, completion time, duration, optional note, optional content id) and validates
on read, so speech or AI data cannot reach storage even if a caller passed it.

### The optional Read Aloud note

Read Aloud allows an optional free-text note on a completed session. Because it is
user-entered text, it is worth stating plainly:

- It is **stored locally in the browser only**, alongside the rest of that session's
  completion metadata.
- It is **never sent to the backend or to any AI/coaching service** by this feature.
- **Clearing browser storage deletes it**, permanently and without warning.
- There is **no cloud backup, no account, and no cross-device sync** — a user should not
  treat these notes as durable or recoverable storage.

SpeakLab performs **no analysis of note content** — no sentiment, no topic detection, no
sensitive-content scanning. The note is stored and read back verbatim, nothing more.

## What may later be sent to Gemini

Coaching (Gemini) is not implemented yet (targeted at M8). When it is, per
`docs/ai-boundaries.md` "Interface Isolation": the coaching service will receive only
structured evidence — the transcript text and computed `SpeechMetrics` — **never raw
audio**. This boundary is decided ahead of implementation specifically so raw voice
audio is never a candidate for leaving the machine at all, even once an external AI
provider is introduced. `GEMINI_API_KEY` is optional; if unset, the app must remain
fully usable minus coaching (`docs/ai-boundaries.md` "Gemini Is Optional, Not
Required").

## Raw recordings are never committed

Every experiment that generates or would generate speech audio (`experiments/
m5_transcription/`, `experiments/m6_speech_metrics/`) gitignores its `samples/`
directory. M5's one ad hoc real-human qualitative check (a real non-native-accented
recording) was, per this same rule, never saved to disk in a way that could be
committed — see `experiments/m5_transcription/conclusions.md`. This is a standing rule
for all future experiment work, not a one-off precaution — see `docs/methodology.md` "Research-integrity rules".

## Experiment privacy policy

- Synthetic (TTS-generated) audio may be committed only as a *script* or *reference
  transcript* (text), never as the audio file itself — matches the existing
  `.gitignore` pattern in both experiment folders.
- Real-human audio, if ever used for validation, is never committed in any form — only
  the resulting written observations/measurements (see `experiments/
  m6_speech_metrics/real_human_validation_checklist.md` for the current example of
  this policy in practice).

## What this document deliberately does not claim

No GDPR/CCPA-specific compliance tooling, no data-retention policy beyond "nothing
persists server-side," no cookie/tracking policy (there is no tracking), no data
export/deletion mechanism (there is nothing stored to export or delete). These would be
premature for a single-user local prototype with no account system — see
`docs/requirements.md` "Out of Scope for V1" and `docs/methodology.md`.
