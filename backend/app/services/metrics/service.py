"""Speech-metrics orchestration.

Deliberately generic name (`SpeechMetricsService`, not "ImpromptuSpeechMetricsEngine")
- see base.py's module docstring on the shared-vs-mode-specific split. Pure
computation only; never touches HTTP/request concerns (see app/api/attempts.py for the
orchestration layer that calls this).
"""

import logging

from app.services.metrics.base import MetricsFailure, MetricsOutcome, MetricsSuccess
from app.services.metrics.fillers import detect_fillers
from app.services.metrics.pauses import detect_long_pauses
from app.services.metrics.wpm import compute_wpm
from app.services.metrics.word_count import count_words
from app.services.transcription.base import TranscriptWordResult

logger = logging.getLogger(__name__)

# Matches experiments/m6_speech_metrics/conclusions.md Step 14's final classification
# table - not invented confidence percentages, just the qualitative tiers M6A decided.
_RELIABILITY = {
    "duration_seconds": "exact",
    "word_count": "approximate",
    "words_per_minute": "approximate",
    "long_pauses": "approximate",
    "fillers": "experimental",
}


class SpeechMetricsService:
    def compute(
        self,
        *,
        transcript_text: str,
        words: list[TranscriptWordResult],
        duration_seconds: float | None,
    ) -> MetricsOutcome:
        if duration_seconds is None or duration_seconds < 0:
            return MetricsFailure(
                "INVALID_DURATION", "Recording duration is missing or invalid."
            )

        try:
            word_count = count_words(transcript_text)
            words_per_minute = compute_wpm(word_count, duration_seconds)
            long_pauses = detect_long_pauses(words)
            fillers = detect_fillers(words)
        except Exception:
            # Defensive - none of the pure functions above are expected to raise on
            # well-formed input, but a metrics failure must never take down the
            # request or destroy the already-successful transcript (see
            # docs/context.md "Metrics failure").
            logger.exception("Speech metrics calculation failed")
            return MetricsFailure(
                "METRICS_CALCULATION_FAILED",
                "Speech metrics could not be calculated for this recording.",
            )

        return MetricsSuccess(
            duration_seconds=duration_seconds,
            word_count=word_count,
            words_per_minute=words_per_minute,
            long_pauses=long_pauses,
            fillers=fillers,
            reliability=dict(_RELIABILITY),
        )
