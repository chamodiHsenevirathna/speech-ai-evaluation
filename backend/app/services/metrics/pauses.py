"""Long-pause detection - word-timestamp gap inference (DEC-014, "Approach A").

Method chosen at M6A over audio-level VAD, which is blocked on this development
machine by an onnxruntime/macOS ABI issue (see docs/decision-log.md DEC-014/DEC-017).
Threshold is PROVISIONAL (1.0s), based on synthetic TTS evidence only - see
experiments/m6_speech_metrics/conclusions.md "Why DEC-014's threshold isn't a final
number". Do not change this threshold based on implementation convenience; it changes
only via a new experiment + decision-log entry (see docs/methodology.md "Research-integrity rules").

Critically: `observed_gap` is NOT a measurement of acoustic silence duration - it is
the gap between two Whisper word timestamps, which M6A found can diverge substantially
from true silence (see base.py's `PauseEvent` docstring). Callers (the API layer, the
frontend) must never present this as an exact pause duration.
"""

from app.services.metrics.base import PauseEvent
from app.services.transcription.base import TranscriptWordResult

# DEC-014: provisional, word-gap inference threshold in seconds.
LONG_PAUSE_THRESHOLD_SECONDS = 1.0


def detect_long_pauses(
    words: list[TranscriptWordResult], threshold: float = LONG_PAUSE_THRESHOLD_SECONDS
) -> list[PauseEvent]:
    if len(words) < 2:
        return []

    events: list[PauseEvent] = []
    for previous, current in zip(words, words[1:]):
        gap = current.start_time - previous.end_time
        # A non-positive/negative gap means overlapping or non-monotonic timestamps -
        # not a real pause, and never large enough to reach a positive threshold
        # anyway, so no special-case branch is needed here; this comment documents
        # that the omission is deliberate, not an oversight.
        if gap >= threshold:
            events.append(
                PauseEvent(
                    previous_word_end=previous.end_time,
                    next_word_start=current.start_time,
                    observed_gap=gap,
                    threshold=threshold,
                )
            )
    return events
