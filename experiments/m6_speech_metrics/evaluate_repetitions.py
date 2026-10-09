#!/usr/bin/env python3
"""EXP-M6-004: repetition / restart detection (experimental).

Hypothesis: simple n-gram-based heuristics (immediate repeated word/phrase, repeated
phrase-start) can catch some scripted repetitions, but Whisper's own decoder smoothing
(already observed at M5 - conclusions.md "Repetition smoothing") will erase some
repetitions before any transcript-based detector ever sees them, meaning a transcript-
based detector's silence is not proof the speaker did not repeat themselves.

Baselines:
- immediate_repeated_ngram: flags any immediately-adjacent repeated 1-3 word sequence
  (e.g. "I think, I think", "the the").
- repeated_phrase_start: flags two clauses/sentences (split on comma/period) that share
  the same first 2+ words (e.g. "The main reason... the reason is" - a *restart*, not
  an exact repeat, so the n-gram check above would miss it).

Ground truth: references/repetitions.json (expected_repetition, hand-labelled when the
samples were scripted).

Writes results/repetitions.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from faster_whisper import WhisperModel

HERE = Path(__file__).parent
SAMPLES_DIR = HERE / "samples"
RESULTS_DIR = HERE / "results"

MODEL_CONFIG = {"model_size": "base.en", "device": "cpu", "compute_type": "int8"}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def detect_immediate_repeated_ngram(words: list[str]) -> list[dict]:
    hits = []
    for n in (1, 2, 3):
        i = 0
        while i + 2 * n <= len(words):
            a = words[i : i + n]
            b = words[i + n : i + 2 * n]
            if a == b:
                hits.append({"ngram": " ".join(a), "n": n, "position": i})
                i += 2 * n
            else:
                i += 1
    return hits


def detect_repeated_phrase_start(text: str) -> list[dict]:
    clauses = [c.strip() for c in re.split(r"[.,]", text) if c.strip()]
    hits = []
    for i in range(len(clauses) - 1):
        words_a = tokenize(clauses[i])
        words_b = tokenize(clauses[i + 1])
        if len(words_a) >= 2 and len(words_b) >= 2 and words_a[:2] == words_b[:2]:
            hits.append({"clause_a": clauses[i], "clause_b": clauses[i + 1], "shared_start": " ".join(words_a[:2])})
    return hits


def transcribe(model: WhisperModel, path: Path) -> str:
    segments_iter, _info = model.transcribe(str(path), language="en")
    return " ".join(s.text.strip() for s in segments_iter if s.text.strip())


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    refs = json.loads((HERE / "references" / "repetitions.json").read_text())

    print(f"Loading model {MODEL_CONFIG}...", file=sys.stderr)
    model = WhisperModel(
        MODEL_CONFIG["model_size"], device=MODEL_CONFIG["device"], compute_type=MODEL_CONFIG["compute_type"]
    )

    results = []
    for ref in refs:
        name = ref["name"]
        path = SAMPLES_DIR / f"{name}.webm"
        print(f"Transcribing {name}...", file=sys.stderr)
        transcript = transcribe(model, path)
        reference_text = ref["text"]

        ngram_hits_transcript = detect_immediate_repeated_ngram(tokenize(transcript))
        phrase_hits_transcript = detect_repeated_phrase_start(transcript)
        ngram_hits_reference = detect_immediate_repeated_ngram(tokenize(reference_text))
        phrase_hits_reference = detect_repeated_phrase_start(reference_text)

        detected_on_transcript = bool(ngram_hits_transcript or phrase_hits_transcript)
        detected_on_reference_script = bool(ngram_hits_reference or phrase_hits_reference)

        results.append(
            {
                "sample": name,
                "pattern": ref["pattern"],
                "expected_repetition": ref["expected_repetition"],
                "reference_script": reference_text,
                "transcript_text": transcript,
                "transcript_matches_reference_script": transcript.strip().lower().rstrip(".") == reference_text.strip().lower().rstrip("."),
                "detected_on_reference_script": {
                    "ngram_hits": ngram_hits_reference,
                    "phrase_start_hits": phrase_hits_reference,
                    "any_detected": detected_on_reference_script,
                },
                "detected_on_transcript": {
                    "ngram_hits": ngram_hits_transcript,
                    "phrase_start_hits": phrase_hits_transcript,
                    "any_detected": detected_on_transcript,
                },
                "verdict": (
                    "correct"
                    if detected_on_transcript == ref["expected_repetition"]
                    else (
                        "erased_by_whisper_smoothing"
                        if ref["expected_repetition"] and detected_on_reference_script and not detected_on_transcript
                        else "missed_by_heuristic"
                        if ref["expected_repetition"]
                        else "false_positive"
                    )
                ),
            }
        )

    out_path = RESULTS_DIR / "repetitions.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out_path}", file=sys.stderr)

    print("\n=== Summary ===", file=sys.stderr)
    for r in results:
        print(
            f"{r['sample']:24s} expected={r['expected_repetition']!s:5s} "
            f"detected_on_transcript={r['detected_on_transcript']['any_detected']!s:5s} "
            f"verdict={r['verdict']}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
