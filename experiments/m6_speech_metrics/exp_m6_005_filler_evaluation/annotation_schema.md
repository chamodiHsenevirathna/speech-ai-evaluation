# EXP-M6-005 — Annotation Schema

Defines Layer A/B/C completely. See `plan.md` §4 for the narrative summary and
`research_review.md` for why this three-layer structure was chosen. **One pilot
recording, `controlled_01`, has Layer A and Layer B annotation** (see
`data/annotations/layer_a.csv`/`layer_b.csv`) — its single event's
`whisper_outcome` is `omitted`, so it correctly has **no Layer C row** (see "Layer
C population" below). This schema remains the authoritative structure for every
recording still to be annotated; nothing below is retroactively changed by that
one pilot event.

---

## Layer A — manual ground truth

One row per genuinely spoken filler-candidate moment, produced by **listening to
the raw audio only**, blind to the transcript and to any detector output (Layer A
must be finalized before Layer B/C are consulted, to reduce — not eliminate — the
self-preference/confirmation risk named in `plan.md` §13).

| field | values | notes |
|---|---|---|
| `recording_id` | string | |
| `annotator_timestamp_sec` | float, approximate | human-judged, not frame-exact — this is exactly what the §"Event matching rule" calibration step measures the precision of |
| `manually_heard_token` | free text | the literal word/sound the annotator heard, e.g. "uh," "um," "like" — kept even when it doesn't match the current 8-item vocabulary, so out-of-vocabulary spoken fillers are still visible in the data rather than silently discarded |
| `filler_type` | um / uh / ah / erm / like / you-know / actually / basically / other | "other" is not discarded — it's how a real spoken filler outside the current vocabulary gets captured |
| `classification` | discourse-filler / semantic / ambiguous | see "Ambiguous handling" below — never forced to a binary call when genuinely unclear |
| `annotator_confidence` | high / medium / low | self-reported, supports later disagreement/instability analysis (`plan.md` §10) |
| `context_note` | free text | e.g. "immediately after long pause," "sentence-initial," "mid-clause" — needed to cross-tab against the controlled-case matrix (`plan.md` §5) |
| `confounder_note` | optional: breath / laugh / repetition / none | only filled in when it might explain a detector miss or false positive later — **not** a full PodcastFillers-style confounder taxonomy (deliberately rejected, see `research_review.md` §1 "Not transferred") |

## Layer B — Whisper-output mapping

One row per Layer-A item, joined by `recording_id` + `annotator_timestamp_sec`
falling inside (or nearest to) a `faster-whisper` word's `[start_time, end_time]`.

| field | values | notes |
|---|---|---|
| `whisper_outcome` | preserved-exact / preserved-normalized / omitted / ambiguous-alignment | |
| `manually_heard_token` | (repeated from Layer A) | what the annotator actually heard |
| `whisper_token` | the actual `TranscriptWordResult.text`, or empty if omitted | what Whisper actually emitted |
| `normalized_token_in_vocabulary` | true / false | is `whisper_token` a member of `fillers.py`'s `_ALWAYS_FILLER`/`_AMBIGUOUS_SINGLE`? checked read-only against the imported production constants (see "Diagnostic tracing," never a new vocabulary decision) |
| `matched_word_start` / `matched_word_end` | float | |
| `punctuation_context` | comma-preceded / sentence-boundary-preceded / none / other | recorded per-recording, since Test D showed some real transcripts contain **zero** punctuation at all |
| `segment_boundary` | true/false — is this the first word of a new `TranscriptSegmentResult`? | plus the gap size to the previous word, if `segment_boundary=true` |
| `previous_word_gap_sec` | float, where available | gap between this word's `start_time` and the previous word's `end_time` — needed to check Test D's occurrence-3 pattern (filler immediately after a detected long pause) across more samples |

**`preserved-normalized` — exact meaning:** Whisper emitted a **different token
that still represents the same spoken event** the annotator heard (e.g. a spoken
"uh" rendered by Whisper as the word "um" — already observed once in real M6B
testing, `../real_human_validation_results.md` Test B). This is distinct from:
- `preserved-exact` — same token, same event.
- `omitted` — no token at all for this event.

This distinction is what lets the pipeline-decomposition metrics (`plan.md` §8,
metrics 4–6) cleanly separate two different upstream stories a single
preserved/omitted boolean would blur together: *spoken filler → STT changed its
lexical form → detector still had an opportunity* (counts as preserved for STT
recall, flows into downstream metrics) vs. *spoken filler → STT omitted it
entirely → detector never had an opportunity* (counts as an STT miss, correctly
excluded from downstream-conditional-on-STT metrics — not treated as a detector
failure).

## Layer C — detector outcome

### Layer C population — not every Layer A/B event gets a Layer C row

A Layer C row exists **only** for a Layer-B event where:

```
whisper_outcome ∈ { preserved-exact, preserved-normalized }
```

For:
- `whisper_outcome = omitted`, or
- `whisper_outcome = ambiguous-alignment` where no reliable detector opportunity
  can be established,

**no Layer C row is created.** This is intentional, not an annotation gap: Layer
C evaluates detector *behavior*, and detector behavior is only a meaningful
thing to evaluate for an event where the detector actually received a token to
classify. An event Whisper never preserved never reached `detect_fillers()` at
all — there is no detector decision to record, so recording one (even as some
"n/a" placeholder row) would misrepresent the event as having produced a
detector opinion when it didn't.

**Auditability:** the absence of a Layer C row for an omitted event does **not**
mean that event is unaccounted for. It remains fully traceable through **Layer A
→ Layer B** — Layer A records that it was genuinely spoken and how it was
classified; Layer B records that Whisper omitted it. That two-layer trace is
itself the complete, correct record for such an event. Its contribution to
end-to-end failure (§"How omitted events enter the metrics" below) is computed
*during evaluation* by reading Layer A/B directly — Layer C is never padded
with a duplicate row just to make every Layer A event visually present at every
layer.

For the population that **does** get a row (`preserved-exact`/
`preserved-normalized`):

| field | values | notes |
|---|---|---|
| `detector_flagged` | true/false | see "Observed vs. reproduced" below — for the pilot, this is read directly from the saved `metrics.fillers` field of that recording's own `data/raw/{recording_id}_response.json`, **not** recomputed |
| `detector_source` | `observed_production_response` (fixed value for this pilot) | records *how* `detector_flagged` was obtained, so a future reproduced-output column can never be silently confused with it (see below) |
| `manual_classification` | (repeated from Layer A) discourse-filler / semantic / ambiguous | |
| `agreement` | true/false, computed only when `manual_classification != ambiguous` | see the table below — no additional "n/a" state is needed, since an event with no genuine detector opportunity simply has no Layer C row to hold one |
| `rule_branch_reason` | free text, filled in manually only for failure-analysis cases (not every row) | e.g. "rejected: no comma, not sentence-initial" — a hand trace against `fillers.py`'s documented logic, not produced by running any tracer script in this pilot |

**`agreement`, evaluated only within Layer C's valid population** (i.e. only
where a row exists at all):

| `manual_classification` | `detector_flagged` | `agreement` |
|---|---|---|
| discourse-filler | true | true |
| discourse-filler | false | false |
| semantic | false | true |
| semantic | true | false |
| ambiguous | (either) | blank — never forced |

### How omitted events enter the metrics

An `omitted` event (Layer A + Layer B only, no Layer C row) still contributes to
evaluation — just not to Layer C's detector-behavior metrics:

- **STT filler recall** (`plan.md` §8 metric 4) — counts as a **miss**: it was a
  genuine Layer A `discourse-filler`, and Layer B shows it was not preserved.
- **End-to-end recall** (metric 2/8) — counts as a **miss**: the final
  `fillers[]` output could never have contained it, since no token reached the
  detector.
- **Downstream detector recall, conditional on STT** (metric 6) — **excluded**
  from the denominator entirely: this metric is scoped to events that survived
  transcription, and this one didn't.
- **Downstream detector precision** (metric 5) — contributes **nothing**: this
  metric is computed over the detector's actual predictions, and there was no
  detector prediction for this event at all (not a false prediction — no
  prediction).

`metrics.fillers=[]` (or any observed-response filler list not containing this
event) must never be read as "the detector rejected this token" when
`whisper_outcome=omitted` — the detector never received a token to accept or
reject. That interpretation is reserved for events that actually reached Layer
C (i.e. `preserved-*`) and were not flagged there.

### Observed production output vs. reproduced detector output

**`detector_flagged` for every pilot recording comes from that recording's own
saved API response — `metrics.fillers` in `data/raw/{recording_id}_response.json`
— never from re-invoking `detect_fillers()` in a REPL or script as the primary
measured result.** This is the **OBSERVED PRODUCTION OUTPUT**: the exact result
SpeakLab actually returned to the user for that attempt, at the time it was
recorded, preserving the original production execution. It survives even if
`fillers.py` changes later — a historical record shouldn't silently change
meaning because production code was edited after the fact.

Layer C workflow, in order:
1. Read `metrics.fillers` from the saved response.
2. Match each returned filler event against the corresponding Layer B / Layer A
   event (by timestamp, per the event-matching rule below).
3. Record `detector_flagged` (`detector_source=observed_production_response`).
4. Record `manual_classification` (carried from Layer A).
5. Record `agreement` where classification is not ambiguous.
6. Add `rule_branch_reason` manually, only where useful for failure analysis —
   not required for every row.

**REPRODUCED DETECTOR OUTPUT** — a later, independent call to the unchanged
production `detect_fillers()` (e.g. from `evaluate.py`, not built yet) run
against the same saved `transcription.words` — exists only as a
**reproducibility/consistency check**, never as the source of truth for a
historical label. If a reproduced result ever disagrees with an already-recorded
observed result, **that disagreement itself is the finding to investigate** (e.g.
a nondeterminism in the pipeline, or a `fillers.py` change since the recording was
made) — it must never silently overwrite the original observed row.

### Diagnostic tracing — explicitly not a second detector implementation

`detect_fillers()` and `fillers.py`'s constants/helpers (`_clean`,
`_ends_with_comma`, `_is_sentence_initial`, `_ALWAYS_FILLER`, `_AMBIGUOUS_SINGLE`,
`_COMPARISON_VERBS`) remain completely untouched — no debug flag, no optional
parameter, no tracing branch is added to production code.

When evaluation tooling is eventually built (not yet — see `README.md` "Tools" and
`plan.md` §14), `rule_branch_reason` will be produced by a **separate,
experiment-only script** (`tools/trace_current_filler_rules.py`, not created in
this session) that:

1. **Imports** the production module's existing pure helpers/constants directly —
   reuse, not reimplementation. The actual matching logic (what counts as "like,"
   a comparison verb, a comma) stays entirely delegated to the imported production
   code.
2. Combines them with the same simple boolean structure `fillers.py`'s own
   docstring already documents (`discourse_position = preceded_by_comma or
   sentence_initial`, etc.) purely to **label** which branch a given word fell
   into — this combination logic is orchestration, not the classification logic
   itself.
3. Runs strictly **after** the real `detect_fillers()` call, only to explain an
   already-final, already-measured result. It has zero influence on any measured
   metric.

**Explicit drift warning** (to be restated in the tracer's own file header once
written): if `fillers.py`'s branching *structure* changes (not just its
constants/vocabulary), this orchestration logic must be reviewed for drift, since
it mirrors — but is never invoked by — `detect_fillers()`.

**Measured detector output for every metric in `plan.md` §8 always comes from the
unchanged production `detect_fillers()` — never from the tracer.**

---

## Ambiguous handling (applies across Layer A/B/C)

`classification=ambiguous` is **excluded from every primary/pipeline binary
metric** in `plan.md` §8 — not folded into positive (discourse-filler) or negative
(semantic) ground truth. Reported separately instead: count, each item's
`context_note`, `whisper_outcome`, and `detector_flagged`. This exists specifically
so a case like Test D's "feel like" (occurrence 2 — plausibly semantic, not
confidently either way) can be discussed on its own terms rather than silently
inflating or deflating measured detector performance in either direction. See
`research_review.md` §Dinkar for the literature basis (ambiguity as a real
linguistic property, not an annotation defect) and §PodcastFillers (explicit
exclusion of indeterminate cases as precedent for *having* a stated rule, not for
this specific rule).

## False-positive categories (never combined)

- **A. Semantic false positive** — the token genuinely exists in the audio and
  transcript (correctly transcribed, really spoken), used semantically (e.g.
  "looks like," "feels like," literal "actually"/"basically"), and the detector
  flags it as filler anyway. Ground truth: Layer A `classification=semantic`
  joined to a Layer C `detector_flagged=true` row.
- **B. Unsupported / hallucination-adjacent false positive** — the detector flags
  a Whisper token as filler, but Layer A has **no corresponding entry at all** for
  that moment. Checked in the reverse direction: starting from every
  `detector_flagged=true` item and confirming a Layer-A match exists; if none
  does, it's category B.

These are always reported as two separate counts/tables, never summed into one
"false positive rate" — they point to different root causes (rule over-firing on
real semantic language vs. something closer to a transcription artifact).

## Event matching rule and timing tolerance

A detector-flagged token counts as matching a Layer-A event when its timestamp
falls within a stated tolerance of `annotator_timestamp_sec`.

**Tolerance rule (predeclared, before any scoring):**

```
event-matching tolerance =
    maximum absolute disagreement between the two independent manual
    timestamp annotations in the annotation-calibration set
```

This formula is fixed now, in advance of seeing calibration results — not chosen
after the fact from whichever value happens to look reasonable, and never chosen
by trying candidate values against `detect_fillers()` precision/recall/F1 and
picking whichever scores best. Doing the latter would tune the evaluation
criterion against the evaluation data, which is exactly the failure mode this
rule exists to prevent.

**Why "maximum," not a mean or a looser bound:** conservative for a small pilot,
directly tied to observed human annotation precision, and leaves no post-hoc
discretion once the calibration set is collected — the formula and the value it
produces are two separate, ordered steps (§9 of `collection_checklist.md`
governs the "collect the pairs" step; this document governs the "compute the
tolerance from them" step, which happens once, from this fixed formula, before
any scoring).

**This is explicitly a pilot-specific annotation tolerance** — a measurement of
how precisely one annotator can consistently timestamp an event in this specific
pilot's conditions, not a claimed general or optimal filler-detection threshold,
and not a value transferable to a different annotator, dataset, or evaluation
setup without its own recalibration.

**Outlier handling:** if the calibration set reveals one clearly anomalous
pair (e.g. one wildly larger disagreement than the rest, suggesting a
misheard/mistimed event rather than normal timestamp imprecision), it must
**not** be silently dropped to produce a smaller, more convenient tolerance.
Document the anomalous pair and what's suspected to have caused it, and revisit
the annotation procedure (e.g. is the audio unclear at that moment? was the
annotator interrupted?) before freezing the tolerance — the maximum is still
computed over the full calibration set as collected, including the outlier,
unless the annotation procedure itself is revised as a result and a fresh
calibration set is then collected under the revised procedure.

No specific numeric value (e.g. PodcastFillers' 200ms, tuned to their own
annotation setup) is adopted here or transferred from the literature — see
`research_review.md` §PodcastFillers "Not transferred."
