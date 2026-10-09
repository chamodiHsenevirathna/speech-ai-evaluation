# speech-ai-evaluation

Research behind **SpeakLab**, a local-first impromptu speaking-practice prototype: how well a local transcription model behaves, which speech measurements can be trusted, where filler-word detection breaks, and how an AI coach could be designed so it never invents evidence.

This repository holds the experiments, their evidence, the decisions they led to, and a small extract of the code under evaluation. The SpeakLab application itself (its user interface and server) is not published here.

> **Status: research in progress.** Some experiments are complete but small and mostly synthetic; others are explicitly unfinished. Nothing here is a validated accuracy claim, a reproduction of a published paper, or evidence that SpeakLab improves anyone's speaking.

## 1. What is SpeakLab?

SpeakLab is a **local-first prototype** for practising impromptu speaking. The user is given a prompt, a short preparation countdown and about a minute to answer. The recording is transcribed on the user's own machine, turned into a few speech measurements, and shown back with each measurement labelled by how far it can be trusted. The intended design adds AI coaching that cites those measurements, but that part is a proposal, not working software (see [section 6](#6-current-implementation-versus-proposed-work)).

## 2. The problem and intended product experience

**The problem.** The project starts from the premise that general advice such as "be more confident" or "use fewer filler words" doesn't show a speaker *where* a problem happened or *what to try next*, and that specifics (where they paused, how their pace changed, which words they leaned on) plus one focused thing to change on the next attempt would help. This is a **product hypothesis**, not a finding: the project documents contain no user interviews or usability testing, so it is untested with real practisers.

**The intended experience** ([requirements](docs/requirements.md), [context](docs/context.md)):

```text
Prompt → 15 s preparation → record (~60 s) → transcribe → measure → show evidence
                                                               ↓ (proposed)
                       compare ← retry the same prompt ← one evidence-grounded retry goal
```

**How the pieces relate to that purpose:**
- **Transcription** produces the words and their timestamps. Everything else is computed from them, so transcription errors flow into every later measurement.
- **Speech measurements** (duration, word count, pace, long pauses, filler words) are computed by deterministic code, never by a language model. They are the *evidence* a user sees.
- **Grounded coaching** (proposed) would let an AI turn that evidence into one concrete suggestion, but it may only cite measured evidence and must never author a number ([AI boundaries](docs/ai-boundaries.md)).

## 3. Research questions and research foundations

**Questions investigated**

1. Is a small local model (`faster-whisper` `tiny.en` / `base.en`, CPU only) good enough for interactive practice? *(M5)*
2. Which speaking measurements can deterministic code compute, and how far can each be trusted? *(M6A)*
3. When a filler is missed, is the cause the transcription or the detection rule? *(EXP-M6-005, EXP-M6-006)*
4. How can AI-written coaching be constrained to cite evidence, and evaluated without fabricating results? *(M7A)*

**Sources that informed the work.** Full details, verification status and caveats are in [docs/research-provenance.md](docs/research-provenance.md). The relationship column says how each source was used.

*Filler-word and disfluency detection* (reviewed in the [EXP-M6-005 research review](experiments/m6_speech_metrics/exp_m6_005_filler_evaluation/research_review.md)):

| Source | Concept | Idea that informed SpeakLab | Relationship |
|---|---|---|---|
| Zhu, Caceres, Salamon (2022), [*Filler Word Detection and Classification: A Dataset and Benchmark*](https://arxiv.org/abs/2203.15135) | A podcast dataset and benchmark for filler words | How to *evaluate* detection: match events with a stated timing tolerance, set an explicit rule for indeterminate events, and report false positives by cause. Shaped the EXP-M6-005 evaluation design. | **Design inspiration** (method only; no dataset, model or numeric value was used) |
| Romana, Koishida, Mower Provost (2023), [*Automatic Disfluency Detection from Untranscribed Speech*](https://arxiv.org/abs/2311.00867) | Disfluency detection from text versus audio | Errors made by the transcription stage propagate into a detector built on its output (the paper reports a drop in recall on telephone speech). Supports separating "was it spoken", "did the transcription keep it" and "did the rule classify it". The failure mode was first seen in SpeakLab's own Test D; the paper was reviewed to ground the evaluation plan. | **Design inspiration / corroboration** |
| Dinkar, Clavel, Vasilescu (2022), [*Fillers in Spoken Language Understanding: Computational and Psycholinguistic Perspectives*](https://arxiv.org/abs/2301.10761) | A survey of how fillers are treated in language technology | The survey reports that some off-the-shelf recognisers remove or normalise fillers by design (it does not test Whisper); fillers are linguistically ambiguous; filler counts should not be read as a simple measure of fluency or confidence. Supports cautious wording and no composite "fluency score". | **Design inspiration / corroboration**: consistent with, not proof of, what Test D showed; no SpeakLab-scale rate follows from it |
| Zhu, Yan, Caceres, Duan (2023), [*Transcription Free Filler Word Detection with Neural semi-CRFs*](https://arxiv.org/abs/2303.06475) | Detecting fillers from audio without a transcript | An acoustic alternative to rule-based detection. The paper's own transcription-based comparison scored higher. The project's notes record no released weights, a custom GPU kernel and non-commercial data (not re-checked for this README). | **Rejected for this use**; not implemented |

*Evaluating LLM-generated coaching* (reviewed in the [M7A research review](experiments/m7_grounded_coaching/research_review.md)):

| Source | Concept | Idea that informed SpeakLab | Relationship |
|---|---|---|---|
| Pombal, Rei, Martins (2026), [*Self-Preference Bias in Rubric-Based Evaluation of Large Language Models*](https://arxiv.org/abs/2604.06996) | AI judges favour their own outputs | The M7A example outputs were scored by the same author that wrote them, which is the situation the paper describes. They are labelled as self-scored design sketches and withheld until independently re-scored. | **Design inspiration**; it changed M7A's conclusions |
| Mancoridis, Hitzig (2026), [*The Consistency Dilemma in LLMs: Generator-Evaluator Agreement and Vulnerability to Mistakes*](https://arxiv.org/abs/2606.30653) | A model that agrees with itself can still be consistently wrong | Planned repeat-run checks must score each run for groundedness, not just compare runs with each other. | **Design inspiration** (plan correction); the repeat-run experiment was not run |
| Han et al. (2026), [*How Trustworthy Are LLM-as-Judge Ratings for Interpretive Responses? Implications for Qualitative Research Workflows*](https://arxiv.org/abs/2604.00008) | Limits of AI judges on interpretive content | A future automated judge would only screen; people would review interpretive claims. | **Design inspiration**; no judge exists |
| Fourati et al. (2025), [*Probing Experts' Perspectives on AI-Assisted Public Speaking Training*](https://arxiv.org/abs/2507.07930) | Interviews with public-speaking experts | Experts wanted carefully selected, understandable feedback rather than a metrics dump. | **Corroboration** of the "one prioritised improvement" principle already adopted |
| Chu et al. (2026), [*FeedEval: Pedagogically Aligned Evaluation of LLM-Generated Essay Feedback*](https://arxiv.org/abs/2601.04574) | An evaluation framework for AI essay feedback | Its dimensions resemble the M7A rubric, which was written before the paper was found. | **Corroboration**; the paper's multi-rater method is not implemented |

Other sources (G-Eval, an essay-feedback trial, and papers seen only as snippets, which are not to be cited) are listed with their status in the provenance document. **No paper was reproduced.**

## 4. How research informed product and technical decisions

Each chain below runs: observation or research → design question → experiment → finding → decision. Findings (measured here) and literature claims (reported by others) are kept separate.

**A. Transcription errors versus filler-classification errors**
- *Observation (Test D, one recording):* the filler detector returned nothing, although the speaker reported deliberately saying "um", "uh" and "like". The speaker's account is self-reported, not independently checked against the audio.
- *Question:* did the transcription drop the fillers, or did the detection rule reject them?
- *Finding (this project, one sample):* two separable causes are visible. (1) "um" and "uh" do not appear in the transcript. This is consistent with Whisper omitting them, but cannot be distinguished from the speaker misremembering what they said. (2) All three "like" tokens survived transcription and none was flagged. The rule needs a comma or sentence boundary, and this transcript had no punctuation. Of the three, two read as filler-like and one as a legitimate comparison, which the rule correctly suppresses.
- *Literature (corroboration, not origin):* some recognisers remove fillers by design and errors propagate into detectors built on transcripts (Dinkar; Romana). Evaluation should separate error sources (Zhu 2022).
- *Experiment:* EXP-M6-005 designs a three-layer evaluation, but only a one-event pilot exists. EXP-M6-006 is an unscored candidate rule that uses pause and segment signals.
- *Decision:* filler detection stays labelled **experimental**; the filler rule and the transcription model were not changed in response to Test D; no accuracy claim is made. Whether omission or rule error dominates is **unknown**.

**B. Pause detection from word timestamps**
- *Observation:* audio-level voice detection could not run on the development machine (a library incompatibility with this macOS version), so pauses had to be inferred from word timestamps.
- *Experiment (EXP-M6-002, synthetic audio):* observed word gaps overshot the injected silence at every length tested. A 0.5 s pause appeared as a 1.00 s gap, so it reached the 1.0 s threshold only through that overshoot. The "no pause" control clip showed a 0.5 s gap that the report attributes to a text-to-speech sentence-boundary artifact, so the threshold may be tuned to synthetic audio.
- *Real speech:* one intentional pause (Test D) was flagged with a 5.38 s gap; in Test B, three events were flagged for two scripted pauses, one with no known cause. Both are single, qualitative samples.
- *Decision:* use the word gap as a **flag only**, never a duration; the 1.0 s threshold stays **provisional**. No paper informed this; it comes from the project's own small measurements.

**C. Evidence-grounding requirements for coaching**
- *Requirement:* an AI may interpret evidence but never author a measurement.
- *Question:* how do you evaluate coaching without fabricating results or trusting a self-scoring judge?
- *Literature (design inspiration; none of these studies speaking coaching):* AI judges favour their own work on general benchmarks (Pombal); self-consistency is not correctness in a clinical setting (Mancoridis); judges diverge from people on interpretive content in qualitative research (Han). Whether the same holds for speaking coaching is untested here.
- *M7A outcome:* a groundedness-first rubric, a plan (not run) for repeat-run checks that score groundedness per run, retraction of numeric thresholds that had no source, and self-scored examples withheld. No coaching was built or run.
- *Status:* coaching is a proposal. M7A recommends an independent re-score before its self-scored sketches count as more than a design illustration.

**D. A transcription-free detector**
- *Question:* would audio-based detection avoid fillers that the transcription omits?
- *Literature:* mixed signals. Romana et al. found audio-only detection can beat a transcript-based model when transcripts are poor, on telephone speech, yet it scored zero recall on restarts. The semi-CRF paper's own transcription-free model scored below its transcription-based comparator on podcast data.
- *Project notes (not re-checked for this README):* no released weights, a custom GPU kernel and non-commercial training annotations.
- *Decision:* **rejected for V1 and not implemented.** The plan says to revisit only if the project's own filler evaluation shows that upstream omission dominates, which has not been measured.

## 5. Experiments and findings

| Experiment | What was done | What it established | Limits |
|---|---|---|---|
| [**M5** transcription](experiments/m5_transcription/) | `tiny.en` vs `base.en` on five synthetic TTS samples | Both ran well under real time on CPU. `base.en` was chosen because latency was not the limiting factor and it is expected, not measured here, to be more robust on real speech. | Five clean synthetic samples cannot separate accuracy; WER says nothing about real speech. Silence produced a spurious word and one repeated word was dropped. |
| [**M6A** speech metrics](experiments/m6_speech_metrics/) | Timestamps, pauses, fillers and repetitions on synthetic samples | See chain B. A context rule suppressed two semantic uses ("looks like her sister", "actually completed…") on eight hand-labelled examples but missed one hedge use; the difference from unconditional matching is not meaningful at this size. | Synthetic audio; eight examples cannot support an accuracy claim. Repetition detection was deferred. |
| [**Real-speech checks**](experiments/m6_speech_metrics/real_human_validation_results.md) | Four single manual recordings | Pause detection behaved plausibly, with one possible false positive. In one test, spoken "um" and "uh" (self-reported) did not appear in the transcript; whether Whisper omitted them was not established. | Four single samples; self-reported ground truth; not quantified. |
| [**EXP-M6-005** filler evaluation](experiments/m6_speech_metrics/exp_m6_005_filler_evaluation/) | Three-layer evaluation design | A complete design, informed by the literature above. | **Unfinished:** one pilot recording, one annotated event, no scores. |
| [**EXP-M6-006** timestamp-aware fillers](experiments/m6_speech_metrics/exp_m6_006_timestamp_aware_fillers/) | A candidate rule using pauses and segment boundaries | 12 unit tests pass on designed, synthetic inputs. | **Unfinished.** Not evaluated on any recording; no scores; not adopted. |
| [**M7A** coaching design](experiments/m7_grounded_coaching/) | Design, rubric, technique library, failure taxonomy, 16 text-only cases | A design and evaluation framework (chain C). | **No coaching code, no model run.** |

## 6. Current implementation versus proposed work

| | Status |
|---|---|
| Recording, playback, local transcription with word timestamps, deterministic metrics with reliability labels, Results screen | **Implemented** in the SpeakLab application (not published here). This repository includes the transcription and metrics code as a [backend extract](backend/). |
| Filler detection, long-pause detection | Implemented but **experimental / provisional** (sections 4 and 5) |
| Evidence-grounded AI coaching | **Proposed design only** (M7A); not implemented |
| Retry goal and attempt comparison | **Placeholder screens with mock data** in the application; not implemented |
| Transcription-free or verbatim filler detection | **Not implemented** |
| Coaching evaluation with an independent judge | **Not implemented** |

## 7. Limitations and reproducibility

**Limitations**
- Filler detection is rule-based and experimental; it has not been evaluated on real, labelled speech, and no precision, recall or F1 claim is made.
- The one-second pause threshold is provisional and derived from synthetic audio; it flags a word-timestamp gap, not measured silence.
- Possible omission of fillers by Whisper was seen in one manual test relying on the speaker's own account; it is not a quantified rate and not a confirmed cause.
- The M5 word error rates come from five synthetic samples.
- No claim is made about coaching effectiveness or user improvement; there was no user testing.

**Not included.** Recordings and raw API responses (private); a one-recording feasibility check of a verbatim-transcription model, because its licence defines "Outputs" to include transcripts, timestamps and derived annotations and requires every recipient of published Outputs to be bound by contract, which a public MIT repository cannot do; and the M7A example outputs, withheld until an independent re-score.

**Reproducibility**

| Experiment | Runnable here? | Needs |
|---|---|---|
| M5 benchmark | Yes | macOS (`say`), `ffmpeg`, Python 3.12; models download on first run (about 74 MB `tiny.en`, 141 MB `base.en`) |
| M6A evaluation scripts | Yes | The same; sample audio is regenerated, not stored |
| Unit tests (`backend/`, EXP-M6-006) | Yes | Python 3.12 and `pytest` |
| EXP-M6-005 | No | The raw recording, which is private; the design and one-row pilot data are included |
| M7A | Nothing to run | Design documents only |

```bash
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

cd experiments/m5_transcription && bash generate_samples.sh && python benchmark.py
cd ../m6_speech_metrics && python generate_samples.py && python evaluate_pauses.py
cd ../../backend && python -m pytest
```

**What was checked.** In a brand-new Python 3.12.14 environment (macOS 13, Apple M1) installed from `backend/requirements.txt`, with samples regenerated and models read from the local cache: the unit tests passed (43 in `backend/`, 12 for EXP-M6-006); the M5 benchmark reproduced the recorded word error rate and filler counts in all 10 rows (9 of 10 transcripts identical, one differing by a punctuation mark); the M6A filler and repetition results were identical and the pause-threshold verdicts matched, with timings varying. `faster-whisper` 1.2.1 fails during real transcription with `av` 19 while the mocked unit tests still pass, so the requirements pin `av<19`. Not tested: downloading the models from scratch, Linux, and Windows.

## 8. Research references and AI-assistance disclosure

- **References.** Every cited paper, with its verification status and what it did and did not influence, is in [docs/research-provenance.md](docs/research-provenance.md). Method and research-integrity rules are in [docs/methodology.md](docs/methodology.md); decisions are in the [decision log](docs/decision-log.md) (an excerpt of the decisions the experiments cite). Bibliographic details of the papers above were re-checked against arXiv abstract pages, not full texts.
- **AI assistance.** AI tools were used to assist with coding, documentation, and research. Experiments and reported results were checked against the included scripts. Research decisions and interpretation remain the author's responsibility.
- **Licence.** The original code and documents are MIT-licensed ([LICENSE](LICENSE)). Third-party dependencies keep their own licences. `faster-whisper` and the Whisper `base.en` weights are MIT-licensed. No recordings, raw API responses, transcripts of real speech or model weights are included, and speaker descriptions are generalised.
