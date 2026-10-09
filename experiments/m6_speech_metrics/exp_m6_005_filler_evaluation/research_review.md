# EXP-M6-005 — Research Review

Four sources reviewed before finalizing `plan.md`, to ground EXP-M6-005's design in
established practice rather than reinventing an evaluation methodology from
scratch. Every claim below is tagged `[PAPER]`, `[SPEAKLAB]`, or `[HYPOTHESIS]` —
see `README.md` "Evidence-type discipline" for what each tag means. All four
sources were fetched and read directly (abstracts plus arXiv HTML full text for
all four; PDF also retrieved for two) — no claim here is sourced from memory alone
without a corresponding fetch.

**Explicitly not claimed anywhere in this document:** that transcription-free
detection is automatically better than transcription-based detection; that
acoustic models automatically solve filler detection; that PodcastFillers' results
will transfer directly to SpeakLab; that any published benchmark number is a
prediction of SpeakLab's own performance.

---

## 1. Zhu, Caceres, Salamon — *Filler Word Detection and Classification: A Dataset and Benchmark* (PodcastFillers), INTERSPEECH 2022

[arXiv:2203.15135](https://arxiv.org/abs/2203.15135) · [ISCA Archive PDF](https://www.isca-archive.org/interspeech_2022/zhu22e_interspeech.pdf) · [dataset site](https://podcastfillers.github.io/)

- **`[PAPER]` Filler definition / categories:** 5 filler classes — `uh` (17,907
  instances), `um` (17,078), `you know` (668), `like` (157), `other` (315) — plus
  **8 non-filler confounder categories**: laughter, breaths, agreement sounds,
  regular words, repetitions, simultaneous speakers, music, noise.
- **`[PAPER]` Annotation methodology:** two independent annotators per candidate, a
  third adjudicator on disagreement; reported agreement 98.4% (`uh`) / 96.4%
  (`um`). Candidates <150ms were **excluded outright** ("hard to determine by ear
  whether they were actual filler words or other sounds") — an explicit,
  documented rule for handling indeterminate cases, not a silent judgment call.
  Candidates >2s were also excluded as unrepresentative.
- **`[PAPER]` Evaluation metrics:** both **segment-based** (fixed time-grid
  comparison) and **event-based** (discrete event matching with a **200ms
  onset/offset slack**) F1; the authors state event-based metrics are "more
  suitable for measuring performance in practice."
- **`[PAPER]` ASR-error treatment:** the ASR-based pipeline assumes ASR omits
  non-lexical fillers as a *feature* (a gap in the transcript signals a filler
  candidate), but this assumption **fails under ASR errors or intentional
  omissions**, generating false candidates.
- **`[PAPER]` Modality:** both — VAD + ASR to find candidates, then an acoustic
  classifier (wav2vec embeddings shown to outperform log-mel features) to
  disambiguate filler vs. confounder.
- **`[PAPER]` Dataset:** 145 hours, 199 podcast episodes, 350+ speakers, English,
  SoundCloud-sourced.
- **`[PAPER]` False-positive analysis:** dominant confusion is filler vs. real word
  (acoustic similarity); `uh` confused with words more than `um` (the nasal `m`
  helps classification).
- **`[PAPER]` Limitations (paper's own):** domain-specific to podcasts; the authors
  cite prior findings that telephony-trained models degrade on naturalistic
  recordings — **the paper itself flags cross-domain transfer as unreliable**,
  before SpeakLab even asks the question. `[HYPOTHESIS]` This applies at least as
  strongly to a podcast→solo-impromptu-practice-speech transfer, an even larger
  domain gap than telephony→naturalistic.

**Borrowed:** the pattern of an explicit, stated exclusion rule for indeterminate
events (not the 150ms value itself); event-based matching with a stated timing
slack (not the 200ms value itself — see `plan.md` §8); reporting a false-positive
breakdown by confusion source, not one aggregate rate.

**Not transferred:** the full 8-category confounder taxonomy (SpeakLab's
recordings are single-speaker solo practice — most of these categories, e.g.
simultaneous speakers, music, are structurally near-impossible); the paper's own
145-hour/350-speaker benchmark numbers as any kind of SpeakLab performance
estimate.

---

## 2. Zhu, Yan, Caceres, Duan — *Transcription Free Filler Word Detection with Neural semi-CRFs*, ICASSP 2023

[arXiv:2303.06475](https://arxiv.org/abs/2303.06475) · [code](https://github.com/gzhu06/Filler-semi-CRF)

- **`[PAPER]` Motivation:** removes ASR dependency because commercial ASR isn't
  universally accessible (budget/language/compute) — an accessibility argument,
  **not** a claim that transcription-free is intrinsically more accurate.
- **`[PAPER]` Architecture:** S4 (structured state-space sequence model) + semi-CRF
  duration-aware sequence labeling, on top of a wav2vec encoder (5M params,
  explicitly *not* fully used, "to make the system deployable").
- **`[PAPER]` Results, on PodcastFillers:** event-level F1 76.9% (vs. 73.8% prior
  transcription-free CRNN baseline — a 3.1-point improvement). **The paper's own
  transcription-*based* comparator (AVC) reaches 92.8% event-F1** — a 16-point gap
  above the best transcription-free result reported in this same paper. The
  authors do not claim to beat ASR-based detection; they target ASR-unavailable
  scenarios specifically.
- **`[PAPER]` False positives/negatives:** confusion with phonetically similar
  words ("a," "the," "uh-huh," "oh," "I"), where the authors themselves state ASR
  "can provide more context for distinguishing those ambiguous cases" — i.e. the
  paper attributes part of ASR-based systems' advantage to context ASR supplies.
  Missed detections cluster on short, medial "uh" in linking-word position.
- **`[PAPER]` Compute:** 221k trainable params beyond the (excluded) 5M wav2vec
  encoder; explicitly slower than CRNN due to FFT/inverse-FFT cost in S4.

**Borrowed:** nothing architectural (no model is being adopted — see
"Why acoustic detection remains only a future candidate" below). The
event-vs-segment-level F1 divergence (6.4pt vs 3.1pt improvement between the two
lenses) is evidence supporting `plan.md` §8's decision to report event-level as
primary rather than assuming one lens tells the whole story.

**Not transferred:** any claim that this (or any) transcription-free approach is a
general upgrade over the current text-based pipeline — directly contradicted by
this paper's own 16-point gap versus its transcription-based comparator.

---

## 3. Romana, Koishida, Mower Provost — *Automatic Disfluency Detection from Untranscribed Speech*, 2023

[arXiv:2311.00867](https://arxiv.org/abs/2311.00867)

- **`[PAPER]` Disfluency categories:** filled pauses, partial words, repetitions,
  revisions, restarts — broader than "filler," includes structural speech-repair
  categories SpeakLab does not attempt (repetition/restart detection is already
  explicitly deferred, per Test A in `../real_human_validation_results.md`).
- **`[PAPER]` Dataset:** Switchboard — 8kHz **telephone conversation** speech
  (upsampled to 16kHz), MSU-corrected transcripts. **Not a stuttering/clinical
  population**, despite clinical application being named as a *motivating use
  case* rather than the evaluation domain.
- **`[PAPER]` Modality comparison, frame-level recall:**
  - Language-only (fine-tuned BERT) on **manual** transcripts: near-perfect on
    filled pauses (1.00), collapses on restarts (0.09).
  - The *same* language model on **ASR transcripts instead of manual ones**:
    weighted recall drops from 0.86 → 0.60 — a direct, quantified demonstration of
    ASR-error propagation into a downstream disfluency detector.
  - Acoustic-only (WavLM): beats the ASR-language pipeline on filled
    pauses/repetitions/revisions/partial-words (0.87 recall on filled pauses), but
    scores **0.00 recall on restarts** — a class needing semantic understanding
    acoustics alone can't supply.
  - Multimodal fusion: improves over both single-modality results, but **still
    requires ASR transcription and loading both unimodal models** — does not
    eliminate the ASR dependency, adds acoustic signal on top of it.
- **`[PAPER]` Limitations (paper's own):** evaluated only on Switchboard telephone
  speech; the authors explicitly leave generalization to natural, unrehearsed
  speech (and to pathological/stuttering speech) to future work.

**Borrowed:** the core insight that upstream/downstream error separation is a real,
measurable, and *already-demonstrated* phenomenon in the literature — direct
support for `plan.md`'s hypothesis (§2) and failure decomposition (§3).

**Not transferred:** the five-category disfluency taxonomy (out of SpeakLab's
product scope, per DEC-005/`ai-boundaries.md`); the Switchboard/telephone-speech
domain as any kind of stand-in for SpeakLab's recordings; the clinical/stuttering
framing (SpeakLab's coaching-evidence goal is a different problem from this
paper's stated clinical-treatment-planning motivation, and none of its evaluation
data is a stuttering population anyway).

---

## 4. Dinkar, Clavel, Vasilescu — *Fillers in Spoken Language Understanding: Computational and Psycholinguistic Perspectives*, 2022/2023

[arXiv:2301.10761](https://arxiv.org/abs/2301.10761) · [ACL Anthology](https://aclanthology.org/2022.tal-3.3/) · *Traitement Automatique des Langues* 63(3), 37–62

- **`[PAPER]` Ambiguity treatment:** frames fillers as occupying a genuinely
  ambiguous space between "paralinguistic phenomenon" (form: filled
  pause/interjection) and "meaningful speech unit" (function: hesitation,
  discourse marker) — the survey's own position is that this ambiguity is a real
  linguistic property, not an annotation-quality problem to be engineered away.
- **`[PAPER]` Annotation methodology:** documents the dominant Switchboard-style
  repair scheme (Reparandum/Interregnum/Repair), which treats fillers as
  **isolated edit tokens outside** that repair structure — a narrower framing than
  PodcastFillers' standalone filler-classification taxonomy. Flags that
  **transcriber experience measurably affects filler-annotation accuracy
  specifically**, more than other annotation categories.
- **`[PAPER]` ASR treatment of fillers — directly on-point for SpeakLab's own
  findings:** documents that off-the-shelf ASR systems (CMU Sphinx via filler-phone
  dictionaries, Google Cloud STT by mapping fillers to silence) **deliberately
  remove/normalize fillers by design**, and separately that fillers are "among
  some of the most likely tokens to be mis-transcribed" even when not deliberately
  filtered. `[SPEAKLAB]` This is independent literature confirmation of the exact
  upstream-omission failure mode Test D already surfaced empirically for
  `faster-whisper`/`base.en` — it upgrades Test D's finding from "one anecdotal
  sample" to "one sample consistent with a documented, general ASR behavior," not
  to a proven SpeakLab-scale rate.
- **`[PAPER]` Downstream-application guidance:** explicitly warns against assuming
  a **linear relationship** between raw filler frequency and any target construct
  (e.g. confidence/fluency) — cites research showing speakers use fillers
  stylistically before introducing new information, and listeners don't
  necessarily read that as low confidence. Names "inclusion of context" as an open
  research challenge, and robustness "in-the-wild" (vs. curated/pre-segmented
  datasets) as a known weak point of current systems.

**Borrowed:** the position that ambiguous filler/semantic cases are a real
property to represent, not resolve away — direct support for `plan.md` §9's
ambiguous-exclusion design. The explicit caution against a linear
filler-count-to-fluency reading is an independent reason (beyond SpeakLab's own
no-composite-score rule, `ai-boundaries.md`) to keep any future filler-based
coaching or UI language conservative.

**Not transferred:** the Switchboard repair-markup scheme itself (Reparandum/
Interregnum/Repair) — designed for structural self-repair, not the isolated-event
framing Layer A/B/C needs, and the survey itself notes fillers sit outside that
structure anyway.

---

## Why event-level is primary for SpeakLab (departure from some reviewed papers)

`[SPEAKLAB]` SpeakLab's product surfaces discrete filler *occurrences* with
timestamps (`FillerOccurrence` in `backend/app/services/metrics/base.py` —
`text`, `category`, `start_time`, `end_time`), not a frame-level sequence label
over the whole recording. `[PAPER]` Romana et al.'s frame-level metrics (25ms
frames, FER/WER-D) suit their goal of identifying which time regions to mask for a
downstream clinical/NLU pipeline — a different consumer than SpeakLab's, which
shows the user a list of moments, not a frame mask. `[PAPER]` PodcastFillers and
the semi-CRF paper both report event-level *alongside* segment-level, and the
semi-CRF paper states event-level is "more suitable... in practice" precisely
because of its discrete nature — the same reasoning applies more strongly to
SpeakLab, whose entire product surface is discrete events. `[HYPOTHESIS →
decision, recorded in `plan.md` §8]` Segment/frame-level analysis is kept as an
optional diagnostic tool (e.g. to check whether a miss is a timing-alignment
problem vs. a classification problem), never a required success metric.

## Why acoustic detection (Alternative C) remains only a future candidate

`[PAPER]` The literature gives genuinely mixed signal, not a green light:
Romana et al. show acoustic-only *can* outperform an ASR-transcript-based language
model specifically when ASR transcript quality is degraded (on filled pauses,
repetitions, revisions) — but on telephone speech, and it still scores 0.00 recall
on an entire disfluency category (restarts). The semi-CRF paper's own
transcription-free approach scores 16 F1 points *below* its transcription-based
comparator on the closest-available domain benchmark to SpeakLab (PodcastFillers).
`[HYPOTHESIS]` Combined, this supports treating acoustic/transcription-free
approaches as conditionally promising **specifically for the upstream-omission
failure mode that no text-based heuristic (current or improved) can ever reach** —
not as a general improvement, and not as a default next step. `plan.md` §12 states
the specific evidence (upstream omission shown to dominate over downstream error,
from EXP-M6-005's own baseline results) that would be needed before scoping any
future investigation of C — this document does not recommend starting that
investigation now, and none is scheduled.

---

## Fix-design review (2026-08-24) — verified feasibility facts

Following controlled_01 (a real, observed upstream-omission case) and Test D's
downstream rule gap, a fix-design review compared concrete options. The facts
below were **verified directly against the actual source repositories and
model cards** on 2026-08-24 (not recalled from training, not assumed from the
papers' general claims) — tagged `[VERIFIED-EXTERNAL]` since they come from
implementation artifacts, not the four academic papers reviewed above, and so
don't fit the `[PAPER]`/`[SPEAKLAB]`/`[HYPOTHESIS]` categories cleanly. Full
option-by-option reasoning lives in that review's chat output; this section
persists only the verified facts a future session would otherwise have to
re-derive.

### Standalone acoustic model (`plan.md` Alternative C) — verified infeasible for V1

`[VERIFIED-EXTERNAL]`, from [github.com/gzhu06/Filler-semi-CRF](https://github.com/gzhu06/Filler-semi-CRF)
(the ICASSP 2023 semi-CRF paper's own codebase):
- **No pretrained weights are released** — the repository ships training code
  only.
- The S4 model component requires a **custom CUDA kernel**, compiled from
  `extensions/cauchy/`.
- **No CPU inference path is documented anywhere in the repository.**
- Code itself is MIT-licensed, but that's irrelevant without weights to run.

`[VERIFIED-EXTERNAL]`, from the [PodcastFillers dataset site](https://podcastfillers.github.io/):
training data (needed to produce weights from scratch, since none exist) has
**non-commercial-licensed annotations**.

`[SPEAKLAB]` DEC-017 already established this project's development machine
has no CUDA (Apple Silicon, no NVIDIA GPU). Combined: training this specific
architecture here would require CUDA hardware this project doesn't have, on a
non-commercially-licensed dataset, to produce a detector whose own paper
reports underperforming its transcription-based comparator by 16 F1 points
(§ above). **Conclusion: rejected for V1** (formalized in `plan.md` §11) — not
"impossible forever," revisit only if released CPU-runnable weights, a
compatible license, or materially different evidence appear.

### Verbatim STT (`plan.md` Alternative B′, new) — candidate, not selected

`[VERIFIED-EXTERNAL]`, from [github.com/nyrahealth/CrisperWhisper](https://github.com/nyrahealth/CrisperWhisper)
and its HuggingFace model cards:
- Purpose-built to transcribe fillers/disfluencies verbatim (bracketed tokens
  `[um]`, `[uh]`, `[laughter]`) with word-level timestamps, rather than
  normalizing them away — directly targets the upstream-omission failure mode
  controlled_01 demonstrated.
- Pretrained weights **do exist**, on HuggingFace (`nyralabs/*`), in large /
  turbo / medium / **small** sizes.
- **CPU-capable** — documented pure-PyTorch macOS/Windows/CPU support.
- A CTranslate2-backed variant exists (`faster_CrisperWhisper`) — the same
  runtime family SpeakLab already depends on via faster-whisper (DEC-004,
  DEC-017), which lowers integration risk relative to an entirely new runtime.
- Code is MIT-licensed. **Model weights are licensed under the "Nyra Health
  Non-Commercial Research License"** — usable for this project's current
  status (DEC-007: portfolio/validation, not a production service) but a
  **hard blocker on any future commercial use** without a separate license.

`[VERIFIED-EXTERNAL]`, from public `faster-whisper`/`openai/whisper` GitHub
discussions on `initial_prompt`-based filler preservation (a zero-new-dependency
alternative path to the same goal, using the existing `base.en`): seeding a
filler-containing prompt does make Whisper more likely to emit "um"/"uh," but
multiple independently-reported cases describe it also **increasing
hallucination** and, in some cases, **losing entire sentences** — a real,
documented downside, not a hypothetical one, and one that directly aggravates
this project's own already-open RISK-004 (silence/lexical hallucination, from
M5).

**Conclusion: real candidate, unmeasured on SpeakLab's own audio.** Not
installed, not downloaded, not selected as architecture. See `plan.md`
"EXP-M6-007 provisional design" for what a future comparison experiment would
need to measure before any adoption decision.
