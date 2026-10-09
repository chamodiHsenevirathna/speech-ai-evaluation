"""Deterministic word-count rule.

Rule established at M6A (experiments/m6_speech_metrics/conclusions.md Step 3): a word
token is a maximal run of letters/digits/apostrophes. This counts contractions
("don't") as one token, digit-rendered numbers ("23") as one token each, and simply
inherits whatever the transcript actually contains - no de-duplication, no spell
correction, no attempt to "fix" transcription errors at this layer (see that
document for why: word count is a count of *transcribed* words, and its accuracy is
bounded by transcription accuracy, which is exactly why this metric is classified
approximate, not exact).
"""

import re

_WORD_PATTERN = re.compile(r"[A-Za-z0-9']+")


def count_words(text: str) -> int:
    if not text:
        return 0
    return len(_WORD_PATTERN.findall(text))
