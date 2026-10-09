"""Speech-metrics types.

Deliberately generic ("speech metrics", not "impromptu speech metrics") - this engine
computes shared evidence (duration, word count, WPM, pauses) that isn't specific to any
one practice mode, and mode-specific evidence (fillers) that happens to be the only
mode-specific metric that exists today. See docs/context.md "Shared vs.
mode-specific split" and experiments/m6_speech_metrics/conclusions.md Step 9.
"""

from dataclasses import dataclass, field
from typing import Literal

MetricReliability = Literal["exact", "approximate", "experimental"]


@dataclass(frozen=True)
class PauseEvent:
    """A candidate long pause inferred from a gap between two word timestamps.

    Deliberately NOT a measurement of acoustic silence duration - `observed_gap` is
    the gap between Whisper's own word timestamps, which M6A found can diverge
    substantially from true silence (a 0.5s real pause measured as a 1.0s observed
    gap - see experiments/m6_speech_metrics/conclusions.md "What this detector
    actually measures"). Field names reflect this: there is no `duration_seconds`
    field here on purpose, to avoid implying an exact-duration claim anywhere this
    type is used (see docs/decision-log.md DEC-014's "Important correction").
    """

    previous_word_end: float
    next_word_start: float
    observed_gap: float
    threshold: float
    method: Literal["whisper_word_gap"] = "whisper_word_gap"


@dataclass(frozen=True)
class FillerOccurrence:
    """One detected filler/discourse-marker occurrence.

    `category` is the matched vocabulary item (e.g. "um", "like", "you know") -
    kept distinct from `text` (the literal transcript token(s) matched) in case they
    ever diverge (e.g. capitalization), though today they're normally the same.
    """

    text: str
    category: str
    start_time: float
    end_time: float


@dataclass(frozen=True)
class MetricsSuccess:
    duration_seconds: float
    word_count: int
    words_per_minute: float | None
    long_pauses: list[PauseEvent] = field(default_factory=list)
    fillers: list[FillerOccurrence] = field(default_factory=list)
    reliability: dict[str, MetricReliability] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricsFailure:
    code: str
    message: str


MetricsOutcome = MetricsSuccess | MetricsFailure
