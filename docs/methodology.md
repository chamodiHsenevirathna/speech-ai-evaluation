# Methodology

How the experiments in this repository were designed and reported. This describes the
practice visible in the experiment documents; it is not a claim of formal rigour.

## Structure of an experiment

1. **Hypothesis or question**, stated before the run.
2. **Plan**: samples, models, settings and what would count as informative.
3. **Run and raw results**, stored under each experiment's `results/` folder.
4. **Conclusions**, including what the experiment could *not* show.
5. **Decision**, recorded in [decision-log.md](decision-log.md) with a status such as
   Provisional or Accepted. Running an implementation does not upgrade a decision's status.

## Synthetic versus real speech

- **Synthetic (text-to-speech) audio** gives exactly known content and exactly known injected
  pauses, so results can be scored exactly. It is unrealistically clean and cannot show how a
  model behaves on accented, noisy or spontaneous speech.
- **Real-speech checks** are small, manual and qualitative. The speaker's description of what
  they said is self-reported, not independently verified, and the documents say so.
- Results from the two are never merged into one figure.

## Reliability tiers

Each measurement is labelled: **exact** (duration), **approximate** (word count and pace,
which inherit transcription errors, and pause detection, which infers from word timestamps),
or **experimental** (fillers). No composite score is produced.

## Failure decomposition (EXP-M6-005)

A single "fillers detected" count hides three different sources of error. The filler
evaluation separates them into annotation layers:

- **Layer A:** was a filler actually spoken (manual ground truth).
- **Layer B:** did the transcription keep it, drop it or change it.
- **Layer C:** if a token survived, did the detection rule classify it correctly.

Only one pilot event has been annotated, so this design has produced no scores.

## Reporting rules followed

- No numeric success threshold without a stated source; unsupported thresholds in the
  coaching plan were retracted and the correction left visible.
- Negative and blocked results are reported with the same prominence as positive ones.
- Self-scored outputs are labelled as such and are not treated as independent evidence.
- Literature is used to shape evaluation design and to corroborate decisions, and is
  labelled accordingly (see [research-provenance.md](research-provenance.md)). Published
  benchmark numbers are not treated as predictions for this project.
- Raw recordings, raw API output, model weights and licence-restricted model outputs are not
  published.

## Research-integrity rules

These are the rules the experiments were held to; several documents cite them.

- **Do not fabricate** metrics, benchmark numbers or test results. If something was not run
  or measured, say so plainly.
- **Preserve experiment evidence.** Results are not edited to make a conclusion look better;
  if a result was wrong, the experiment is re-run and the change recorded.
- **Do not treat model output as ground truth** without justification (Whisper can
  hallucinate on silence, smooth away repetitions, and its word gaps are not acoustic
  silence).
- **Do not silently change a model or its parameters** when that could change behaviour
  (model size, device, compute type, timestamp settings, thresholds taken from experiments).
  A change follows: reason, experiment, comparison against current behaviour, measured
  result, documented decision.
- **Do not turn an experimental metric into an authoritative claim.** Experimental results
  keep their label until evidence at a suitable scale exists.
- **Report negative results** such as a blocked approach as readily as positive ones.
- **Architecture-level changes** are proposed and recorded in the decision log before they
  are made.
