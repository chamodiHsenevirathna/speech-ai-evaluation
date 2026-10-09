"""Unit tests for the deterministic speech-metrics engine (backend/app/services/metrics/).

Pure-function tests - no model, no HTTP, no I/O. API-level orchestration is covered
separately in test_attempts.py.
"""

from app.services.metrics.base import MetricsFailure, MetricsSuccess
from app.services.metrics.fillers import detect_fillers
from app.services.metrics.pauses import LONG_PAUSE_THRESHOLD_SECONDS, detect_long_pauses
from app.services.metrics.service import SpeechMetricsService
from app.services.metrics.word_count import count_words
from app.services.metrics.wpm import MIN_DURATION_SECONDS_FOR_WPM, compute_wpm
from app.services.transcription.base import TranscriptWordResult


def _word(text: str, start: float, end: float) -> TranscriptWordResult:
    return TranscriptWordResult(text=text, start_time=start, end_time=end)


# --- word_count ---------------------------------------------------------------


def test_word_count_simple_sentence():
    assert count_words("The quick brown fox jumps") == 5


def test_word_count_ignores_standalone_punctuation():
    assert count_words("Hello, world! How are you?") == 5


def test_word_count_preserves_contractions_as_one_word():
    assert count_words("I don't think that's right") == 5


def test_word_count_counts_digit_numbers_as_one_word_each():
    assert count_words("I have 23 apples and 4 oranges") == 7


def test_word_count_handles_extra_whitespace():
    assert count_words("  hello    world  \n\n") == 2


def test_word_count_empty_transcript_is_zero():
    assert count_words("") == 0


def test_word_count_whitespace_only_is_zero():
    assert count_words("   \n\t  ") == 0


# --- wpm -----------------------------------------------------------------------


def test_wpm_known_expected_result():
    # 60 words over 30 seconds (0.5 min) = 120 WPM.
    assert compute_wpm(60, 30.0) == 120.0


def test_wpm_zero_duration_returns_none_not_a_crash():
    assert compute_wpm(10, 0.0) is None


def test_wpm_near_zero_duration_returns_none():
    assert compute_wpm(1, 0.1) is None
    assert MIN_DURATION_SECONDS_FOR_WPM == 1.0


def test_wpm_empty_transcript_is_zero_not_none():
    # Zero words over a valid duration is a legitimate 0 WPM, not an error.
    assert compute_wpm(0, 30.0) == 0.0


def test_wpm_at_exactly_the_minimum_duration_computes():
    assert compute_wpm(1, MIN_DURATION_SECONDS_FOR_WPM) == 60.0


# --- pauses ----------------------------------------------------------------------


def test_pause_below_threshold_is_not_flagged():
    words = [_word("hello", 0.0, 0.5), _word("world", 0.5 + LONG_PAUSE_THRESHOLD_SECONDS - 0.1, 2.0)]
    assert detect_long_pauses(words) == []


def test_pause_exactly_at_threshold_is_flagged():
    words = [_word("hello", 0.0, 0.5), _word("world", 0.5 + LONG_PAUSE_THRESHOLD_SECONDS, 2.0)]
    events = detect_long_pauses(words)
    assert len(events) == 1
    assert events[0].observed_gap == LONG_PAUSE_THRESHOLD_SECONDS
    assert events[0].threshold == LONG_PAUSE_THRESHOLD_SECONDS
    assert events[0].method == "whisper_word_gap"


def test_pause_above_threshold_is_flagged():
    words = [_word("hello", 0.0, 0.5), _word("world", 3.5, 4.0)]
    events = detect_long_pauses(words)
    assert len(events) == 1
    assert events[0].observed_gap == 3.0


def test_multiple_gaps_are_all_detected():
    words = [
        _word("one", 0.0, 0.5),
        _word("two", 2.0, 2.5),  # 1.5s gap - flagged
        _word("three", 3.0, 3.5),  # 0.5s gap - not flagged
        _word("four", 5.5, 6.0),  # 2.0s gap - flagged
    ]
    events = detect_long_pauses(words)
    assert len(events) == 2
    assert events[0].observed_gap == 1.5
    assert events[1].observed_gap == 2.0


def test_no_words_produces_no_pauses():
    assert detect_long_pauses([]) == []


def test_single_word_produces_no_pauses():
    assert detect_long_pauses([_word("hello", 0.0, 0.5)]) == []


def test_non_monotonic_overlapping_timestamps_do_not_crash_or_flag():
    # Malformed/overlapping timestamps (next word starts before previous word ends) -
    # must not raise and must not be treated as a pause (negative gap never reaches a
    # positive threshold).
    words = [_word("hello", 0.0, 2.0), _word("world", 1.0, 3.0)]
    assert detect_long_pauses(words) == []


def test_custom_threshold_is_respected():
    words = [_word("hello", 0.0, 0.5), _word("world", 1.0, 1.5)]
    assert detect_long_pauses(words, threshold=0.3) != []
    assert detect_long_pauses(words, threshold=1.0) == []


# --- fillers (DEC-015 vocabulary/policy) ------------------------------------------


def test_filler_um_is_detected():
    words = [_word(" So,", 0.0, 0.3), _word(" um,", 0.3, 0.6), _word(" I", 0.6, 0.8)]
    occurrences = detect_fillers(words)
    assert [o.category for o in occurrences] == ["um"]


def test_filler_ah_is_detected_per_uh_to_ah_normalization_policy():
    # DEC-015: Whisper renders scripted "uh" as "ah" - the vocabulary accounts for
    # this, so "ah" itself is treated as a filler occurrence.
    words = [_word(" well,", 0.0, 0.3), _word(" ah,", 0.3, 0.6)]
    occurrences = detect_fillers(words)
    assert [o.category for o in occurrences] == ["ah"]


def test_filler_literal_uh_is_also_detected():
    words = [_word(" um,", 0.0, 0.3), _word(" uh,", 0.3, 0.6)]
    occurrences = detect_fillers(words)
    assert [o.category for o in occurrences] == ["um", "uh"]


def test_filler_like_semantic_comparison_is_not_counted():
    # "She looks like her sister." - comparison verb before "like" -> not a filler.
    words = [_word(" She", 0.0, 0.2), _word(" looks", 0.2, 0.5), _word(" like", 0.5, 0.7), _word(" her", 0.7, 0.9), _word(" sister.", 0.9, 1.3)]
    assert detect_fillers(words) == []


def test_filler_like_discourse_marker_is_counted():
    # "Like, I don't really know..." - sentence-initial discourse use.
    words = [_word(" Like,", 0.0, 0.3), _word(" I", 0.3, 0.5)]
    occurrences = detect_fillers(words)
    assert [o.category for o in occurrences] == ["like"]


def test_filler_actually_semantic_is_not_counted():
    # "The report was actually completed early." - no surrounding comma, mid-clause.
    words = [
        _word(" The", 0.0, 0.2),
        _word(" report", 0.2, 0.5),
        _word(" was", 0.5, 0.7),
        _word(" actually", 0.7, 1.0),
        _word(" completed", 1.0, 1.4),
        _word(" early.", 1.4, 1.8),
    ]
    assert detect_fillers(words) == []


def test_filler_actually_hedge_mid_sentence_is_counted_per_refined_dec_015_rule():
    # "So, actually, um, I forgot..." - comma-preceded, not sentence-initial. This is
    # exactly the case DEC-015's refined rule (comma-preceded, not only
    # sentence-initial) was written to fix - see experiments/m6_speech_metrics/
    # experiment_plan.md EXP-M6-003.
    words = [_word(" So,", 0.0, 0.2), _word(" actually,", 0.2, 0.5), _word(" um,", 0.5, 0.8)]
    occurrences = detect_fillers(words)
    assert {o.category for o in occurrences} == {"actually", "um"}


def test_filler_actually_sentence_initial_with_comma_is_counted():
    words = [_word(" Actually,", 0.0, 0.3), _word(" I", 0.3, 0.5), _word(" agree.", 0.5, 0.9)]
    occurrences = detect_fillers(words)
    assert [o.category for o in occurrences] == ["actually"]


def test_filler_basically_discourse_use_is_counted():
    words = [_word(" Basically,", 0.0, 0.3), _word(" we're", 0.3, 0.6), _word(" done.", 0.6, 0.9)]
    occurrences = detect_fillers(words)
    assert [o.category for o in occurrences] == ["basically"]


def test_filler_you_know_phrase_is_counted():
    words = [_word(" It", 0.0, 0.2), _word(" was,", 0.2, 0.4), _word(" you", 0.4, 0.6), _word(" know,", 0.6, 0.9), _word(" weird.", 0.9, 1.2)]
    occurrences = detect_fillers(words)
    assert [o.category for o in occurrences] == ["you know"]


def test_filler_empty_transcript_produces_no_occurrences():
    assert detect_fillers([]) == []


def test_filler_occurrences_carry_timestamps():
    words = [_word(" um,", 1.5, 1.8)]
    occurrences = detect_fillers(words)
    assert occurrences[0].start_time == 1.5
    assert occurrences[0].end_time == 1.8


# --- SpeechMetricsService (aggregation) -------------------------------------------


def test_service_reliability_metadata_matches_m6a_classification():
    outcome = SpeechMetricsService().compute(transcript_text="hello world", words=[], duration_seconds=10.0)
    assert isinstance(outcome, MetricsSuccess)
    assert outcome.reliability == {
        "duration_seconds": "exact",
        "word_count": "approximate",
        "words_per_minute": "approximate",
        "long_pauses": "approximate",
        "fillers": "experimental",
    }


def test_service_emits_no_repetition_related_field():
    outcome = SpeechMetricsService().compute(transcript_text="hello world", words=[], duration_seconds=10.0)
    assert isinstance(outcome, MetricsSuccess)
    field_names = {f for f in outcome.__dataclass_fields__}
    assert not any("repetit" in name for name in field_names)


def test_service_invalid_duration_is_a_failure():
    outcome = SpeechMetricsService().compute(transcript_text="hello", words=[], duration_seconds=None)
    assert isinstance(outcome, MetricsFailure)
    assert outcome.code == "INVALID_DURATION"

    outcome = SpeechMetricsService().compute(transcript_text="hello", words=[], duration_seconds=-1.0)
    assert isinstance(outcome, MetricsFailure)
    assert outcome.code == "INVALID_DURATION"


def test_service_computes_pauses_and_fillers_together():
    words = [
        _word(" So,", 0.0, 0.3),
        _word(" um,", 0.3, 0.6),
        _word(" I", 3.0, 3.2),  # 2.4s gap -> long pause
        _word(" agree.", 3.2, 3.6),
    ]
    outcome = SpeechMetricsService().compute(
        transcript_text="So, um, I agree.", words=words, duration_seconds=5.0
    )
    assert isinstance(outcome, MetricsSuccess)
    assert outcome.word_count == 4
    assert len(outcome.long_pauses) == 1
    assert len(outcome.fillers) == 1
    assert outcome.fillers[0].category == "um"
