"""Filler detection - context-sensitive matching (DEC-015), EXPERIMENTAL.

Vocabulary and policy are exactly what DEC-015 established at M6A - not expanded here.
Vocabulary: um, uh, ah (Whisper normalizes scripted "uh" to "ah" - see
experiments/m5_transcription/conclusions.md and DEC-015), erm, like, you know,
actually, basically.

Policy: unconditional matching over-counts semantic/comparative uses of "like",
"actually", and "basically" (experiments/m6_speech_metrics/experiment_plan.md
EXP-M6-003). Context-sensitive matching only counts these in discourse-marker
position. DEC-015's decision-log entry additionally specifies the REFINED rule (fixing
the one gap EXP-M6-003 found in the original M6A evaluation script): a discourse
marker is filler-position if it is comma-preceded OR sentence-initial-and-comma-
followed - not only sentence-initial, which missed a real mid-sentence hedge use
("So, actually, um, I forgot...").

Operates on word-level tokens (not raw joined text) because faster-whisper's
word-level output keeps punctuation attached to the token it follows (confirmed via a
live check during M6B implementation, e.g. `" um,"`, `" is,"`) - this makes
comma-adjacency directly readable from the token text, and gives each filler
occurrence a real timestamp for evidence display, which M6A's text-regex approach
could not do.

Classified EXPERIMENTAL - see docs/decision-log.md DEC-015 and
experiments/m6_speech_metrics/conclusions.md (8-example evaluation, not general
real-world accuracy evidence). This module implements the *provisional* policy as-is;
it does not itself upgrade DEC-015's status.
"""

from app.services.metrics.base import FillerOccurrence
from app.services.transcription.base import TranscriptWordResult

_ALWAYS_FILLER = {"um", "uh", "ah", "erm"}
_AMBIGUOUS_SINGLE = {"like", "actually", "basically"}
_COMPARISON_VERBS = {"look", "looks", "looked", "sound", "sounds", "feel", "feels", "felt", "seem", "seems", "seemed"}


def _clean(word_text: str) -> str:
    return word_text.strip().strip(",.!?").lower()


def _ends_with_comma(word_text: str) -> bool:
    return word_text.strip().endswith(",")


def _is_sentence_initial(previous_word_text: str | None) -> bool:
    if previous_word_text is None:
        return True
    return previous_word_text.strip().endswith((".", "!", "?"))


def detect_fillers(words: list[TranscriptWordResult]) -> list[FillerOccurrence]:
    occurrences: list[FillerOccurrence] = []

    for index, word in enumerate(words):
        clean = _clean(word.text)
        previous_text = words[index - 1].text if index > 0 else None

        if clean in _ALWAYS_FILLER:
            occurrences.append(
                FillerOccurrence(text=clean, category=clean, start_time=word.start_time, end_time=word.end_time)
            )
            continue

        if clean == "like":
            preceded_by_comma = previous_text is not None and _ends_with_comma(previous_text)
            sentence_initial = _is_sentence_initial(previous_text)
            discourse_position = preceded_by_comma or sentence_initial
            comparison_verb_before = previous_text is not None and _clean(previous_text) in _COMPARISON_VERBS
            if discourse_position and not comparison_verb_before:
                occurrences.append(
                    FillerOccurrence(text="like", category="like", start_time=word.start_time, end_time=word.end_time)
                )
            continue

        if clean in _AMBIGUOUS_SINGLE:  # "actually" / "basically"
            preceded_by_comma = previous_text is not None and _ends_with_comma(previous_text)
            sentence_initial = _is_sentence_initial(previous_text)
            followed_by_comma = _ends_with_comma(word.text)
            if preceded_by_comma or (sentence_initial and followed_by_comma):
                occurrences.append(
                    FillerOccurrence(text=clean, category=clean, start_time=word.start_time, end_time=word.end_time)
                )
            continue

    # "you know" - a two-word phrase, checked as an adjacent pair over the same list
    # rather than folded into the loop above (different match shape: two tokens, one
    # occurrence).
    for index in range(len(words) - 1):
        first, second = _clean(words[index].text), _clean(words[index + 1].text)
        if first == "you" and second == "know":
            occurrences.append(
                FillerOccurrence(
                    text="you know",
                    category="you know",
                    start_time=words[index].start_time,
                    end_time=words[index + 1].end_time,
                )
            )

    return occurrences
