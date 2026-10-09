# Research Provenance

What research the SpeakLab project drew on, how each source relates to what was actually built, and —
just as important — what the repository does **not** support claiming. This document
summarizes; the evidence lives in the files cited. Where this document and a cited file
disagree, the cited file wins.

Primary sources for this document:
[`experiments/m6_speech_metrics/exp_m6_005_filler_evaluation/research_review.md`](../experiments/m6_speech_metrics/exp_m6_005_filler_evaluation/research_review.md),
[`experiments/m7_grounded_coaching/research_review.md`](../experiments/m7_grounded_coaching/research_review.md),
[`docs/decision-log.md`](decision-log.md), and the `conclusions.md` file of each
experiment folder.


> **Scope of this repository.** The hand-written M7A coaching example outputs
> (`approach_*.json` and `summary.md` under `experiments/m7_grounded_coaching/results/`) and
> the EXP-M6-007A verbatim-STT smoke test are **not included** (see the README). Where this
> document describes them, it is describing work that is not published here.

## How to read the status labels

| Label | Meaning here |
|---|---|
| **Implemented** | The functionality exists in the SpeakLab application code. Only a backend extract (`backend/`) is included in this repository. |
| **Experimentally evaluated** | Tested in a limited experiment under `experiments/`. Not production evidence. |
| **Design inspiration** | Research that influenced a design or evaluation-method decision. |
| **Corroboration** | Research found *after* a design decision that agrees with it. It is **not** the origin of that decision. |
| **Considered, not implemented** | Evaluated and rejected, or deferred. |
| **Unverified** | Seen only as a search snippet or abstract, or not fully checked. Do not cite for claims. |

**Verification note.** Bibliographic details below are those recorded in the two research
reviews. For the papers marked "metadata re-checked", title, authors and year were also
compared against the arXiv abstract page on 2026-10-10. That check covered the abstract
page only — it does not mean the full text was re-read. Whether the full text was read at
the time of the original review is as stated in each review ("fetched" vs "snippet").

## 1. Summary

SpeakLab is **not** an implementation or replication of any single paper. The shipped
metrics (duration, word count, WPM, long pauses, fillers) are deterministic Python rules
built on `faster-whisper` output. Their design came from SpeakLab's own measurements
(M5, M6A, real-human tests A–D). Research papers were used mainly to:

1. design how filler detection should be *evaluated* (EXP-M6-005),
2. justify keeping acoustic/transcription-free detection out of V1, and
3. set limits and cautions for how coaching quality may be evaluated later (M7A).

No source in the repository supports a claim of measured accuracy, coaching
effectiveness, or user improvement.

## 2. Implemented functionality (software choices, not research)

These are engineering decisions recorded in the decision log. They rest on the project's
own experiments, not on a paper. No paper is cited in the SpeakLab application source (the backend extract here, or the frontend, which is not included).

| Component | Where | Basis |
|---|---|---|
| Local transcription with `faster-whisper` (`base.en`, CPU, int8), lazy-loaded | DEC-004, DEC-017; `backend/app/services/transcription/` | M5 benchmark (see §4) |
| Word-level timestamps | DEC-020; `faster_whisper_service.py` | EXP-M6-001 |
| Long-pause detection: gap between consecutive Whisper word timestamps ≥ 1.0 s | DEC-014; `backend/app/services/metrics/pauses.py` | EXP-M6-002 (synthetic audio) |
| Filler detection: rule-based vocabulary with context-sensitive matching for ambiguous words | DEC-015; `backend/app/services/metrics/fillers.py` | EXP-M6-003 (8 examples) |
| Duration, word count, WPM | `backend/app/services/metrics/` | Arithmetic; definition fixed at M6A |

Not cited anywhere in the repository: the Whisper paper, a faster-whisper or CTranslate2
publication, a Silero VAD publication, a published speaking-pace norm. Statements such as
"Whisper hallucinates on silence" are the project's own M5 observations or described as
"known behavior" without a citation.

## 3. Filler and disfluency research (M6 track)

Reviewed in `experiments/m6_speech_metrics/exp_m6_005_filler_evaluation/research_review.md` (four sources, per that file
fetched as abstract plus arXiv HTML full text).

| Source | Status | How it relates to SpeakLab |
|---|---|---|
| Zhu, Caceres, Salamon (2022). *Filler Word Detection and Classification: A Dataset and Benchmark.* Interspeech 2022. [arXiv:2203.15135](https://arxiv.org/abs/2203.15135). Metadata re-checked. | **Design inspiration** (evaluation method only) | EXP-M6-005 borrows *patterns*: event-based matching with a stated timing tolerance, an explicit exclusion rule for indeterminate events, and a false-positive breakdown by cause. It does **not** copy the paper's numeric values and does not use its dataset or model. |
| Romana, Koishida, Mower Provost (2023). *Automatic Disfluency Detection from Untranscribed Speech.* [arXiv:2311.00867](https://arxiv.org/abs/2311.00867). Metadata re-checked. | **Design inspiration / corroboration** | Supports EXP-M6-005's decomposition of errors into "spoken", "kept by STT" and "classified correctly". The failure mode itself was first observed in SpeakLab's own Test D; the paper was reviewed to ground the plan. |
| Dinkar, Clavel, Vasilescu (2022). *Fillers in Spoken Language Understanding: Computational and Psycholinguistic Perspectives.* Traitement Automatique des Langues 63(3), 37–62; [arXiv:2301.10761](https://arxiv.org/abs/2301.10761). Metadata re-checked. | **Design inspiration / corroboration** | Supports treating ambiguous filler/word cases as a real property, using cautious user-facing wording, and not equating filler count with fluency. The review states it is "consistent with" SpeakLab's own observation that Whisper can omit fillers; it does not quantify it. |
| Zhu, Yan, Caceres, Duan (2023). *Transcription Free Filler Word Detection with Neural semi-CRFs.* ICASSP 2023. [arXiv:2303.06475](https://arxiv.org/abs/2303.06475). Metadata re-checked. | **Considered, not implemented** | A transcription-free acoustic detector. Rejected for V1 in the review: per its notes, no pretrained weights are released, the model needs a custom CUDA kernel, and the training dataset's annotations are non-commercial; the paper's own transcription-based comparator scored higher. Those code/dataset facts come from the project's earlier reading of the authors' GitHub repository and dataset site and have **not** been re-checked for this document. |

**Not transferred from these papers:** published benchmark numbers, class taxonomies,
and the 150 ms / 200 ms constants. The review and `plan.md` state these are not adopted.

## 4. Experimental evidence behind the shipped metrics

Each item is a limited experiment. None supports a claim of general accuracy.

| Evidence | What it was | Limit |
|---|---|---|
| **M5 transcription benchmark** (`experiments/m5_transcription/`) | `tiny.en` vs `base.en` on **five synthetic text-to-speech samples**, reporting latency, real-time factor and WER against hand-written references. Basis for DEC-017. | Synthetic TTS audio is unusually clean. The experiment itself says it cannot differentiate model accuracy. The WER figures do **not** establish real-world transcription accuracy. |
| **EXP-M6-001** word timestamps | 10 samples with and without word timestamps; latency overhead and whether the largest word gap overlapped known injected pauses. | Synthetic samples. |
| **EXP-M6-002** pause detection | Word-gap inference compared with VAD on synthetic audio with injected pauses. VAD could not run on the development machine (onnxruntime/macOS ABI error). | Synthetic audio. The 1.0 s threshold is **provisional**. Observed word gaps overshoot true silence (the 0.5 s injected pause appeared as 1.00 s), so the detector flags a *thresholded word gap* and is **not** a measurement of silence. |
| **EXP-M6-003** filler detection | Unconditional vs context-sensitive matching on **8 hand-labelled synthetic examples**. Basis for DEC-015. | Far too small for any accuracy claim. No precision, recall or F1 claim is made. `DEC-015` records the scores that this tiny set produced; they are bookkeeping for that experiment, not estimates of real-world performance, and are intentionally not repeated here. |
| **Real-human tests A–D** (`real_human_validation_results.md`) | Four single manual recordings, qualitative observations only. | Single samples. Test D observed that Whisper omitted spoken "um"/"uh" and that the punctuation-dependent rule rejected clearly filler-like "like" tokens. This is described as an **observed limitation** in these recordings, not a quantified general rate. |
| **EXP-M6-005** filler evaluation | Design for a baseline evaluation with three annotation layers. **Partial**: one pilot recording and one annotated event. | No scores computed; none should be inferred. |
| **EXP-M6-006** timestamp-aware fillers (unfinished) | Candidate rule using pause/segment signals. | Candidate code only; "do not score it yet" per its own README. Not implemented in the application. |
| **EXP-M6-007A** verbatim-STT smoke test | One recording, one candidate model (CrisperWhisper small). | **Not published here.** The model's licence treats timestamps and derived annotations as restricted "Outputs", and its terms for publishing them have not been cleared (see the README). | Its findings are deliberately not summarised. |

## 5. Grounded-coaching research (M7A track)

M7A is a **design and evaluation-framework milestone**. No coaching code exists in the
application, and no Gemini or other model call was made.

### What the M7A "results" are

The files under `experiments/m7_grounded_coaching/results/` are **hand-written design
illustrations** authored by Claude, the agent doing the design work. They are **not**
model-generated coaching results, not a benchmark of Gemini or any model, and not evidence
of output quality, latency or cost. The rubric scores attached to them are **self-scores**:
the same author wrote the outputs and scored them. That setup is the one described by the
self-preference-bias paper below, so the comparison pattern in the withheld `results/summary.md`
("Approach C" scoring highest) is a **design sketch, not a validated result**, until an
independent re-scoring pass is done.

### Sources

Papers were found by a web search during M7A and reviewed after the design had been
drafted. The review records that several of its design choices were reached
independently first. They are therefore described below as **corroboration** unless
stated otherwise.

| Source | Status | Relation |
|---|---|---|
| Pombal, Rei, Martins (2026). *Self-Preference Bias in Rubric-Based Evaluation of Large Language Models.* [arXiv:2604.06996](https://arxiv.org/abs/2604.06996). Metadata re-checked. Read as "fetched" per review. | **Design inspiration** (changed the conclusions) | The one source that altered M7A: it added the self-scoring limitation to `conclusions.md` and `results/README.md`. The bias magnitudes in the paper are not SpeakLab's. |
| Mancoridis & Hitzig (2026). *The Consistency Dilemma in LLMs: Generator-Evaluator Agreement and Vulnerability to Mistakes.* [arXiv:2606.30653](https://arxiv.org/abs/2606.30653). Metadata re-checked. | **Design inspiration** (plan correction) | `experiment_plan.md` EXP-M7-004 requires per-run groundedness scoring in addition to run-to-run consistency. EXP-M7-004 has **not been run**. |
| Han et al. (2026). *How Trustworthy Are LLM-as-Judge Ratings for Interpretive Responses? Implications for Qualitative Research Workflows.* [arXiv:2604.00008](https://arxiv.org/abs/2604.00008). Metadata re-checked. | **Design inspiration** (principle only) | Any future automated judge would only screen; humans keep review of interpretive claims. No judge exists. |
| Fourati et al. (2025). *Probing Experts' Perspectives on AI-Assisted Public Speaking Training.* [arXiv:2507.07930](https://arxiv.org/abs/2507.07930). Metadata re-checked. | **Corroboration** | Agrees with the "one prioritized improvement" principle that M7A had already adopted. It is an interview study of experts about commercial tools; it is not evidence about SpeakLab's users. |
| Chu et al. (2026). *FeedEval: Pedagogically Aligned Evaluation of LLM-Generated Essay Feedback.* [arXiv:2601.04574](https://arxiv.org/abs/2601.04574). Metadata re-checked. | **Corroboration; not implemented** | M7A's `evaluation_rubric.md` was written before the paper was found and was noted as matching it in spirit. FeedEval's method (multiple trained annotators, inter-rater agreement) is **not** implemented. |
| Liu et al. (2023). *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment.* [arXiv:2303.16634](https://arxiv.org/abs/2303.16634). Metadata re-checked. Marked "snippet" in the review. | **Considered, not implemented** | Deferred as a possible future way to scale evaluation. No G-Eval-style judge exists in the repository. |
| Lu et al. (2026). *AI-Mediated Feedback Improves Student Revisions: A Randomized Trial with FeedbackWriter in a Large Undergraduate Course.* [arXiv:2602.16820](https://arxiv.org/abs/2602.16820). Metadata re-checked. | **Considered, not implemented** | An essay-revision study with a human in the loop. Used to frame a *future* retry experiment; it is not evidence that SpeakLab's retry goals help. |

### Unverified or not used

Recorded in the review as snippet-only, grouped or lower-confidence, and **not to be
cited**: arXiv 2606.27380 (presentation-coaching survey), 2603.23714, 2601.11541,
2509.23412, 2602.05125, 2605.29857, 2606.17507, the Frontiers and Springer articles on
AI versus teacher feedback, and a Hechinger Report article. Pronunciation-assessment
papers (arXiv 2104.01378 and four others) are a **future track only** and do not affect
the application.

Toastmasters roles and the technique library are described in `technique_library.md` as
common public-speaking advice patterns. They are practitioner-inspired and **not**
research-derived.

## 6. Considered but not implemented (summary)

| Approach | Outcome | Reference |
|---|---|---|
| Audio-level voice activity detection for pauses | Blocked on the development machine; word-gap inference used instead | DEC-014, M5 conclusions |
| Transcription-free acoustic filler detector | Rejected for V1 | §3; EXP-M6-005 research review |
| Verbatim STT (CrisperWhisper) | Tried once on a single recording; results withheld because of the licence terms on Outputs; not adopted | DEC-006 |
| Seeding `initial_prompt` to preserve fillers | Rejected on reported hallucination risk (from public discussions summarized in the review; not tested here) | EXP-M6-005 research review |
| Repetition/restart detection | Deferred | M6A conclusions |
| Automated LLM coaching judge, inter-rater study, coaching-driven retry experiment | Deferred to M7B/M8 | `experiments/m7_grounded_coaching/` |

## 7. What this project does not claim

- It does not reproduce or replicate any paper, and uses no paper's dataset, model or
  numeric threshold.
- It does not claim measured accuracy for filler or pause detection. The filler detector
  is rule-based and experimental. The pause threshold is provisional.
- The 1.0 s pause threshold is **not** research-derived and is **not** a measurement of
  silence; it flags a gap between two Whisper word timestamps.
- It does not claim Whisper's behavior in general. It reports that, in the project's own
  recordings, `faster-whisper` `base.en` omitted some spoken fillers.
- It does not claim real-world transcription accuracy; the M5 WER figures are from five
  synthetic samples.
- It does not implement a transcription-free filler detector, G-Eval, FeedEval, or any
  automated coaching evaluation.
- It has no coaching feature. M7A outputs are hand-written illustrations with
  self-scoring, not model results.
- It claims no coaching effectiveness, measured user improvement, or production
  readiness.
- Research found after a design decision is corroboration, not the source of that
  decision.

## 8. Open items

- **Order of decision and paper is only partly recorded.** The M7 review states that the
  "one prioritized improvement" principle and the rubric dimensions were reached before
  the corresponding papers were found, so those papers are corroboration. For the other
  sources the records label the outcome ("Adopt", "Defer", "Borrowed", "Not transferred")
  but do not say whether the paper or the design came first. This document uses the
  records' own labels and does not claim an origin the records do not establish.
- Read the snippet-only M7 sources in full before citing any of them.
- Independent re-scoring of the M7A illustrations (a different session or a human).
- EXP-M6-005: collect a real annotated set before any filler accuracy statement.
- The code and dataset facts about arXiv:2303.06475 and the Whisper `initial_prompt`
  discussions come from earlier project notes; re-verify before publishing them as fact.
