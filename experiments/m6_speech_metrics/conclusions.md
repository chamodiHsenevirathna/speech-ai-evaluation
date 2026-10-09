# M6A Conclusions — Speech Metrics & Evidence Design

**Status: design and experiment milestone.** No production metrics code is wired into
the backend/frontend as a result of this document — see `../../docs/decision-log.md`
for what was actually decided (DEC-014, DEC-015, DEC-020) and what remains provisional.

## Step 1 — Metric Reliability Classification

| Metric | Source | Calculation | Reliability | Key assumptions | Failure modes | Suitable for V1? | User-facing label | Human validation required? |
|---|---|---|---|---|---|---|---|---|
| **Recording duration** | Audio container (decoded), not transcript | Container duration as reported by the audio decoder | **High-confidence deterministic** | The uploaded bytes are a valid, decodable audio container | Corrupt/truncated upload (already rejected at the upload-validation stage, DEC-018) | Yes — ACCEPTED | "Duration" | No |
| **Word count** | Transcript text | Whitespace/punctuation tokenization of transcript text | **Derived from imperfect transcription** | Transcript approximates what was actually said | Lexical errors, hallucinated words on silence (M5 finding), smoothed-away stutters (M6A finding) all shift the count in either direction | Yes, labelled as approximate — ACCEPTED BUT APPROXIMATE | "Word count (approx.)" | Recommended before treating as exact |
| **WPM** | Word count ÷ duration | See Step 3 below | **Derived from imperfect transcription** | Both inputs (word count, duration) are individually imperfect/approximate | Compounds word-count error; near-empty transcripts risk divide-by-zero-like distortion (already handled per `context.md` "No speech detected" — metrics aren't computed on empty input) | Yes, labelled as approximate — ACCEPTED BUT APPROXIMATE | "Approx. WPM" | Recommended |
| **Long-pause detection** | Word-level timestamp gaps (Approach A, EXP-M6-002) | Gap between consecutive word end/start times ≥ threshold — **a threshold on Whisper's observed word-gap, not a direct measurement of acoustic silence duration** (see "What this detector actually measures" below) | **Detection-dependent** | Word timestamps correlate with known injected pauses well enough to *flag* them (EXP-M6-001/002); does **not** assume the observed gap equals the true silence duration — EXP-M6-002 found a 0.5s injected pause produced a 1.00s observed gap | Whisper's word-gap can overshoot true acoustic silence by a fixed offset that becomes a large relative error at short pause lengths (2x at 0.5s in this data); TTS sentence-boundary gaps (~0.5s) may not represent real natural speech word gaps; VAD alternative is environment-blocked | Yes, labelled as approximate — ACCEPTED BUT APPROXIMATE (as a *flag*, not a duration measurement) | "Detected long pauses (approx.)" — **never** "you paused for exactly N seconds" | **Required** before the threshold can be called final |
| **Filler detection** | Context-sensitive vocabulary matching (Baseline B, EXP-M6-003) | Regex/positional rules over transcript text | **Detection-dependent** | Transcript preserves filler words reasonably (mixed evidence: "um" preserved, "uh"→"ah" normalized) and context rules generalize beyond 8 examples | Whisper normalization changes filler surface forms; context rules only tested on a handful of hand-written examples; F1 gap between approaches (0.8 vs 0.833) is not statistically meaningful at this sample size | **Not yet** — EXPERIMENTAL | "Detected fillers (experimental)" | **Required** — 8 examples is not enough to claim precision/recall |
| **Repetition / restart detection** | N-gram + phrase-start heuristics | See EXP-M6-004 | **Detection-dependent** | Assumes the transcript preserves the repetition; EXP-M6-004 shows this assumption fails on real Whisper output, via **two distinct failure sources** (see below) | **(A) Downstream:** current heuristic misses restarts that don't share a second word, even when the transcript has the evidence. **(B) Upstream:** Whisper decoder smoothing erases some real stutters/repeats before any transcript-based detector ever sees them — no heuristic could fix this | No — **DEFERRED** | N/A (not shown in V1) | Required, plus a detector redesign (source A) and/or a different STT model (source B) |

### Filler detection: exact figures and what they do (and don't) show

**Context-sensitive matching (Baseline B, the chosen policy direction) measured
precision = 0.833, recall = 0.833, F1 = 0.833** on `results/fillers.json`. Stated
plainly, with the caveats that must travel with these numbers every time they're cited:

- **The evaluation size was 8 synthetic examples** (9 scored vocabulary occurrences).
  This is a small hand-built sample, not a research-scale benchmark, and **does not
  establish general real-world accuracy** — it shows this specific rule set behaves
  reasonably on this specific small, synthetic set, nothing stronger.
- **Ambiguous discourse markers remain a known failure mode.** Baseline B's rule
  correctly suppressed the two clean semantic false positives ("looks like her sister,"
  "actually completed a week ahead") but missed a real hedge use of "actually" that
  wasn't sentence-initial (`filler_actually_hedge`) — a documented, reproducible rule
  gap, not a hypothetical one.
- **Whisper normalization can affect filler detection upstream of any detector logic.**
  The scripted "uh" was rendered as "ah" by the model (reproducing the exact M5
  finding) — a filler-detection rule that only matches literal "uh" will silently miss
  it, regardless of how good the rule's context-sensitivity is, because the problem
  originates in transcription, not detection.

These three points are why filler detection is classified **EXPERIMENTAL**, not
ACCEPTED BUT APPROXIMATE like pause detection — pause detection's flagging behavior was
100% correct across all 5 samples tested, while filler detection has a documented,
non-hypothetical error on both baselines even at this small scale.

## Step 2 — Recording Duration

**Authoritative source: the audio container's own decoded duration, not the transcript.**
Concretely, this should come from an independent, cheap probe of the uploaded audio
bytes (e.g. PyAV's container `duration`), separate from whether transcription itself
succeeds — not solely `TranscriptionSuccess.duration_seconds` as returned today by
`backend/app/services/transcription/faster_whisper_service.py`. That field happens to be
correct today because faster-whisper decodes the same audio it transcribes, but it is
only populated on a *successful* transcription. If transcription fails
(`transcription.status: "failed"`), duration should still be computable from the audio
alone, since `context.md` treats "transcription failure" and "duration unavailable"
as two different concerns — the recording and its playback survive a transcription
failure, and its duration is a property of the recording, not of the transcript.

**Fallback:** if the audio cannot be decoded at all (the same failure mode that would
also fail transcription), duration is unavailable and should be shown as such — this is
already representable by the existing per-stage failure model, it just needs duration
to be sourced independently of the transcription stage rather than nested inside it.

**Rounding:** round to 1 decimal place (0.1s) for display — matches the precision
already used for `transcription_seconds`/`duration_seconds` in the M5 API contract
(`docs/context.md`); no evidence in this experiment suggests finer precision is
meaningful to a user.

**Silence before/after speech:** counts. Duration is a property of the *recording*
(what the user submitted, including any leading/trailing silence from when they
pressed stop), not of the *speech* within it — this matches DEC-009 (manual stop, no
auto-cutoff) and keeps duration a simple, unambiguous, always-available number rather
than one that depends on speech-detection accuracy.

## Step 3 — Word Count and WPM

**Word-counting rule:** split transcript text on whitespace after stripping punctuation
that isn't part of a word (matches the `[a-z']+` tokenization already used in
`experiments/m5_transcription/benchmark.py`'s WER calculation, extended to preserve
internal apostrophes for contractions — "don't" counts as one word, not two).
Numbers rendered as words ("twenty three") count as separate word tokens same as any
other words; numerals rendered as digits ("23") count as one token each. Partial/cut-off
words at a recording's very end are counted as whatever token the transcript actually
contains — no special-casing, since the transcript is already the single source of
truth for "what words exist," consistent with not letting any other layer re-interpret
STT output.

**Repeated tokens:** counted as they appear in the transcript, including any that
Whisper genuinely preserved (e.g. `hesitation_restart`'s scripted repeat, per M5) — word
count is a count of *transcribed* words, not a de-duplicated linguistic analysis. This
is a deliberate simplification: de-duplicating would require the still-DEFERRED
repetition detector, and V1's WPM number does not need to solve that problem to be
useful.

**Transcription errors:** not correctable at this layer — word count inherits whatever
error the transcript already has (see Step 1's reliability table). This is exactly why
word count and WPM are labelled *approximate*, not exact.

**WPM formula:** `word count / (duration in minutes)`, per `requirements.md` FR-10.

**Total recording duration vs. detected-speech duration — conceptual comparison:**

- **Total recording duration** (what Step 2 defines): simple, always available whenever
  duration is available at all, matches what the user actually experienced (they were
  "in the recording" for the whole clip, including any pause where they were thinking).
  A user who pauses for 10 seconds mid-attempt will see a *lower* WPM than someone who
  spoke continuously for the same word count — which is arguably correct: it reflects
  their actual pace across the whole attempt, thinking time included.
- **Detected-speech duration** (total duration minus detected long pauses): would show
  a *higher*, "pace while actively talking" number, isolating fluency from hesitation.
  This is more informative for a specific coaching question ("was your delivery pace,
  not just your overall pacing, too fast/slow?") but **depends on pause detection**,
  which this experiment classifies as ACCEPTED BUT APPROXIMATE (provisional threshold,
  synthetic-only evidence) — stacking one approximate metric inside another compounds
  uncertainty for comparatively little benefit at this stage.

**Decision:** compute WPM using **total recording duration** for M6, and label it
plainly as an approximation of overall pace, not delivery pace. A speaking-duration-only
WPM variant is not ruled out for later, once pause detection has real-human validation,
but is not needed to satisfy FR-10 as written.

**What the user actually learns from WPM:** a single approximate pacing signal —
whether they spoke, overall, unusually fast or slow across their attempt — useful as a
coarse, relative comparison between attempt 1 and attempt 2 of the *same* prompt (same
speaker, same task, so WPM's absolute-number caveats mostly cancel out in the delta),
which is exactly what the Comparison screen (FR-17) needs. It does **not** by itself
tell the user *why* their pace was what it was (fillers? pauses? genuinely fast
delivery?) — that requires the other metrics alongside it, which is why WPM is shown as
one card among several, not a standalone score.

## EXP-M6-001 through EXP-M6-004

See `experiment_plan.md` for the full hypothesis → experiment → result → decision for
each, and `results/*.json` for raw measured output. Summary of resolutions:

- **DEC-020 (word timestamps):** now **Accepted** — enable `word_timestamps=True`.
- **DEC-014 (long-pause threshold):** **provisional** — method (word-gap inference,
  Approach A) is decided with good evidence; the numeric threshold (1.0s) is
  evidence-based but **synthetic-only**, so it is not marked final.
- **DEC-015 (filler vocabulary/policy):** **provisional** — vocabulary and a
  context-sensitive policy direction are decided with real (if small) evidence; not
  marked final because 8 examples cannot support a precision/recall claim that should
  be shown to users as anything but "experimental."

### What this detector actually measures

**The pause detector does not measure acoustic silence duration. It measures the gap
between two Whisper word timestamps, and flags that gap when it exceeds a threshold.**
These are related but not identical quantities, and this experiment's re-check found a
concrete case where they diverge substantially:

| Sample | Injected acoustic silence (ground truth) | Observed Whisper word-gap | Discrepancy |
|---|---|---|---|
| `pause_0_5s` | 0.5s | **1.00s** | **+0.50s (2.0x)** |
| `pause_1_0s` | 1.0s | 1.16s | +0.16s (1.16x) |
| `pause_2_0s` | 2.0s | 2.52s | +0.52s (1.26x) |
| `pause_3_0s` | 3.0s | 3.10s | +0.10s (1.03x) |
| `pause_control_0s` | 0s | 0.50s | +0.50s (natural TTS boundary, no injected silence at all) |

At every injected duration, the observed word-gap **overshoots** the true acoustic
silence — plausibly because Whisper's word boundaries don't land exactly at the edges
of the injected silence (the tail of "important." and the head of "The" both eat into
what should be pure silence). The overshoot is a roughly fixed amount in absolute
terms (~0.1–0.5s) but at the **shortest** tested duration (0.5s), that fixed overshoot
is a **100% relative error** — the observed gap (1.00s) is exactly double the true
pause. This means: **a "1.0 second" reading from this detector could correspond to a
true acoustic pause anywhere from roughly 0.5s to 1.0s** on this evidence, not a
precise 1.0s measurement.

**Consequence for wording:** any future user-facing text must describe this as a
*detected* long pause above a threshold, never as a *measured duration* of exact
acoustic silence (e.g. "a long pause was detected here," not "you paused for exactly
1.0 seconds"). This is a correction to how this document's earlier draft described the
result — a prior version's "correctly overlapped the known interval" wording was
accurate about *flagging* but could be read as implying duration accuracy, which the
evidence above does not support. This document and `experiment_plan.md` EXP-M6-002 have
been revised to make this distinction explicit.

### Why DEC-014's threshold isn't a final number

The synthetic pause samples' "natural gap" control (`pause_control_0s`) measured a
largest inter-word gap of **0.5 seconds** — this is a TTS sentence-boundary pause
artifact (macOS `say` inserts a real pause at the end of a sentence, not a
word-to-word gap), not representative of a real speaker's natural word-to-word
spacing (typically much shorter, on the order of tens of milliseconds) or of a real
hesitation pause (highly variable, and exactly the thing this metric needs to detect).
Because the *control's* gap size is itself inflated by an artifact of the generation
method, a threshold "derived" purely from separating it from the injected pauses risks
being tuned to that artifact rather than to real speech. Compounding this, the
observed-gap-vs-injected-silence discrepancy above (0.5s → 1.00s observed) means the
threshold is being tuned against Whisper's *word-gap signal*, which is itself an
imperfect proxy for the acoustic quantity we actually care about. The **method**
(word-gap inference over VAD, given VAD's environment block) is well-supported; the
**specific number** needs a real recording — ideally with an independently-measured
true silence duration to compare against, not just Whisper's own word-gap output — before
DEC-014 can move from provisional to accepted.

## Step 9 — Multi-Mode Architecture Constraint

SpeakLab's metrics/evidence layer should be split into two conceptual groups, matching
the roadmap's later practice modes (read-aloud, tongue-twisters, articulation):

**Shared speech evidence** (mode-independent, computed the same way regardless of what
kind of practice this is):
- Recording duration
- Transcript (text + timestamps)
- Word count
- WPM
- Pause events

**Mode-specific evaluation** (depends on what the practice mode is actually testing):
- *Impromptu speaking* (V1's only mode): fillers, (future) flow/structure
- *Read-aloud* (later): reference-text accuracy, omissions/additions, pace-vs-reference
- *Tongue twisters* (later): phrase accuracy, repeated-attempt improvement, speed
- *Articulation* (later): target-sound/phrase performance

**Architectural principle:** the shared evidence layer must never assume it's only
serving impromptu speaking (e.g. it must not require a "prompt" concept that only makes
sense for impromptu, or bake in filler detection as if every mode wants it) — filler
detection specifically belongs in the *impromptu* mode-specific layer, not the shared
layer, because "um" is meaningful evidence for impromptu fluency but not obviously
meaningful for e.g. a tongue-twister attempt. This is a documentation-only principle for
M6A — no other mode is implemented, and the current single-mode (impromptu) backend
does not need restructuring yet, but new metrics code written from M6 onward should be
organized so a later mode-specific layer can be added without reworking the shared one.

## Step 10 — Metric Confidence / Provenance (minimum proposal)

Each metric result should carry enough metadata to answer "where did this come from"
without over-modeling now. Minimum proposed shape (not implemented yet):

```json
{
  "name": "wpm",
  "value": 126,
  "unit": "words_per_minute",
  "method": "whisper_transcript_word_count / recording_duration_minutes",
  "reliability": "approximate"
}
```

`reliability` takes one of the four Step 14 classifications
(`exact` | `approximate` | `experimental` | `unavailable`), directly reusable as the
frontend label tier. This is deliberately flat — no separate provenance sub-object, no
versioning, no confidence *score* (a fabricated-looking number would contradict this
milestone's own findings about not overclaiming precision). Add fields only when a
concrete consumer needs them (e.g. a future `threshold_used` field for pause detection,
once DEC-014 is finalized) — consistent with this project's established practice
(`docs/context.md` design notes) of not adding unused structure ahead of need.

## Step 11 — User-Facing Language

| Metric | Prefer | Avoid |
|---|---|---|
| Duration | "Duration: 58.3s" (exact, no hedge needed) | — |
| Word count | "Word count (approx.): ~142" | "Word count: 142" (implies exactness the source doesn't have) |
| WPM | "Approx. WPM: 126" | "WPM: 126" |
| Pauses | "Detected long pauses (approx.)" | "You paused exactly 3 times" or "you paused for exactly N seconds" (the detector flags a thresholded gap between word timestamps, not a measured acoustic duration — see "What this detector actually measures" above) |
| Fillers | "Detected fillers (experimental)" | "You used exactly 7 fillers" |
| (any composite) | *(not proposed — see Step 14)* | "Fluency score: 82" |

## Step 14 — Final Classification

| Metric | Classification | Source | Main limitation | Intended user-facing wording |
|---|---|---|---|---|
| Recording duration | **ACCEPTED FOR V1** | Audio container's own decoded duration (independent of transcription) | None significant — only fails if the upload itself is undecodable, which is already rejected at upload validation (DEC-018) | "Duration: 58.3s" |
| Word count | **ACCEPTED BUT APPROXIMATE** | Tokenized transcript text | Inherits transcript error (lexical mistakes, hallucinated words on silence, smoothed-away stutters) | "Word count (approx.): ~142" |
| Approximate WPM | **ACCEPTED BUT APPROXIMATE** | Word count ÷ recording duration | Compounds word-count error; uses total recording duration, not speech-only duration (Step 3) | "Approx. WPM: 126" |
| Long pauses | **ACCEPTED BUT APPROXIMATE** | Gaps between Whisper word-level timestamps ≥ a threshold (provisional 1.0s) | Detector flags a *thresholded word-gap*, not a measured acoustic silence duration — EXP-M6-002 found a 0.5s true pause read as a 1.00s observed gap; threshold validated only on synthetic TTS audio | "Detected long pauses (approx.)" — never a specific duration claim |
| Fillers | **EXPERIMENTAL** | Context-sensitive vocabulary matching over transcript text | Evaluated on only 8 synthetic examples (does not establish general accuracy); known rule gap on mid-sentence hedges; Whisper's own normalization (`uh`→`ah`) can hide fillers before detection even runs | "Detected fillers (experimental)" |
| Repetition/restarts | **DEFERRED** | N/A — not implemented | Two independent failure sources: heuristic misses restarts (fixable), Whisper smooths some stutters away before the transcript ever reaches a detector (not fixable at this layer) | Not shown in V1 |

No composite "speaking score" is proposed anywhere in this document, and no confidence
*percentage* is invented for any metric above — only the four qualitative
classifications requested, each backed by the specific evidence cited in its row.

## Limitations of this experiment overall

- **No real-human recording at all** (unlike M5, which had one ad hoc check) — every
  number in this document comes from synthetic TTS audio with artificially clean
  acoustics and TTS-specific pause behavior (see "Why DEC-014's threshold isn't a final
  number" above). This is this experiment's single biggest limitation and the reason
  DEC-014 and DEC-015 are left provisional rather than accepted.
- No non-native-accented or otherwise accented sample in this experiment specifically
  (M5's one real-human check was accented, but as noted, wasn't retained for reuse).
- Filler and repetition evaluation sets are small by design (8 and 4 labelled examples
  respectively) — explicitly not claimed as research-scale, per the task's own
  instruction to prefer ~10-20 examples over pretending otherwise.
- The context-sensitive filler rule (Baseline B) has one known, documented gap (misses
  a mid-sentence hedge use of "actually") — not silently glossed over, see EXP-M6-003.
- The repeated-phrase-start heuristic (repetition detection) is known to be too strict
  for restarts that don't share their second word — documented in EXP-M6-004, not
  treated as evidence repetition detection is impossible, only that this particular
  heuristic needs refinement before being reconsidered for V1.
- VAD remains blocked by the same onnxruntime/macOS ABI issue found at M5 — re-confirmed
  here, not re-investigated for a fix (out of scope for M6A).
- Only one hardware/OS configuration tested (Apple M1, macOS 13.0), same as M5.
