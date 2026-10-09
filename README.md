# speech-ai-evaluation

A small, honest research portfolio on evaluating speech AI for a speaking-practice tool: how well a local transcription model behaves, which speech measurements can be computed reliably, where filler-word detection breaks, and how an AI coach could be designed so it never invents evidence.

The work was done while building **SpeakLab**, a local-first impromptu speaking practice prototype. This repository contains the experiments, their evidence, the decisions they led to, and a small extract of the code under evaluation. It does **not** contain the application UI.

> **Status: research in progress.** Some experiments are complete but small and mostly synthetic. Others are explicitly unfinished. Nothing here is a validated accuracy claim, a reproduction of a published paper, or evidence that the tool improves anyone's speaking.

## Research questions

1. **Transcription.** Is a small local model (`faster-whisper` `tiny.en` / `base.en`, CPU only) good enough for interactive practice of about 60 seconds of speech? *(M5)*
2. **Measurement.** Which speaking measurements (duration, word count, pace, pauses, fillers, repetitions) can be computed by deterministic code, and how far can each be trusted? *(M6A)*
3. **Failure analysis.** When filler detection misses a filler, is the cause the transcription model or the detection rule? *(EXP-M6-005, EXP-M6-006)*
4. **Coaching design.** How can AI-written coaching be constrained to cite measured evidence, and how should it be evaluated without fabricating results? *(M7A)*

## Method

- **Hypothesis → experiment → result → decision.** Each experiment states a hypothesis and a plan, records what actually happened, and ends in an entry in the [decision log](docs/decision-log.md).
- **Synthetic versus real speech is always labelled.** Most controlled experiments use text-to-speech audio with exactly known content and pauses, which allows exact scoring but is unrealistically clean. Real-speech checks are small, manual and qualitative.
- **Reliability tiers, not scores.** Each measurement is classed as exact, approximate or experimental, and no composite "fluency score" is produced.
- **Negative results are recorded.** Failed approaches stay in the evidence and drive later decisions.
- **Thresholds need a source.** Numeric pass/fail lines were retracted from the coaching plan when no justification existed.

See [docs/methodology.md](docs/methodology.md), [docs/research-provenance.md](docs/research-provenance.md) and [docs/context.md](docs/context.md) (the pipeline and data contract the experiments evaluate).

## Experiments and what they established

| Experiment | What was done | What it established | Limits |
|---|---|---|---|
| [**M5** transcription](experiments/m5_transcription/) | `tiny.en` vs `base.en` on five synthetic TTS samples: latency and word error rate | Both ran well under real time on CPU, so `base.en` was kept as the default. Fillers were sometimes transcribed differently from the script. | Five clean synthetic samples cannot separate accuracy; the WER figures say nothing about real speech. |
| [**M6A** speech metrics](experiments/m6_speech_metrics/) | Word timestamps, pause detection, filler rules and repetition detection on synthetic samples with known content | Word-gap detection flagged every injected pause down to 0.5 s with no false alarm on a control clip, but it overstates real silence, so it is a presence flag only. A context rule reduced false positives for ambiguous words such as "like" on eight hand-labelled examples, with one miss. | Synthetic audio. Eight examples cannot support an accuracy claim. The 1.0 s pause threshold is provisional. |
| [**Real-speech checks**](experiments/m6_speech_metrics/real_human_validation_results.md) | Four single manual recordings | Pause detection behaved plausibly, with one possible false positive. In a limited manual test, Whisper omitted spoken filler words such as "um" and "uh" from the transcript, and the filler rule missed clearly filler-like "like" words because the transcript had no punctuation. | Four single samples; self-reported ground truth; not quantified. |
| [**EXP-M6-005** filler evaluation](experiments/m6_speech_metrics/exp_m6_005_filler_evaluation/) | A three-layer design separating "was it spoken", "did the STT keep it" and "did the rule classify it" | A complete design grounded in the filler-detection literature. | **Unfinished:** one pilot recording and one annotated event. No scores exist. |
| [**EXP-M6-006** timestamp-aware fillers](experiments/m6_speech_metrics/exp_m6_006_timestamp_aware_fillers/) | A candidate rule that uses pauses and segment boundaries | Candidate code whose 12 unit tests pass on designed, synthetic inputs. | **Unfinished.** Not evaluated on any recording, no evaluation scores exist, and it is not adopted. |
| [**M7A** coaching design](experiments/m7_grounded_coaching/) | Design, evidence hierarchy, technique library, rubric, failure taxonomy and 16 text-only test cases (mostly synthetic) | A design and evaluation framework. | **No coaching code was written and no model was run.** |

## What failed, what was learned, and how decisions changed

- **Voice-activity detection could not run** on the development machine because of a library incompatibility, so pauses are inferred from gaps between word timestamps instead. Re-checking the data then showed the gap overshoots true silence (a 0.5 s pause appeared as 1.0 s), so the claim was narrowed from "pause length" to "a long pause was detected" ([DEC-014](docs/decision-log.md)).
- **Silence was transcribed as a spurious word** by both models, and one repeated word was dropped. The silence artefact is recorded in the risk register; the dropped repetition is one reason repetition detection was deferred.
- **A real-speech test exposed a rule gap** that the synthetic set could not: the filler rule depends on punctuation that the transcription does not always provide. That led to the failure-decomposition design in EXP-M6-005.
- **An acoustic filler detector from the literature was rejected for this use** on practical and licensing grounds recorded in the EXP-M6-005 research review.
- **The coaching plan was corrected** to remove numeric thresholds that had no source, and to state that self-scored example outputs are subject to self-preference bias.

## What remains experimental or unvalidated

- Filler detection is rule-based and experimental. It has not been evaluated on real, labelled speech, and no precision, recall or F1 claim is made.
- The one-second pause threshold is provisional and derived from synthetic audio.
- Whisper's omission of fillers was observed in a limited manual test and is not a quantified rate.
- The M5 word error rates come from five synthetic samples.
- No transcription-free detector, automated coaching evaluation or coaching feature was implemented.
- No claim is made about coaching effectiveness or user improvement; there was no user testing.

## Not included

- **EXP-M6-007A**, a one-recording feasibility check of a verbatim-transcription model (CrisperWhisper), is not published. That model's licence defines its "Outputs" to include transcripts, timestamps and derived annotations, and requires anyone who publishes them to bind every recipient by contract to non-commercial terms. A public MIT repository cannot do that, so the results are withheld rather than summarised.
- **The M7A example coaching outputs** (hand-written design illustrations, scored by their own author) are withheld until an independent re-score has been done.
- **Recordings and raw API responses** from the real-speech checks, which are private.

## Reproducibility

| Experiment | Runnable here? | Needs |
|---|---|---|
| M5 benchmark | Yes | macOS (`say`), `ffmpeg`, Python 3.12; models are downloaded on first run (about 74 MB for `tiny.en`, 141 MB for `base.en`) |
| M6A evaluation scripts | Yes | The same; sample audio is regenerated, not stored |
| Unit tests (`backend/`, EXP-M6-006) | Yes | Python 3.12 and `pytest` |
| EXP-M6-005 | No | The raw recording, which is private; the design and the one-row pilot data are included |
| M7A | Nothing to run | Design documents only |

```bash
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

cd experiments/m5_transcription && bash generate_samples.sh && python benchmark.py
cd ../m6_speech_metrics && python generate_samples.py && python evaluate_pauses.py
cd ../../backend && python -m pytest
```

**What was checked.** In a brand-new Python 3.12.14 virtual environment (macOS 13, Apple M1), installed from `backend/requirements.txt`, with samples regenerated and the Whisper models read from the local cache:
- The unit tests passed: 43 in `backend/` and 12 for EXP-M6-006.
- The M5 benchmark reproduced the recorded word error rate and filler counts in all 10 rows; 9 of 10 transcripts were identical, and one differed by a single punctuation mark.
- The M6A filler and repetition results were identical to the recorded ones, and the pause-threshold verdicts matched; timing numbers differ between runs.

**One install pitfall.** `faster-whisper` 1.2.1 fails during real transcription with `av` 19, but the unit tests still pass because they mock the model. `backend/requirements.txt` therefore pins `av<19`.

Not tested: downloading the models from scratch, Linux, and Windows. The sample generators use macOS text-to-speech.

## Provenance, AI assistance and licensing

- **Research sources** are listed in [docs/research-provenance.md](docs/research-provenance.md), with what each influenced, whether it only corroborated a decision, and which were seen only as snippets. No paper was reproduced.
- **AI assistance.** AI tools were used to assist with coding, documentation, and research. Experiments and reported results were checked against the included scripts. Research decisions and interpretation remain the author's responsibility.
- **Licence.** The original code and documents are MIT-licensed ([LICENSE](LICENSE)). Third-party dependencies keep their own licences. `faster-whisper` and the Whisper `base.en` weights are MIT-licensed. No recordings, raw API responses, transcripts of real speech or model weights are included, and speaker descriptions are generalised.
