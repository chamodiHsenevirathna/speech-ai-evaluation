"""Approximate WPM.

Definition established at M6A (experiments/m6_speech_metrics/conclusions.md Step 3):
transcript-derived word count divided by TOTAL RECORDING DURATION in minutes - not
speech-only/pause-trimmed duration. This measures overall delivery pace across the
whole attempt (including any thinking pauses), not articulation rate. Deliberately not
"corrected" for pauses in M6B - see that document's "Total recording duration vs.
detected-speech duration" comparison for why total duration was chosen.
"""

# Below this duration, a word-count/duration ratio is not a meaningful pace figure -
# e.g. 1 word in 0.1s would compute to 600 WPM, which is a measurement artifact, not a
# real pace. Documented here rather than silently allowed to produce a nonsensical
# number (see M6B task: "handle... near-zero duration").
MIN_DURATION_SECONDS_FOR_WPM = 1.0


def compute_wpm(word_count: int, duration_seconds: float) -> float | None:
    if duration_seconds < MIN_DURATION_SECONDS_FOR_WPM:
        return None
    minutes = duration_seconds / 60.0
    return word_count / minutes
