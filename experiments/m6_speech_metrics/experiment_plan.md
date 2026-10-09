# M6A Experiment Plan

Every decision below follows: **Hypothesis → Experiment → Result → Decision.** Full raw
output is in `results/*.json`; narrative conclusions and the metric reliability table
are in `conclusions.md`. This file records only the four required experiments.

---

## EXP-M6-001 — Word-level vs segment-level timestamps (revisits DEC-020)

**Hypothesis:** Word-level timestamps cost a measurable but acceptable amount of extra
latency, and their timing is plausible enough to localize a known pause — enough to
justify enabling them now that M6 actually has a consumer (pause detection), unlike M5
which deferred this with no consumer yet.

**Experiment:** `evaluate_word_timestamps.py`. Ran `base.en`/cpu/int8 against the 5 M5
samples plus this experiment's 5 `pause_*` samples, twice each — once with
`word_timestamps=False`, once `True`. Compared latency/RTF, transcript text equality,
and — for the pause samples, which have an exactly-known injected silence interval —
whether the largest inter-word gap overlaps that known interval.

**Result** (`results/word_timestamps.json`):
- Latency overhead ranged from **-3.0% to +27.1%** across the 10 samples, average
  **+7.5%** — consistent with, and on the low end of, M5's single-sample ≈11%
  measurement (`../m5_transcription/conclusions.md`). Negative values on some samples
  are measurement noise (single-run CPU timing, not a real speedup).
- Transcript text was **identical** with the flag on or off, on every sample — the flag
  only adds metadata, never changes decoding.
- On all 4 real injected pauses (0.5s/1.0s/2.0s/3.0s), the largest detected inter-word
  gap **correctly overlapped** the known pause interval. On the no-pause control, the
  largest detected gap did **not** overlap the (zero-width) known interval — i.e. it
  correctly found no equivalent pause there.

**Decision (resolves DEC-020):** Enable `word_timestamps=True` for M6+. The latency
cost (~7.5% average, single-digit-to-low-double-digit percent) is small in absolute
terms (well under 1 extra second on the samples tested) and the timestamps are
demonstrably usable for pause localization — this experiment's actual purpose. Also
directly useful for future filler-occurrence timestamps and transcript click-to-audio
(both listed as intended future uses). See `../../docs/decision-log.md` DEC-020 for the
updated entry.

---

## EXP-M6-002 — Pause detection: word-gap inference (A) vs VAD (B) (informs DEC-014)

**Hypothesis:** Gaps between word-level timestamps (Approach A) can reliably *flag* a
known injected silence without a separate VAD pass; VAD (Approach B) would be a more
direct silence measurement but is expected to be blocked by the onnxruntime ABI issue
already found at M5 (`../m5_transcription/conclusions.md` "VAD investigation"). **This
experiment does not test whether Approach A measures the acoustic silence duration
accurately — only whether it can correctly flag that a pause occurred, above a
threshold.** These are different claims; see the corrected result below for why the
distinction matters.

**Experiment:** `evaluate_pauses.py`. Approach A: transcribe each `pause_*` sample with
`word_timestamps=True`, compute every inter-word gap, and check 6 candidate thresholds
(0.3s–2.0s) against the known injected interval. Approach B: attempt
`model.transcribe(..., vad_filter=True)` on one representative sample and record
whether it succeeds or fails.

**Result** (`results/pauses.json`):
- **Approach B (VAD) failed**, reproducing the exact M5 finding: `dlopen` symbol-not-
  found error from `onnxruntime_pybind11_state.so`, built for macOS 13.4 running on
  13.0. Not forced or worked around, per the task's own instruction.
- **Approach A (word-gap): injected acoustic silence vs. Whisper-observed word-gap.**
  These are two different quantities and this experiment found they are **not the
  same number** — the observed gap is not a precise measurement of the acoustic
  silence, only a correlated signal:

  | Sample | Injected acoustic silence | Observed Whisper word-gap | 0.75s threshold | 1.0s threshold |
  |---|---|---|---|---|
  | `pause_0_5s` | 0.5s | **1.00s** | detected | detected |
  | `pause_1_0s` | 1.0s | 1.16s | detected | detected |
  | `pause_2_0s` | 2.0s | 2.52s | detected | detected |
  | `pause_3_0s` | 3.0s | 3.10s | detected | detected |
  | `pause_control_0s` (no injected silence) | 0s | 0.50s | not detected (no false positive) | not detected (no false positive) |

  **The 0.5s injected pause produced an observed word-gap of 1.00s — exactly double the
  true acoustic silence.** This is the largest relative discrepancy in the data: at
  every other injected duration the observed gap overshoots the true silence by a
  roughly constant ~0.1–0.5s (plausibly attributable to how the decoder times the tail
  of "important." and the head of "The", not a to-the-millisecond audio boundary), but
  at 0.5s that same fixed overshoot is a 2x multiplier rather than a small percentage.
  **Both candidate thresholds (0.75s and 1.0s) still correctly flag every injected
  pause and produce zero false positives on the control** — but this experiment
  demonstrates a *threshold/flagging* correctness, not a *duration-measurement*
  correctness. **The detector must not be described as measuring true acoustic pause
  duration** — see `conclusions.md` "What this detector actually measures" for the
  corrected framing and its consequence for any future "you paused for N seconds"
  wording.

**Decision (DEC-014 — provisional, not final):** Method: **Approach A (word-timestamp
gap inference)**, not VAD — VAD is environment-blocked here and Approach A correctly
flags every injected pause with zero false positives on this evidence. Threshold:
**provisionally 1.0 second**, pending real-human confirmation (see `conclusions.md`
"Why this isn't a final threshold" — TTS sentence-boundary gaps are a poor proxy for
real natural speech word-to-word gaps, and the observed-gap-vs-injected-silence
discrepancy above means the threshold is being tuned against Whisper's word-gap
signal, not against true silence duration). This decision is about *flagging*
capability, not about duration-measurement accuracy — see `conclusions.md` "What this
detector actually measures." See `../../docs/decision-log.md` DEC-014.

---

## EXP-M6-003 — Filler detection: unconditional (A) vs context-sensitive (B) matching (informs DEC-015)

**Hypothesis:** Unconditional matching over-counts ambiguous words ("like", "actually",
"basically") that have legitimate non-filler uses; a small set of positional/punctuation
rules can distinguish the two well enough on this evaluation set to justify the added
complexity.

**Experiment:** `evaluate_fillers.py`. Baseline A: any vocabulary word/phrase occurrence
counts as filler. Baseline B: same, except "like"/"actually"/"basically" only count when
a comma/sentence-boundary heuristic suggests discourse-marker position. Both run against
8 labelled samples (`references/fillers.json`), scored at the (sample, vocabulary item)
level restricted to items that actually appear in the transcript.

**Result** (`results/fillers.json`):

| | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Baseline A (unconditional) | 6 | 3 | 0 | 0.667 | 1.0 | 0.8 |
| Baseline B (context-sensitive) | 5 | 1 | 1 | 0.833 | 0.833 | 0.833 |

- Baseline A's 3 false positives: `filler_like_semantic` ("looks like her sister"),
  `filler_actually_semantic` ("actually completed a week ahead"), and one from
  `filler_um_uh` — Whisper transcribed the scripted "uh" as **"ah"** (confirming M5's
  finding again), which happens to also be in the candidate vocabulary and got counted
  as an unrelated filler hit distinct from the missing "uh".
- Baseline B correctly suppressed both semantic false positives, but introduced 1 false
  negative: on `filler_actually_hedge` ("So, actually, um, I forgot..."), the rule
  required "actually" to be *sentence-initial* and comma-followed, but here it's
  mid-sentence (after "So,") — the rule as written is too strict for a hedge that isn't
  at the very start of the utterance.
- On a genuinely small sample (8 examples, 9 scored vocabulary occurrences), F1 differs
  by only 0.033 between baselines — **not a statistically meaningful gap**, but the
  qualitative pattern (A over-counts semantic uses, B's rule needs a "preceded by
  another discourse marker" case added) is a real, reproducible finding, not noise.

**Decision (DEC-015 — provisional):** Vocabulary: `um`, `uh` (normalizing for Whisper's
`uh`→`ah` rendering), `erm`, `like`, `you know`, `actually`, `basically` — all confirmed
present as realistic candidates in this evaluation. Policy: **context-sensitive
matching (Baseline B's approach)**, refined to also treat a discourse marker preceded by
a comma (not only sentence-initial) as filler-position — this experiment found the exact
gap in the current rule rather than guessing at one. Explicitly **not** claiming robust
precision/recall from 8 examples; see `conclusions.md` for why this is provisional. See
`../../docs/decision-log.md` DEC-015.

---

## EXP-M6-004 — Repetition / restart detection (experimental)

**Hypothesis:** Simple n-gram/phrase-start heuristics catch some scripted repetitions,
but Whisper's own smoothing (M5 finding) erases others before any transcript-based
detector can see them — so a transcript-based detector's silence is not proof the
speaker didn't repeat themselves.

**Experiment:** `evaluate_repetitions.py`. Two heuristics: immediate repeated 1–3-word
n-grams, and repeated first-2-words across adjacent comma/period-split clauses. Run
against 4 labelled samples (`references/repetitions.json`).

**Result** (`results/repetitions.json`). Two distinct failure sources were found, and
they have different implications, so they are kept separate rather than lumped under
one "missed" label:

- **Failure source A — downstream detector failure**: the transcript *does* contain the
  repetition evidence, but our heuristic fails to recognize it.
- **Failure source B — upstream information loss**: Whisper's own decoder removes or
  smooths the repetition *before* the transcript ever reaches our detector — no
  heuristic, however good, could recover it from this transcript.

| Sample | Expected | Detected | Verdict | Failure source |
|---|---|---|---|---|
| `repetition_immediate` ("I think, I think we should leave") | repetition | yes | correct | — |
| `repetition_restart` ("The main reason, the reason is...") | repetition | no | **missed by heuristic** | **A (downstream)** — transcript reads verbatim "The main reason, the reason is...", the heuristic's first-2-word-match rule simply doesn't match "the main" against "the reason" |
| `repetition_none_clean` | none | no | correct | — |
| `repetition_word_stutter` ("the the", reused `filler_um_uh` script) | repetition | no | **erased by Whisper smoothing** | **B (upstream)** — confirmed by running the same heuristic against the *reference script* (which does contain "the the"), where it correctly fires; the transcript itself only contains a single "the" |

**Why this distinction matters for future model choices:** failure source A is fixable
by improving the heuristic (e.g. shared-first-word-only matching, or edit-distance
between adjacent clauses) without touching the STT layer. Failure source B is **not**
fixable at the detector layer at all — it requires a transcription model that doesn't
smooth disfluencies away, which is a *model-selection* question (relevant to any future
STT model comparison, e.g. the M12 CrisperWhisper evaluation), not a metrics-engine
question. Conflating the two would incorrectly suggest that better detector code alone
could fix repetition detection.

- `repetition_restart`: Whisper transcribed the script *verbatim*, comma included
  ("The main reason, the reason is..."). The heuristic still missed it because it
  compares each clause's first **two** words exactly ("the main" vs "the reason") — a
  restart naturally doesn't share the second word, so this specific heuristic is too
  strict for restarts by construction, not because of any transcription problem.
- `repetition_word_stutter`: reproduces M5's exact finding — Whisper's decoder smoothed
  "the the" down to a single "the" in the transcript, so no transcript-based detector,
  however good, could have caught this one. Confirmed by comparing against the
  reference *script* (`detected_on_reference_script`), where the same heuristic
  correctly finds "the the" — the miss is specifically a transcription-fidelity problem,
  not a detector problem.
- Net: 2/4 correct, 1 heuristic-design miss, 1 unavoidable-given-current-STT miss.

**Decision:** **DEFERRED from V1.** Two independent failure modes (heuristic can't
handle restarts as currently written; Whisper itself erases some real stutters) on a
sample this small is not evidence of a metric users should be shown as a confident
detection. This is exactly the outcome the M6A task anticipated as acceptable — "it is
completely acceptable if the result is... Repetition → DEFERRED." Revisit only after
either a smarter restart heuristic (e.g. shared-first-word-only, or edit-distance
between adjacent clauses) is evaluated, or the STT layer changes in a way that stops
smoothing disfluencies.
