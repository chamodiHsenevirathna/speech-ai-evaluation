"""
Unit tests for EXP-M6-006's candidate.py.

These tests verify only that the candidate implementation matches its
specified behavior (design.md) on designed cases. This is IMPLEMENTATION
VERIFICATION, not model/evaluation evidence - it says nothing about how the
candidate performs on real recordings. See README.md "Do not score it yet."
"""

# Snapshot note: neighbouring words in the fixtures below were replaced with the neutral
# token " word" before publication (they came from a real recording). Timestamps and the
# words the rule actually depends on ("like", "feel") are unchanged.
from candidate import PAUSE_DISCOURSE_THRESHOLD_SECONDS, Word, detect_fillers_v2


def _flagged_texts(words: list[Word]) -> list[str]:
    return [occ.text for occ in detect_fillers_v2(words)]


# --- A. Test-D-style case: pause + segment boundary -> flagged -------------


def test_a_pause_and_segment_boundary_flags_like():
    words = [
        Word(text=" word", start_time=24.68, end_time=28.30, segment_start=False),
        Word(text=" like", start_time=33.68, end_time=35.08, segment_start=True),
        Word(text=" word", start_time=35.08, end_time=36.48, segment_start=False),
    ]
    assert "like" in _flagged_texts(words)


# --- B. gap < threshold + segment boundary -> not flagged by new signal ----


def test_b_short_gap_with_segment_boundary_does_not_flag_like():
    gap = PAUSE_DISCOURSE_THRESHOLD_SECONDS - 0.5
    words = [
        Word(text=" word", start_time=0.0, end_time=1.0, segment_start=False),
        Word(text=" like", start_time=1.0 + gap, end_time=1.0 + gap + 0.3, segment_start=True),
    ]
    assert "like" not in _flagged_texts(words)


# --- C. gap >= threshold but NOT a segment boundary -> not flagged ---------


def test_c_long_gap_without_segment_boundary_does_not_flag_like():
    words = [
        Word(text=" word", start_time=0.0, end_time=1.0, segment_start=False),
        Word(text=" like", start_time=1.0 + PAUSE_DISCOURSE_THRESHOLD_SECONDS, end_time=2.5, segment_start=False),
    ]
    assert "like" not in _flagged_texts(words)


# --- D. segment boundary but no previous word -> normal sentence-initial ---


def test_d_segment_boundary_with_no_previous_word_uses_sentence_initial_only():
    words = [
        Word(text=" like", start_time=0.0, end_time=1.0, segment_start=True),
        Word(text=" word", start_time=1.0, end_time=1.5, segment_start=False),
    ]
    # Flagged, but via the pre-existing sentence_initial(previous=None) path,
    # not via pause_boundary_signal (which requires a previous word to exist).
    assert "like" in _flagged_texts(words)


# --- E-H. semantic suppression must survive the new pause_boundary signal --


def test_e_feel_like_after_long_pause_remains_suppressed():
    words = [
        Word(text=" feel", start_time=0.0, end_time=1.0, segment_start=False),
        Word(text=" like", start_time=1.0 + PAUSE_DISCOURSE_THRESHOLD_SECONDS + 1.0, end_time=4.0, segment_start=True),
    ]
    assert "like" not in _flagged_texts(words)


def test_f_looks_like_after_long_pause_remains_suppressed():
    words = [
        Word(text=" looks", start_time=0.0, end_time=1.0, segment_start=False),
        Word(text=" like", start_time=1.0 + PAUSE_DISCOURSE_THRESHOLD_SECONDS + 1.0, end_time=4.0, segment_start=True),
    ]
    assert "like" not in _flagged_texts(words)


def test_g_sounds_like_after_long_pause_remains_suppressed():
    words = [
        Word(text=" sounds", start_time=0.0, end_time=1.0, segment_start=False),
        Word(text=" like", start_time=1.0 + PAUSE_DISCOURSE_THRESHOLD_SECONDS + 1.0, end_time=4.0, segment_start=True),
    ]
    assert "like" not in _flagged_texts(words)


def test_h_seems_like_after_long_pause_remains_suppressed():
    words = [
        Word(text=" seems", start_time=0.0, end_time=1.0, segment_start=False),
        Word(text=" like", start_time=1.0 + PAUSE_DISCOURSE_THRESHOLD_SECONDS + 1.0, end_time=4.0, segment_start=True),
    ]
    assert "like" not in _flagged_texts(words)


# --- I. pause-adjacent "actually" -> flagged via the new branch ------------


def test_i_pause_adjacent_actually_is_flagged():
    words = [
        Word(text=" important", start_time=0.0, end_time=1.0, segment_start=False),
        Word(
            text=" actually",
            start_time=1.0 + PAUSE_DISCOURSE_THRESHOLD_SECONDS + 0.4,
            end_time=3.0,
            segment_start=True,
        ),
        Word(text=" that", start_time=3.0, end_time=3.3, segment_start=False),
    ]
    # No preceding/following comma and not sentence-initial by punctuation -
    # this is flagged only because pause_boundary_signal is true.
    assert "actually" in _flagged_texts(words)


# --- J. punctuation-free, pause-free mid-clause "like" -> remains unflagged


def test_j_punctuation_free_pause_free_mid_clause_like_remains_unflagged():
    """Documented KNOWN UNRESOLVED CASE (design.md), not a test failure.

    This is Test D occurrence 1's actual failure pattern: no comma, not
    sentence-initial, no preceding pause, not a segment boundary. EXP-M6-006
    deliberately does not attempt to fix this - see design.md "Known unsolved
    cases" and the task instructions this experiment was scoped against.
    """
    words = [
        Word(text=" think", start_time=1.0, end_time=1.5, segment_start=False),
        Word(text=" like", start_time=1.5, end_time=1.8, segment_start=False),
        Word(text=" word", start_time=1.8, end_time=2.3, segment_start=False),
    ]
    assert "like" not in _flagged_texts(words)


# --- K. "you know" -> behavior identical to baseline (unconditional) -------


def test_k_you_know_matches_unconditionally_like_baseline():
    """Documented KNOWN, UNADDRESSED false-positive risk (design.md): a
    genuine question ("Do you know the time?") still matches, exactly as in
    production. EXP-M6-006 deliberately does not add a context check here.
    """
    words = [
        Word(text=" Do", start_time=0.0, end_time=0.3, segment_start=False),
        Word(text=" you", start_time=0.3, end_time=0.5, segment_start=False),
        Word(text=" know", start_time=0.5, end_time=0.8, segment_start=False),
        Word(text=" the", start_time=0.8, end_time=1.0, segment_start=False),
        Word(text=" time", start_time=1.0, end_time=1.3, segment_start=False),
    ]
    assert "you know" in _flagged_texts(words)


# --- L. preserved "um" -> unconditionally detected --------------------------


def test_l_preserved_um_is_unconditionally_detected():
    words = [
        Word(text=" I", start_time=0.0, end_time=0.3, segment_start=True),
        Word(text=" um", start_time=0.3, end_time=0.6, segment_start=False),
        Word(text=" think", start_time=0.6, end_time=1.0, segment_start=False),
    ]
    assert "um" in _flagged_texts(words)
