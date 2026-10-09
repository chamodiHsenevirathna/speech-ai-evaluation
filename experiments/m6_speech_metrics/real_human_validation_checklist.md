# M6A Real-Human Validation Checklist

**Purpose:** M6A's evidence is entirely synthetic (macOS TTS + `ffmpeg`-injected
silence) — see `conclusions.md` "Limitations of this experiment overall." DEC-014 and
DEC-015 are both marked **provisional**, not accepted, specifically because of this
gap. This checklist lets a human validate the M6A findings against real speech
**without committing any private audio** — every step below produces only text notes
or numbers you write down yourself, never a raw recording.

**Do not commit recordings.** Keep them local (they don't need to go anywhere near this
repo). Nothing in this checklist requires the recordings to be added to git — only your
written observations, if you choose to save them, are safe to keep as notes.

**Prerequisite:** the SpeakLab backend running locally (`backend/`, see its `README.md`)
with a way to inspect the transcript response — either the app's Processing/Results
screens once M6B wires metrics in, or by calling `POST /api/v1/attempts/audio` directly
(e.g. via `curl` or a short script) and reading the JSON response, since M6A did not
change the production API contract.

---

## Recording A — Natural speech (~30–60 seconds, normal conversational delivery)

Speak naturally about any topic (e.g. describe your day, explain a hobby) — no
scripted fillers or pauses, just talk normally.

**What to compare manually:**
- [ ] Does the transcript text roughly match what you actually said? Note any
      words that are clearly wrong (not just stylistically different).
- [ ] Does the reported `duration_seconds` roughly match how long you actually spoke
      (check against a stopwatch or your recording app's own duration display)?
- [ ] Roughly how many words did you say vs. the transcript's word count? (Rough
      count is fine — this isn't a WER computation, see "No automatic WER" below.)
- [ ] Does the computed WPM feel plausible for how fast you were actually speaking
      (clearly too fast, too slow, or about right)?

## Recording B — Controlled fillers + pauses

Deliberately include, in order, so each is easy to locate afterward:
1. An "um"
2. An "uh"
3. One **semantic** use of "like" (e.g. "It looks like it might rain.")
4. One **discourse/filler** use of "like" (e.g. "Like, I don't really know.")
5. A pause of approximately **1 second** (silently count "one-one-thousand")
6. A pause of approximately **2 seconds** (silently count "one-one-thousand,
   two-one-thousand")

**What to compare manually:**
- [ ] Does the transcript contain "um"? "uh" (or does it render as "ah" — this is a
      known, already-documented finding from M5/M6A; note whether it recurs)?
- [ ] Does the transcript correctly render both uses of "like"? (Transcription
      fidelity here is separate from whether a filler *detector* would classify them
      correctly — this step is just checking the transcript, not running detection
      logic, since M6A's detector code isn't wired into production yet.)
- [ ] If you inspect word-level timestamps (requires `word_timestamps=True` — not
      the production default yet per DEC-020's current state, so this may require a
      one-off local script using `faster_whisper` directly, similar to
      `evaluate_word_timestamps.py`): is there a word-gap roughly around your ~1s
      pause? Around your ~2s pause?
- [ ] **Write down the observed word-gap duration for each pause**, and compare it
      to your intended ~1s / ~2s. Per EXP-M6-002's finding, expect the observed gap
      to be somewhat *larger* than your actual pause, not identical — the question is
      whether the relationship still looks reasonably consistent (e.g. roughly
      proportional) on real speech, not whether it matches exactly.
- [ ] Would a 1.0-second threshold (DEC-014's current provisional value) have flagged
      both of your pauses? Would it have produced any false positives elsewhere in
      the recording (e.g. a natural breath or a normal word gap flagged incorrectly)?

## Recording C — Repetition

Deliberately include something like:
- "I think... I think the main reason is..." (immediate repeated phrase)
- "the the main issue..." (single-word stutter)

**What to compare manually:**
- [ ] Does the transcript preserve "I think, I think"? Or does it get smoothed to a
      single "I think" (per EXP-M6-004's finding on scripted repetition)?
- [ ] Does the transcript preserve "the the"? Or does it get smoothed to a single
      "the" (per EXP-M6-004's exact finding on the synthetic sample — this is the
      most directly comparable check to a result already in `results/repetitions.json`)?
- [ ] If a repetition **is** preserved in the transcript, would a human eyeballing it
      say "yes, that's clearly a repeat"? (No heuristic needs to be run — repetition
      detection is DEFERRED, this step is only checking transcription fidelity.)

---

## No automatic WER required

Per this task's explicit instruction: **do not compute WER unless you've manually
written out a reference transcript first.** If you want a WER number for Recording A,
write down exactly what you intended to say (or transcribe your own recording by ear)
before looking at the model's output, then it's fair to compute WER the same way
`experiments/m5_transcription/benchmark.py` does. Otherwise, the checklist items above
(rough word-match, "does this look right") are sufficient for M6A's purpose — sanity-
checking the synthetic findings, not producing a new formal benchmark.

## What to do with your notes

If any checklist item contradicts a specific M6A finding (e.g. a 1.0s threshold clearly
misses a real pause, or the "like"/"actually" context rule clearly fails differently
than documented), record that as a new observation — it's exactly the kind of evidence
DEC-014/DEC-015 need before they can move from provisional to accepted. Do not silently
adjust the threshold/vocabulary based on one informal recording; log the discrepancy
and treat a formal follow-up experiment (more samples, same rigor as EXP-M6-002/003) as
the next step, consistent with how DEC-017 (STT model choice) explicitly says a
real-user finding should prompt a new decision-log entry, not a silent change.
