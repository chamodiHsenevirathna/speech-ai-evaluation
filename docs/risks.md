# Risk Register

Known weaknesses with real evidence behind them — distinct from `docs/assumptions.md`
(things believed true but unverified). Every risk below has a mitigation already in
place or a trigger condition for when to revisit it; none are silently unmitigated. No
numeric risk scores are used — Probability/Impact are qualitative (Low/Medium/High)
judgment calls, not computed values.

---

### RISK-001

**Description:** STT transcription errors distort downstream metrics (word count, WPM,
future filler counts) that are computed from transcript text.

**Evidence:** M5's real-human validation found "several meaningful lexical
transcription errors" on a real non-native-accented recording
(`experiments/m5_transcription/conclusions.md`).

**Probability:** Medium (confirmed to occur on real speech, frequency not yet
quantified across a larger sample).

**Impact:** Medium — affects metric *accuracy*, not availability; already mitigated by
labeling these metrics "approximate" rather than exact (see
`experiments/m6_speech_metrics/conclusions.md` Step 1).

**Mitigation:** Word count/WPM classified ACCEPTED BUT APPROXIMATE, never presented as
exact; user-facing wording guidance already defined (Step 11 of the same document).

**Trigger to revisit:** A larger real-human evaluation set (beyond the one ad hoc M5
recording) showing error rates high enough to undermine even the "approximate" framing.

**Status:** Open, mitigated by labeling — not eliminated.

**Relevant experiment:** `experiments/m5_transcription/conclusions.md`.

---

### RISK-002

**Description:** Whisper's decoder smooths away some real repetitions/stutters before
any transcript-based detector can see them.

**Evidence:** M5 found scripted "the the" collapsed to "the"; M6A's EXP-M6-004
reproduced the exact same finding and confirmed (by checking against the reference
script) that the heuristic would have caught it had the transcript preserved it.

**Probability:** Medium — confirmed reproducible on at least one specific disfluency
pattern (word-level stutter); unknown frequency on other repetition patterns.

**Impact:** High for this specific metric — this is the primary reason repetition
detection is classified DEFERRED, not just approximate; no detector design can fix an
upstream information loss.

**Mitigation:** Repetition/restart detection deferred from V1 entirely rather than
shipped as an unreliable metric.

**Trigger to revisit:** A different STT model (e.g. a future CrisperWhisper evaluation,
M12) that measurably preserves disfluencies better — this is a model-selection
question, not a detector-logic question (see the AI/ML rules in `docs/methodology.md`).

**Status:** Open, accepted via deferral.

**Relevant experiment:** `experiments/m6_speech_metrics/experiment_plan.md` EXP-M6-004.

---

### RISK-003

**Description:** The pause detector's observed word-timestamp gap is not the same
quantity as true acoustic silence duration, and can overshoot it substantially at short
pause lengths.

**Evidence:** M6A's EXP-M6-002 found a 0.5s injected (ground-truth) silence produced a
1.00s observed Whisper word-gap — a 2x overshoot — while longer pauses (1–3s) showed
smaller relative overshoot (~3–26%).

**Probability:** High — this is a confirmed, reproducible measurement artifact, not a
hypothetical.

**Impact:** Medium — affects the *precision* of a duration claim, not the ability to
detect that a pause occurred (flagging was 100% correct across all tested thresholds).

**Mitigation:** DEC-014 kept Provisional (not Accepted); explicit rule adopted that the
detector must never be presented as measuring an exact duration, only as flagging a
detected long pause (see `experiments/m6_speech_metrics/conclusions.md` "What this
detector actually measures").

**Trigger to revisit:** Real-human validation via
`experiments/m6_speech_metrics/real_human_validation_checklist.md`, ideally with an
independently-measured true silence duration to compare against.

**Status:** Open, mitigated by wording/threshold caution, not resolved.

**M6B real-human evidence (2026-08-20):** a controlled real-human test (Test B, see
`experiments/m6_speech_metrics/real_human_validation_results.md`) with 2 intentional
scripted pauses (~1s, ~2s) produced 3 detected word-gap events — the third had no known
intentional source and is treated as a possible false positive. Consistent with this
risk's existing finding (word-gap detection overshoots/diverges from true acoustic
silence); a single real-human sample, not new evaluation-set evidence. Does not change
this risk's status or DEC-014's status.

**Relevant decision/experiment:** DEC-014; `experiments/m6_speech_metrics/experiment_plan.md` EXP-M6-002.

---

### RISK-004

**Description:** Whisper hallucinates a spurious word on near-silent/silent audio
rather than returning an empty transcript.

**Evidence:** M5's `near_silent` sample (pure digital silence) was transcribed as the
single word "You" by both `tiny.en` and `base.en`.

**Probability:** High — confirmed on both model candidates tested.

**Impact:** Low today (only affects transcript display in an edge case already handled
by "no speech detected" UX per `docs/context.md`); would become Medium if a future
metric naively used transcript non-emptiness as a proxy for "speech occurred."

**Mitigation:** None implemented at the metrics layer yet — currently only relevant to
transcript display, which already has a "no speech detected" UX path independent of
transcript content specifically.

**Trigger to revisit:** If/when a future "was there speech at all" check is built on
transcript content rather than duration/VAD, this hallucination must be accounted for
explicitly.

**Status:** Open, low current impact, not yet mitigated at the metrics layer (no
metrics layer exists yet).

**M6B real-human evidence (2026-08-20):** a real-human near-silence test (Test C, see
`experiments/m6_speech_metrics/real_human_validation_results.md`) produced a
punctuation-only transcript (`"."`), and the metrics tokenizer correctly produced word
count 0, WPM 0, filler count 0, and long-pause count 0 — the specific feared failure
mode (a lexical hallucination producing apparently legitimate nonzero metrics) did
**not** reproduce in this run. This does **not** resolve or reduce this risk: the
sample exercised a punctuation-only hallucination, not the lexical hallucination
("You") this risk documents from M5, so the prior evidence remains fully valid. An
evidence-sufficiency/abstention gate remains a possible future mitigation, not a
requirement introduced by this result.

**Relevant experiment:** `experiments/m5_transcription/conclusions.md` "Silence
hallucination."

---

### RISK-005

**Description:** A future Gemini coaching integration sends transcript and metrics
data to a third-party API, outside the user's machine.

**Evidence:** None yet — Gemini is not implemented in any code path. This is a
forward-looking risk based on the stated architecture (`docs/ai-boundaries.md`), not an
observed incident.

**Probability:** High that this will eventually happen (it's the planned M8 design),
Low that it happens in an uncontrolled way given the boundary already decided.

**Impact:** Medium — structured evidence (transcript, metrics) leaving the machine is a
real privacy change from today's fully-local behavior, even though raw audio is
explicitly excluded by design.

**Mitigation:** `docs/ai-boundaries.md` "Interface Isolation" already scopes this
narrowly (structured evidence only, never raw audio) and requires Gemini to remain
fully optional (`GEMINI_API_KEY` unset must not break the core app).

**Trigger to revisit:** M8 implementation — at that point, `docs/privacy.md` needs a
concrete (not forward-looking) update describing exactly what's sent.

**Status:** Anticipated, pre-mitigated by architecture, not yet realized.

**Relevant decision:** See `docs/ai-boundaries.md`; no DEC-XXX yet since Gemini isn't
implemented.

---

## Risks considered and not included here

Risks that were evaluated but don't meet this register's bar (real, evidence-backed,
currently unmitigated-or-partially-mitigated) are not listed — e.g. purely
hypothetical multi-user risks, which are excluded per the project's explicit
scope (no multi-user system exists to have those risks).
