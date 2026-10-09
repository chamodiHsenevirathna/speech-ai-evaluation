"""
EXP-M6-006 - Timestamp-Aware Filler Heuristic (experimental candidate).

NOT PRODUCTION CODE. See README.md and design.md in this directory.

This module implements a CANDIDATE variant of
backend/app/services/metrics/fillers.py's detect_fillers() for offline
evaluation only, once EXP-M6-005's frozen baseline annotations exist. It does
not import, modify, or monkey-patch production code in any way - the values
below that originate from production code or production decisions (DEC-014's
pause threshold; fillers.py's vocabulary/suppression sets) are copied as
FROZEN local constants, not imported, so that:

  - this experiment's results stay reproducible even if production values
    change later (a later DEC-014 revision or fillers.py edit must not
    silently change EXP-M6-006's historical results), and
  - production fillers.py is never touched or coupled to by this module.

Threshold provenance (PAUSE_DISCOURSE_THRESHOLD_SECONDS):
  Inherited from DEC-014 / backend/app/services/metrics/pauses.py's
  LONG_PAUSE_THRESHOLD_SECONDS as it stood on 2026-08-24
  (docs/decision-log.md DEC-014, itself Status: Provisional). EXP-M6-006 does
  NOT independently validate 1.0s as an optimal threshold for filler
  discourse-position detection - it reuses an already-decided, already
  evidence-logged number instead of inventing a new one for this experiment.
  If DEC-014's value is ever revised, this constant is updated here
  deliberately, as a new, explicitly-noted experiment run - never silently.

Word/type provenance:
  `Word` and `FillerOccurrenceV2` are intentionally NOT imported from
  backend.app.services.transcription.base / backend.app.services.metrics.base
  - this experiment stays fully standalone (no dependency on the backend
    package or its import path). See design.md "Why types aren't imported
    from production."
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Frozen constants (see module docstring "provenance" for why these are
# copied, not imported).
# ---------------------------------------------------------------------------

# Inherited from DEC-014 (docs/decision-log.md) / pauses.py's
# LONG_PAUSE_THRESHOLD_SECONDS, as of 2026-08-24. Not re-validated here.
PAUSE_DISCOURSE_THRESHOLD_SECONDS = 1.0

# Frozen copies of backend/app/services/metrics/fillers.py's vocabulary and
# suppression sets, as they stood on 2026-08-24.
_ALWAYS_FILLER = {"um", "uh", "ah", "erm"}
_AMBIGUOUS_SINGLE = {"like", "actually", "basically"}
_COMPARISON_VERBS = {
    "look", "looks", "looked",
    "sound", "sounds",
    "feel", "feels", "felt",
    "seem", "seems", "seemed",
}


@dataclass(frozen=True)
class Word:
    """Minimal word representation this candidate needs: text, timing, and
    whether it is the first word of a transcript segment. The caller is
    responsible for computing `segment_start` (e.g. from the same
    `transcription.segments`/`transcription.words` data SpeakLab's API
    already returns) - this module has no opinion on how segmentation is
    produced, only on how it's used once known."""

    text: str
    start_time: float
    end_time: float
    segment_start: bool = False


@dataclass(frozen=True)
class FillerOccurrenceV2:
    """Candidate-detector output. Same shape as production's
    FillerOccurrence (text, category, start_time, end_time), defined
    separately here rather than imported - see module docstring."""

    text: str
    category: str
    start_time: float
    end_time: float


def _clean(word_text: str) -> str:
    return word_text.strip().strip(",.!?").lower()


def _ends_with_comma(word_text: str) -> bool:
    return word_text.strip().endswith(",")


def _is_sentence_initial(previous_word_text: str | None) -> bool:
    if previous_word_text is None:
        return True
    return previous_word_text.strip().endswith((".", "!", "?"))


def _pause_boundary_signal(word: Word, previous_word: "Word | None") -> bool:
    """EXP-M6-006's new candidate signal: treat a sufficiently strong pause
    immediately before a segment-starting word as discourse-position
    evidence, alongside (not instead of) punctuation. See design.md for
    rationale, known false-positive risks, and known unsolved cases."""
    if not word.segment_start:
        return False
    if previous_word is None:
        return False
    gap = word.start_time - previous_word.end_time
    return gap >= PAUSE_DISCOURSE_THRESHOLD_SECONDS


def detect_fillers_v2(words: list[Word]) -> list[FillerOccurrenceV2]:
    """Experimental candidate filler detector (EXP-M6-006). NOT production
    code - see README.md.

    Unchanged from backend/app/services/metrics/fillers.py's detect_fillers():
      - um / uh / ah / erm: unconditional given a preserved token.
      - "you know": unconditional adjacent-pair match, no context check.
      - "like" semantic suppression via _COMPARISON_VERBS.
      - "actually"/"basically"'s existing comma-based branches.

    Added:
      - `like`: an additional `pause_boundary_signal` OR-branch, still gated
        by the existing comparison-verb suppression.
      - `actually`/`basically`: an additional, independent
        `pause_boundary_signal` OR-branch alongside the existing two.
    """
    occurrences: list[FillerOccurrenceV2] = []

    for index, word in enumerate(words):
        clean = _clean(word.text)
        previous_word = words[index - 1] if index > 0 else None
        previous_text = previous_word.text if previous_word is not None else None

        if clean in _ALWAYS_FILLER:
            occurrences.append(
                FillerOccurrenceV2(text=clean, category=clean, start_time=word.start_time, end_time=word.end_time)
            )
            continue

        if clean == "like":
            preceded_by_comma = previous_text is not None and _ends_with_comma(previous_text)
            sentence_initial = _is_sentence_initial(previous_text)
            pause_boundary = _pause_boundary_signal(word, previous_word)
            discourse_position = preceded_by_comma or sentence_initial or pause_boundary
            comparison_verb_before = previous_text is not None and _clean(previous_text) in _COMPARISON_VERBS
            if discourse_position and not comparison_verb_before:
                occurrences.append(
                    FillerOccurrenceV2(text="like", category="like", start_time=word.start_time, end_time=word.end_time)
                )
            continue

        if clean in _AMBIGUOUS_SINGLE:  # "actually" / "basically"
            preceded_by_comma = previous_text is not None and _ends_with_comma(previous_text)
            sentence_initial = _is_sentence_initial(previous_text)
            followed_by_comma = _ends_with_comma(word.text)
            pause_boundary = _pause_boundary_signal(word, previous_word)
            if preceded_by_comma or (sentence_initial and followed_by_comma) or pause_boundary:
                occurrences.append(
                    FillerOccurrenceV2(text=clean, category=clean, start_time=word.start_time, end_time=word.end_time)
                )
            continue

    # "you know" - UNCHANGED from production: unconditional adjacent-pair
    # match, no context check. Deliberately not given one in EXP-M6-006 - see
    # design.md "Known unsolved cases."
    for index in range(len(words) - 1):
        first, second = _clean(words[index].text), _clean(words[index + 1].text)
        if first == "you" and second == "know":
            occurrences.append(
                FillerOccurrenceV2(
                    text="you know",
                    category="you know",
                    start_time=words[index].start_time,
                    end_time=words[index + 1].end_time,
                )
            )

    return occurrences
