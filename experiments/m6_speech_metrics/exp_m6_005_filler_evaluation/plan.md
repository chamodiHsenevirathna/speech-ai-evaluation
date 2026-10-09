# EXP-M6-005 — Filler Evaluation Plan

Follows this project's established pattern (`../experiment_plan.md`):
**Hypothesis → Experiment → Result → Decision.** This document defines the
Hypothesis and Experiment only — no Result or Decision exists yet; see `README.md`
"Status." Grounded in `research_review.md`; see that document for full paper
citations and evidence tagging.

---

## 1. Problem

`../real_human_validation_results.md` Test D showed a single "0 fillers detected"
outcome that decomposes into at least two independent failures — `faster-whisper`
omitting spoken "um"/"uh" before any detector runs, and `detect_fillers()`
rejecting real, surviving "like" tokens because its context rule
(`preceded_by_comma` / `sentence_initial` in `fillers.py`) depends on punctuation
that this specific transcript did not contain at all. The existing evidence (M6A's
8-example synthetic set, plus qualitative Tests A–D) cannot separate how much of
the problem is upstream (STT) versus downstream (rule logic) — which means DEC-015
cannot be responsibly narrowed to a specific fix without guessing which stage to
target.

## 2. Hypothesis

**[HYPOTHESIS]** Filler-detection failures are not uniformly distributed across
the pipeline — upstream STT omission and downstream rule misclassification are
expected to have measurably different error rates and different failure shapes
(e.g., omission concentrating on unstressed "um"/"uh"; downstream misclassification
concentrating on punctuation-free transcripts and pause-adjacent tokens, per Test
D). This experiment tests that directly rather than assuming it, and is
independently supported by the literature: **[PAPER]** Romana et al. (2023) show a
language-only disfluency detector's weighted recall drops from 0.86 (manual
transcript) to 0.60 (ASR transcript) — direct, quantified evidence that an
upstream/downstream split is a real, separable phenomenon, not just a SpeakLab
artifact.

## 3. Failure decomposition (three sources of error)

1. **Spoken → not preserved by Whisper** (upstream omission/normalization) — the
   detector never had a chance.
2. **Preserved by Whisper → misclassified by `detect_fillers()`** (downstream rule
   error) — false negative despite a real opportunity, or false positive on a
   semantic use.
3. **Not spoken → falsely detected** — a hallucination-adjacent case, measured
   even though the current design has no structural protection against it.

## 4. Layer A/B/C structure

Full field-level definitions live in `annotation_schema.md`. Summary:

- **Layer A — manual ground truth.** A human annotates the raw audio only (blind
  to transcript/detector output): every genuinely spoken filler-candidate moment,
  its timestamp, type, and whether it's discourse-filler / semantic / ambiguous.
- **Layer B — Whisper-output mapping.** For each Layer-A item: did Whisper preserve
  it exactly, preserve it under a different token (normalization), or omit it —
  plus punctuation and segment-boundary context.
- **Layer C — detector outcome.** For each Layer-B item that survived
  transcription: did the real, unmodified `detect_fillers()` flag it, and does that
  agree with the Layer-A classification.

**[SPEAKLAB]** This structural separation was already validated by hand during
Test D's manual trace — this experiment formalizes and scales that same trace
across many recordings rather than repeating it ad hoc per anomaly.

## 5. Controlled test-case matrix

Each row is a short scripted utterance (coverage target, not a sample-size target
— see §7):

| # | Case | What it isolates |
|---|---|---|
| 1 | Filler at sentence start | True sentence-boundary handling |
| 2 | Filler immediately after a long pause (>1.0s) | Test D's occurrence-3 gap: no pause/segment-boundary awareness in the current rule |
| 3 | Filler immediately after a short pause (<1.0s) | Whether short pauses behave differently from long ones |
| 4 | Filler mid-clause with no surrounding punctuation | Direct replication of Test D's structural failure |
| 5 | Repeated fillers in one utterance | Whether repetition changes Whisper's preservation behavior |
| 6 | Semantic "like" ("It looks like rain") | False-positive risk on the existing `_COMPARISON_VERBS` suppression |
| 7 | "Feel like" as semantic opinion-marker | Test D's ambiguous occurrence 2 — needs multiple examples, one sample can't establish reliability |
| 8 | "Looks like" (different comparison verb) | Same suppression rule, different verb |
| 9 | "You know" as filler vs. genuine question | Currently matched **unconditionally**, no context check at all (`fillers.py:89-99`) — a gap not surfaced by Test D but real |
| 10 | Deliberate, clear "um"/"uh"/"ah" | Direct replication of Test D's upstream-omission finding, with enough repetitions to see if it's consistent |
| 11 | Fast, run-on delivery with no natural punctuation-triggering pauses | Whether punctuation-free output is rare or reproducible under certain delivery styles |

## 6. Natural-speech pilot

A small number of unscripted recordings (same style as SpeakLab's actual practice
flow: answer a prompt for ~60s, unprepared), annotated identically via Layers
A/B/C. Purpose: §5's controlled cases test known situations; natural speech tests
whether those situations occur at realistic rates and surfaces failure shapes a
script can't anticipate (already suggested by Test A's untagged "like"
observations in `real_human_validation_results.md`).

## 7. Scope: baseline only

EXP-M6-005 evaluates **Alternative A (current heuristic) only**. Alternatives B
and C are not implemented, tuned, or run here — see `README.md` "Baseline-first
sequencing" and §11/§12 below.

## 8. Metrics

**Primary — event-level** (SpeakLab's product surfaces discrete filler
occurrences/timestamps, e.g. `FillerOccurrence`, not a frame-level sequence label,
so event-level is the metric that matches what the product actually does; this is
a deliberate departure from some reviewed papers that report frame/segment-level
first — see `research_review.md` §"Why event-level is primary for SpeakLab"):

1. **Event-level precision** = correct final filler-event detections / all final
   filler-event detections
2. **Event-level recall** = correct final filler-event detections / all manually
   annotated spoken fillers (Layer A, `discourse-filler` class only — `ambiguous`
   excluded, see §9)
3. **Event-level F1** = harmonic mean of 1 and 2

**Event matching rule:** a detector-flagged token counts as matching a Layer-A
event if its timestamp falls within a stated tolerance of the annotated timestamp.

**Timing tolerance: `TBD BEFORE SCORING`.** Per explicit instruction, this value is
**not chosen now**, and specifically **not chosen by testing which value makes the
detector look best** — that would tune the evaluation criterion against the
evaluation data. It will instead be set **before any scoring happens**, during
annotation-protocol calibration: have the annotator(s) independently timestamp the
same handful of unambiguous events twice (or two annotators timestamp the same
events once each), measure the actual spread between those repeated/independent
timestamps, and set the tolerance from that measured human-timestamp precision —
not copied from any paper's value (e.g. PodcastFillers' 200ms is tuned to their own
annotation setup, not SpeakLab's, per `research_review.md`).

**Pipeline decomposition** (unchanged from the approved design, restated here for
completeness):

4. **STT filler recall** = Layer-A items where Whisper preserved (exact or
   normalized) / all Layer-A items (`discourse-filler` + `semantic`, ambiguous
   excluded — see §9)
5. **Downstream detector precision** = Layer-C items correctly flagged / all
   Layer-C items flagged
6. **Downstream detector recall, conditional on STT** = Layer-C items correctly
   flagged / Layer-B items that survived transcription and are `discourse-filler`
7. **End-to-end precision** = same as event-level precision (metric 1) — kept
   listed separately here only because it's part of the upstream/downstream
   decomposition story, not a different computation
8. **End-to-end recall** = same as event-level recall (metric 2), same note

**Optional diagnostic — segment/frame-level.** Not a mandatory success metric.
Computed only if, once real data exists, a specific failure-analysis question
needs it (e.g. checking whether a miss is a timing-alignment problem rather than a
classification problem, the way the semi-CRF paper used segment-level analysis
diagnostically). Never required for a baseline conclusion.

**False-positive categories**, kept as two separate tables, never combined into one
rate:
- **A. Semantic false positive** — token genuinely spoken and transcribed, used
  semantically, detector flags it anyway (e.g. "feels like").
- **B. Unsupported / hallucination-adjacent false positive** — detector flags a
  Whisper token with **no corresponding Layer-A entry at all**.

## 9. Ambiguous handling

`classification=ambiguous` (Layer A) is **excluded from every primary/pipeline
binary metric above** (1–8) — not counted as positive, not counted as negative.
Reported separately: count, `context_note` per item, whether Whisper preserved it,
whether the detector flagged it. This mirrors both reviewed handling strategies
(PodcastFillers' explicit exclusion of indeterminate short candidates; Dinkar et
al.'s treatment of filler/semantic ambiguity as a real linguistic property, not an
annotation defect) — see `research_review.md`.

## 10. Stopping signals for the pilot (not a fixed sample size)

Start with a small pilot covering every §5 row at least once, plus 2–3 natural
speech samples (§6). After the pilot, check:

- **Metric stability** — do the metrics in §8 stay roughly stable as a few more
  samples are added, or do they swing significantly? Swinging = pilot too small to
  trust yet; stable = probably enough for a qualitative (not statistical-
  significance) conclusion, consistent with how this project has always framed
  small real-human evidence (Tests A–D).
- **New failure-mode categories** — does each new recording keep surfacing
  categories already seen (§3), or genuinely new ones? New categories = keep
  collecting; only repeats = pilot is likely sufficient for a qualitative read.

This is a stopping *signal*, not a target number.

## 11. Alternatives (comparison targets — status as of the 2026-08-24 fix-design review)

**Terminology note:** the fix-design review conducted on 2026-08-24 (see
`research_review.md` "Fix-design review" for the full verified evidence) used its
own working letters (Option A/B/B′/D) for that conversation. This document keeps
its own original, stable lettering below — **A/B/C/D always mean the same thing
in this file**, and a **B′** entry is added alongside B rather than renumbering
anything. Where the two differ, this mapping applies: fix-design-review "Option
A" (improved heuristic) = this file's **B**; fix-design-review "Option B"
(standalone acoustic model) = this file's **C**; fix-design-review "Option B′"
(verbatim STT) = this file's new **B′**; fix-design-review "Option D" = this
file's **D**.

- **A — current heuristic.** The system under baseline evaluation in this
  experiment. Unchanged.
- **B — improved text/timestamp heuristic** (pause/word-gap, segment-boundary,
  token position, wider surrounding-word window, reused semantic-suppression
  logic). **Status: candidate experiment (EXP-M6-006), after baseline results
  exist** — targets root cause "downstream heuristic miss" only (Test D's
  preserved-but-rejected "like" tokens); cannot recover a filler the STT layer
  never emitted as a token. Not implemented in EXP-M6-005.
- **B′ — verbatim STT** (e.g. CrisperWhisper or an `initial_prompt`-seeded
  `base.en`, in place of or alongside the current transcription service).
  **Status: candidate experiment (EXP-M6-007), after baseline results exist** —
  targets root cause "upstream STT omission" (controlled_01's un-transcribed
  "um") directly, which no purely text-based fix (A or B) can reach. **Not
  selected as architecture** — a comparison candidate only. See
  `research_review.md` "Fix-design review" for verified feasibility facts
  (pretrained weights exist, CPU-capable, CTranslate2-compatible, **weights
  carry a non-commercial license**) and §"EXP-M6-007 provisional design" below.
  Not installed, not downloaded, not implemented.
- **C — standalone acoustic/disfluency model trained from the reviewed papers'
  approach** (e.g. the semi-CRF/S4 architecture). **Status: rejected for
  SpeakLab V1**, based on verified facts (not assumption): the reviewed
  implementation ([gzhu06/Filler-semi-CRF](https://github.com/gzhu06/Filler-semi-CRF))
  ships **no released pretrained weights**; its S4 component requires a
  **custom CUDA kernel** to train; **no CPU inference path is documented**;
  this project's development machine **has no CUDA** (DEC-017); the
  PodcastFillers dataset's **annotations carry a non-commercial license**; and
  the semi-CRF paper's own reported results (76.9% event-F1) sit **16 points
  below** its transcription-based comparator (92.8%) on the closest-available
  domain benchmark — published transcription-free results do not establish
  superiority over transcript-based approaches. **Rejected for V1 does not mean
  impossible forever** — revisit only if practical CPU-runnable pretrained
  weights, a compatible license, or materially different evidence become
  available.
- **D — conservative product approach** (e.g. UI copy such as "Possible fillers
  detected" instead of pipeline changes). **Status: open product question, not
  implemented.** Documented limitation: renaming "Detected fillers" to "Possible
  fillers detected" alone does **not** fully address the zero-result failure
  mode controlled_01 surfaced — a displayed `0` can still be read as "the
  detector listened faithfully and found none," when in fact a genuinely spoken
  filler may never have reached the detector at all (STT omission, not a
  detector judgment). A future copy decision should consider explicitly
  communicating upstream transcription uncertainty, not just detector-tier
  uncertainty. Does not depend on this experiment's results; remains available
  regardless of what baseline evaluation finds.

## 12. Decision criteria — final experiment sequence (locked 2026-08-24)

```
EXP-M6-005 (this experiment): current-pipeline baseline
   manual audio annotation → STT preservation (Layer B) →
   current detector (Layer C, observed production output) → end-to-end outcome
        │
        ├─ if downstream rule failure (Test-D-style: preserved token,
        │  detector still misses/false-positives) materially matters
        │  across the pilot, reproducibly and traceably to a specific
        │  rule branch →
        │       EXP-M6-006 — improved text/timestamp heuristic (Alternative B)
        │
        ├─ if upstream STT omission (controlled_01-style: filler never
        │  became a token at all) materially matters across the pilot →
        │       EXP-M6-007 — verbatim STT comparison (Alternative B′)
        │
        └─ if BOTH matter →
                only evaluate a combined architecture AFTER both EXP-M6-006
                and EXP-M6-007 have real results. The hybrid architecture is
                explicitly NOT pre-selected before that evidence exists.
```

**What would count as evidence for EXP-M6-006 (toward B):** downstream detector
precision/conditional-recall (metrics 5/6) showing a specific, reproducible
failure pattern across *multiple* recordings — not one sample like Test D —
traceable to a specific, nameable rule branch (via the experiment-only tracer
described in `annotation_schema.md`, never via production instrumentation),
**and** STT filler recall (metric 4) being high enough that downstream
improvements would actually move the end-to-end numbers.

**What would count as evidence for EXP-M6-007 (toward B′):** STT filler recall
(metric 4) being the dominant, reproducible error source across the pilot —
i.e. genuinely spoken fillers (like controlled_01's "um") repeatedly failing to
appear in `transcription.words` at all, independent of whatever the downstream
rule would have done with them.

**What would count as evidence for keeping the current heuristic + Experimental
status (status quo, possibly with D's copy change):** metrics 1–8 showing
meaningful instability across recordings (§10); or new failure-mode categories
still appearing late in the pilot (meaning the evaluation hasn't converged
enough to justify any code decision).

**C (standalone acoustic model) is not gated on pilot evidence at all** — it is
already rejected for V1 per the verified findings in §11 above, independent of
what EXP-M6-005/006/007 find. Revisiting it requires new external evidence
(released CPU-runnable weights, license, etc.), not more SpeakLab pilot data.

## EXP-M6-007 provisional design (high-level only — not scheduled, not run)

Gated on EXP-M6-005 showing upstream STT omission materially matters (§12
above). Documented now only so the comparison shape is on record.

**Compare, on the same frozen annotated pilot recordings used by EXP-M6-005:**
1. **Current transcription service** — `faster-whisper base.en` as shipped
   (DEC-017), unchanged.
2. **`base.en` with an experimentally-justified filler-preservation
   `initial_prompt`, if feasible** — cheapest candidate, zero new dependency,
   but carries a documented hallucination risk (aggravates RISK-004) that must
   itself be measured, not assumed acceptable.
3. **A verbatim-STT candidate** (e.g. CrisperWhisper) — targets the omission
   problem directly by design, at the cost of a non-commercial weights license
   and unmeasured latency/accuracy on SpeakLab's own audio.

**Metrics to measure (all currently unmeasured):**
- STT filler recall (the same Layer A/B metric EXP-M6-005 already defines)
- Non-filler transcript accuracy / degradation (does verbatim mode hurt the
  normal transcript SpeakLab already relies on?)
- Hallucination incidence (directly relevant to RISK-004)
- Timestamp usability (does word-level timing stay usable for pause detection,
  DEC-014, if the STT layer changes?)
- Latency / RTF, compared against DEC-017's existing `base.en` baseline
- Model size (download/footprint, relevant to DEC-007's local-first framing)
- Local CPU feasibility, verified on this project's actual machine, not just a
  model card's general claim
- Licensing constraints (the non-commercial weights license is a hard blocker
  on any future commercial use, independent of technical performance)

Not run. Not scheduled. No dependency added.

## 13. Limitations

- **Annotator subjectivity in Layer A** — discourse-filler vs. semantic vs.
  ambiguous is a judgment call; a single annotator (likely the project owner) has
  no inter-rater reliability check, unlike PodcastFillers' two-annotator-plus-
  adjudicator protocol (`research_review.md`), which is named as an aspirational
  future upgrade, not required for this pilot.
- **Small-sample instability** — §10 exists precisely because any metric from a
  pilot this size is directional, not statistically established.
- **Self-preference/self-scoring bias** — the same risk already named and
  corrected during M7A: whoever might later design an improved heuristic (B)
  should not be the sole judge of whether it improved on the same small annotated
  set used to discover the problem; Layer A annotation should be finalized before
  looking at detector output where practical.
- **Controlled speech may not transfer to natural speech** — §5's clean scripted
  cases could all pass while natural speech (§6) still fails in ways scripts can't
  anticipate (already the case comparing Test A to Tests B/D).
- **Cross-domain literature limits** — the four reviewed papers' own datasets
  (podcast conversation, telephone conversation) are not impromptu solo practice
  speech; their quantitative results inform expectations, never predict SpeakLab's
  numbers (`research_review.md`).
- **Timing tolerance is genuinely undetermined until calibration** (§8) — any
  metric computed before that calibration step would not be trustworthy, which is
  exactly why scoring cannot start before it.

## 14. Production code: explicitly out of scope

No production file is modified by this experiment at any stage:
`backend/app/services/metrics/fillers.py`, `pauses.py`, `service.py`, `base.py`,
`backend/app/services/transcription/faster_whisper_service.py`,
`backend/app/services/transcription/base.py`, all frontend code, all UI copy, and
`docs/decision-log.md` DEC-015's status/decision text. Any experiment-side
diagnostic tracing (see `annotation_schema.md`) reads production constants/helpers
via import only — it never adds a parameter, flag, or branch to production code,
and never generates a measured result (measured results always come from calling
the real, unmodified `detect_fillers()`).
