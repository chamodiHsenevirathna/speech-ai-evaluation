# M6B Real-Human Validation Results

**Date:** 2026-08-20
**Nature of this evidence:** three manual browser/microphone tests run by a human
against the live SpeakLab frontend/backend (M6B's production implementation), not the
synthetic TTS samples used in `conclusions.md`/`experiment_plan.md`. **Qualitative
evidence only** — three single samples, not an evaluation set. No precision, recall, or
F1 was calculated from these samples, and none should be inferred from this document.
No pause threshold, filler rule, or STT model was changed as a result of these tests.

This document is deliberately kept separate from M6A's `conclusions.md` so the two
evidence types — synthetic (M6A) and real-human (this document, M6B) — are never
conflated. See `docs/decision-log.md` DEC-014/DEC-015 for how this evidence was weighed
against decision status (both remain unchanged).

## Test A — Natural speech (~2:14, unscripted)

Duration 133.7s, word count 240, WPM 108 (arithmetically consistent with displayed
values). Transcript broadly understandable, with several transcription errors that
cannot be conclusively separated from unusual real phrasing (no reference transcript
exists for natural speech). 2 long pauses detected (0:44, 2:03); correspondence to
actual pauses was not established. 0 fillers detected, despite the transcript appearing
to contain two natural discourse-marker uses of "like" — flagged as a **possible**
filler false-negative on natural speech, not confirmed (single unlabeled sample). One
repetition/restart visible in the transcript, correctly not flagged (repetition
detection remains deferred).

## Test B — Controlled fillers + pauses (scripted)

Script: "Um, I think speaking clearly takes practice. My friend looks like her sister.
Like, sometimes I lose my train of thought. [~1s pause] Uh, then I try to continue.
[~2s pause] Actually, regular practice probably helps."

Duration 27.4s, word count 34, WPM 74 (consistent). All four scripted filler triggers
were detected: initial "um"; a second filler where spoken "uh" was transcribed as "um"
(not "ah") and was still caught; "actually" (fires per DEC-015's sentence-initial-and-
comma-followed rule); discourse "like" (detected even after Whisper altered
surrounding punctuation). Semantic "like" ("looks like her sister") was correctly
**not** flagged — no false positive. 3 long-pause events were detected against 2
intentional pauses (~0:13, ~0:15, ~0:20); the ~0:15 event has no known intentional
source and is treated as a possible false positive, consistent with the word-gap
(not acoustic-silence) nature of this detector.

## Test C — Near silence (~13.1s, no intentional speech)

Transcript was punctuation-only (`"."`) — no lexical hallucination occurred in this
run. Word count, WPM, filler count, and long-pause count were all correctly 0. The
specific feared failure mode (a hallucinated lexical word producing apparently
legitimate nonzero metrics) did **not** reproduce here. This is a different
hallucination shape than M5's prior finding (pure digital silence transcribed as the
lexical word "You" on both `tiny.en` and `base.en`) — this result does not retire or
reduce that prior finding, since a different near-silence input was used and the
lexical-hallucination path was not exercised this time.

## Test D — Controlled fillers + one long pause (2026-08-21)

**Controlled human intent (self-reported by the speaker, not independently verified
against the audio — see "Limitations" below):** deliberately used "um", deliberately
used "uh", deliberately used "like" (multiple times), deliberately inserted one pause
of approximately 3–5 seconds.

**Observed transcription:** contained **zero punctuation** anywhere in the output (no
commas, no periods) — unlike Test B, where DEC-015's context rule had punctuation to
key off of. The three relevant occurrences of "like" are identified below by position
and timestamp only: a punctuation-free discourse-marker "like", a "like" directly
following a comparison verb, and a pause-adjacent "like". *(The full sentence and the
words surrounding each "like" were removed before publication because they are
real-voice content; timestamps, analysis and conclusions are unchanged.)*

**Word timestamps** (full `words` array from the actual API response; all three
"like" occurrences and their immediate neighbors):

| idx | text | start | end | note |
|---|---|---|---|---|
| 4 | *(redacted)* | 5.10 | 5.68 | precedes like #1 |
| 5 | **"like"** | 5.68 | 7.14 | occurrence 1 |
| 6 | *(redacted)* | 7.14 | 8.52 | |
| … | | | | |
| 11 | *(redacted; a comparison verb)* | 19.26 | 19.70 | precedes like #2 |
| 12 | **"like"** | 19.70 | 20.16 | occurrence 2 |
| 13 | *(redacted)* | 20.16 | 21.12 | |
| … | | | | |
| 18 | *(redacted)* | 24.68 | 28.30 | precedes the long pause, and like #3 |
| — | *(5.38s gap)* | 28.30 | 33.68 | detected long pause |
| 19 | **"like"** | 33.68 | 35.08 | occurrence 3 (segment 2's first word) |
| 20 | *(redacted)* | 35.08 | 36.48 | |

`duration_seconds: 39.54`, `word_count: 21`, `words_per_minute: 31.9` (arithmetically
consistent with the transcript's 21 words over 39.54s — the low WPM reflects the
long pause being included in the duration denominator, as designed per DEC-021).

**Pause outcome — correctly detected.** One `long_pauses` event:
`previous_word_end=28.30`, `next_word_start=33.68`, `observed_gap=5.38`
(33.68 − 28.30 = 5.38, confirmed), against a `threshold=1.0`. This falls within the
~3–5s intentional pause the speaker reports inserting. **The word-gap pause
detector (DEC-014) correctly identified the intentional pause** — this is a clean,
unambiguous positive result, and the closest this project has come to a real,
intentional-and-successfully-flagged long pause.

**Filler outcome — empty, for two distinct and separately traceable reasons.**

***A. Upstream STT omission (no opportunity for the detector to act).*** The speaker
reports deliberately saying "um" and "uh"; neither appears anywhere in
`transcription.words` or `transcription.text`. `detect_fillers` (`fillers.py`) can
only match against word tokens Whisper actually emitted — it has no access to the
raw audio. If "um"/"uh" were genuinely spoken and Whisper silently dropped them,
this is **upstream STT behavior the filler detector cannot see or compensate for**,
consistent with the "possible false negative" already logged for Test A's natural
speech. This sample cannot distinguish "Whisper omitted a real filler" from "the
speaker's self-report of exactly when they said 'um'/'uh' doesn't line up with what
was actually vocalized" — see Limitations below.

***B. Downstream contextual-classification false negatives (a newly identified rule
gap, distinct from A).*** All three "like" tokens **did** survive transcription, so
the detector had a real opportunity here — and still produced zero matches. Tracing
`fillers.py`'s exact rule against this transcript:

```
discourse_position = preceded_by_comma or sentence_initial
comparison_verb_before = previous_text is not None and _clean(previous_text) in _COMPARISON_VERBS
if discourse_position and not comparison_verb_before: <flag>
```

Because this transcript contains **no punctuation at all**, `preceded_by_comma` is
`False` for every word without exception, and `sentence_initial` (which only checks
whether the previous word's text ends in `.`/`!`/`?`) is `False` for every word
except a hypothetical word with no predecessor. So `discourse_position` evaluates to
`False` for all three "like" occurrences, independent of `comparison_verb_before` —
**the rule rejects every occurrence for the same structural reason: it is
punctuation-dependent, and this transcript has none.** This is a rule-design gap,
not a one-off scoring mistake: DEC-015's original policy (and its docstring in
`fillers.py`) assumed faster-whisper reliably keeps punctuation attached to tokens
(confirmed true in Test B's script), but this sample shows that assumption does not
hold on all real speech — this transcript run produced zero punctuation despite
containing multiple genuine sentence/clause boundaries.

Per-occurrence classification (context only — not assuming every "like" was
filler merely because the speaker intended some):

- **Occurrence 1** (5.68–7.14) —
  **clearly filler-like.** Read in context it is a canonical discourse-marker hedge;
  nothing in the surrounding words suggests a comparative or semantic use. Rejected
  here purely by the missing-punctuation gap (A above) — with a comma present before
  it, this occurrence would have been correctly flagged.
- **Occurrence 2** (19.70–20.16) —
  **plausibly semantic, not clearly filler.** A comparison verb immediately precedes
  it, and `_COMPARISON_VERBS` includes "feel"/"feels"/"felt" specifically to suppress
  constructions like "it feels like rain." In context it reads as a semantic
  opinion-marker use of "like," not a discourse filler (surrounding words removed
  before publication). Checking
  the code: `comparison_verb_before` is computed from `_clean(previous_text)`, which
  strips punctuation before comparing — so this occurrence would have been
  **suppressed as a comparison verb regardless of whether punctuation had been
  present**. This is the rule working as designed, not a gap, assuming the semantic
  reading is correct — which cannot be fully confirmed without knowing the speaker's
  actual intent for this specific instance (see Limitations).
- **Occurrence 3** (after the 5.38s pause, 33.68–35.08) —
  **clearly filler-like.** The surrounding clause is coherent without it; "like" is
  inserted immediately after the intentional pause, exactly where a
  speaker resuming after a hesitation would plausibly insert a filler while
  re-starting the sentence. This occurrence surfaces a **second, distinct rule gap**:
  it is the first word of transcript segment 2, immediately following a 5.38s
  detected pause — a much stronger discourse-boundary signal than punctuation would
  be — but `_is_sentence_initial` only inspects the *previous word's text* for
  trailing punctuation, with no awareness of pause/segment boundaries at all. Even
  with normal punctuation elsewhere in this transcript, this specific occurrence
  would likely still have been missed unless the previous word happened to end a
  sentence.

**Limitations of this evidence (user-reported spoken ground truth, no manual audio
annotation):** the "deliberately used um/uh/like" and "~3–5s pause" facts are the
speaker's self-report of overall intent, not a timestamped, independently-verified
annotation of the raw audio. This sample can show *what Whisper output* and *what
the detector did with that output*, and can flag omissions/rejections consistent
with the self-report — but it cannot, on its own, prove that a specific "um" was
vocalized at a specific instant and omitted, versus the speaker's memory of their
own delivery being imprecise (e.g., they may have said "uh" fewer times than
recalled, or hesitated without a filled pause at all). Distinguishing "STT recall
failure" from "self-report imprecision" requires audio with real timestamped human
annotation, not speaker self-report after the fact — this is exactly why the
follow-up experiment recommended below specifies manually annotated audio as its
ground truth, not spoken intent.

## Summary of decision-relevant conclusions

- **DEC-014 (pause threshold):** Test B's 3-detections-for-2-scripted-pauses result is
  a single real-human data point consistent with the already-documented word-gap
  overshoot behavior (`docs/risks.md` RISK-003); it does not by itself justify a
  status change. Test D adds a **clean positive result** — a single intentional
  ~3–5s pause, one detection, `observed_gap=5.38s` arithmetically confirmed
  (33.68 − 28.30). Still one sample; does not upgrade the threshold's status.
  **Remains Provisional.**
- **DEC-015 (filler vocabulary/policy):** mixed real-human evidence (correct semantic
  suppression, correct discourse-marker detection under script conditions, a possible
  natural-speech false negative, one semantically ambiguous but rule-conformant
  detection). Test D adds a **newly identified, distinct downstream rule gap**: the
  context-sensitive rule is structurally punctuation-dependent, and on a transcript
  with zero punctuation it cannot flag *any* discourse-marker "like"/"actually"/
  "basically", regardless of how clearly filler-like the usage is — plus upstream
  evidence consistent with Whisper omitting "um"/"uh" entirely on this sample. Not
  enough scale or labeling to justify Accepted; this is real evidence of an
  additional failure mode, not a clean pass. **Remains Provisional/Experimental.**
- **DEC-021 (duration source):** nothing observed contradicts decoded-audio duration as
  authoritative — duration remained available and consistent even in Test C, where the
  transcript was empty. Test D's low WPM (31.9) is arithmetically consistent with
  including the 5.38s pause in the duration denominator, not a new concern.
  **Unchanged.**
- **Silence hallucination (RISK-004):** not resolved by this test; the lexical-
  hallucination path documented at M5 was not exercised in this sample. An
  evidence-sufficiency/abstention gate remains a possible future mitigation, not a
  requirement introduced by this result.

## Recommended follow-up: a proper filler pipeline-stage experiment

Test D shows the single "0 fillers detected" outcome actually conflates at least two
separable failure stages (STT omission vs. downstream rule rejection), which the
current EXP-M6-003 8-example evaluation and the qualitative Test A/B/D observations
were not designed to separate. A follow-up experiment should measure each stage
independently:

- **Ground truth:** manually, independently annotated real audio — a human listens to
  the actual recording and marks every genuinely spoken filler with a timestamp,
  *without* reference to what Whisper or the detector produced. Per Test D's own
  Limitations note, speaker self-report of intent is not sufficient ground truth for
  this purpose.
- **Three things to compare against that ground truth, kept separate rather than
  collapsed into one end-to-end number:**
  1. **STT filler recall** — of the manually annotated fillers, how many appear as
     matching word tokens anywhere in `transcription.words` (regardless of what the
     downstream detector later does with them)? This isolates upstream
     omission/normalization (failure mode A).
  2. **Downstream detector precision/recall, conditional on STT output** — restricted
     to only the fillers that *did* survive transcription, how does
     `detect_fillers`'s context rule perform? This isolates rule-logic accuracy
     (failure mode B) from STT loss.
  3. **End-to-end precision/recall** — ground truth vs. final `fillers` array, the
     number actually surfaced to a user today. This is the metric users experience,
     but conflates stages 1 and 2, which is exactly why it's necessary to also report
     1 and 2 separately.
- **What this would let the project conclude that it currently cannot:** whether a
  low end-to-end recall is primarily an STT problem (in which case no rule change to
  `fillers.py` would help much) or primarily a rule-logic problem (in which case the
  punctuation-dependency gap Test D surfaced would be the place to start) — the
  current evidence cannot separate these, which is precisely why DEC-015 remains
  Experimental rather than being narrowed to a specific fix.
- **Deliberately not specified here, per this task's constraint:** a sample-size
  target, a numeric pass/fail threshold, or a specific fix to `fillers.py`'s
  punctuation-dependent rule. Those require either a source/benchmark justification
  or should fall out of running this experiment, not be assumed ahead of it.

## Flagged for future consideration (not decided, not implemented here)

Test D's two-failure-mode result (real fillers omitted upstream by STT, real
surviving "like" tokens rejected downstream) raises a **product-copy question**: the
current UI label "Detected fillers" (`MetricCard` on `ResultsScreen`) reads as a
completed, confident count. Given the now-documented gap between what was actually
spoken and what the pipeline can detect, a more uncertainty-aware label such as
"Possible fillers detected" may better match what this EXPERIMENTAL-tier metric
actually claims. **This is a future product-copy evaluation question only — no UI
copy was changed as part of this task.**
