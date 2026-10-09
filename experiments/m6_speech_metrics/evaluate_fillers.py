#!/usr/bin/env python3
"""EXP-M6-003: filler detection - unconditional matching (A) vs context-sensitive (B).

Hypothesis: simple unconditional token/phrase matching over-counts ambiguous words
("like", "actually", "basically") that have legitimate non-filler uses, and a small set
of context rules can distinguish the two cases well enough on this evaluation set to be
worth the extra complexity - but only a labelled evaluation, not intuition, can show
whether that's actually true, and account for known Whisper normalization
("uh" -> "ah", see experiments/m5_transcription/conclusions.md).

Baseline A: candidate vocabulary word/phrase appears anywhere in the transcript ->
counted as a filler occurrence, unconditionally.

Baseline B: same vocabulary, but "like", "actually", and "basically" are only counted
when a simple positional/punctuation heuristic suggests discourse-marker use (see
rule comments below) rather than their literal/semantic use.

Ground truth: references/fillers.json (expected_fillers per sample, hand-labelled when
the samples were scripted in generate_samples.py).

Evaluates at the level of (sample, vocabulary_item) pairs where the vocabulary item's
text actually appears somewhere in the *transcribed* output (an item that never appears
in the transcript at all can't be flagged as a false positive by either baseline, and
its absence is a transcription-completeness question, not a filler-detector question -
kept separate rather than conflated).

Writes results/fillers.json.
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

# Candidate vocabulary. "uh" intentionally still probed even though M5 found Whisper
# often renders it as "ah" - this experiment re-confirms that on these specific samples
# rather than assuming it.
SINGLE_WORD_VOCAB = ["um", "uh", "ah", "erm", "like", "actually", "basically"]
PHRASE_VOCAB = ["you know"]


def baseline_a_unconditional(text: str) -> dict[str, int]:
    """Every vocabulary occurrence counts as a filler, no context considered."""
    lower = text.lower()
    counts = {}
    for word in SINGLE_WORD_VOCAB:
        counts[word] = len(re.findall(rf"\b{re.escape(word)}\b", lower))
    for phrase in PHRASE_VOCAB:
        counts[phrase] = len(re.findall(re.escape(phrase), lower))
    return counts


def baseline_b_context_sensitive(text: str) -> dict[str, int]:
    """Context rules for the three ambiguous words; everything else same as baseline A."""
    lower = text.lower()
    counts = {}
    for word in ["um", "uh", "ah", "erm"]:
        counts[word] = len(re.findall(rf"\b{re.escape(word)}\b", lower))
    for phrase in PHRASE_VOCAB:
        counts[phrase] = len(re.findall(re.escape(phrase), lower))

    # "like": filler when sentence-initial ("Like,") or preceded by a comma (discourse
    # marker use). NOT filler when immediately preceded by a comparison verb
    # (looks/looked/sounds/sound/feels/felt/seems/seemed) - the simile/comparison case.
    like_filler = 0
    for m in re.finditer(r"\blike\b", lower):
        start = m.start()
        before = lower[:start]
        comparison_verb_before = re.search(
            r"\b(looks?|looked|sounds?|feels?|felt|seems?|seemed)\s*$", before.rstrip()
        )
        discourse_position = bool(re.search(r"(^|[,.]\s*)$", before)) or start == 0
        if discourse_position and not comparison_verb_before:
            like_filler += 1
    counts["like"] = like_filler

    # "actually"/"basically": filler when sentence-initial followed by a comma
    # ("Actually,"/"Basically,") - the hedge/discourse-marker position. NOT filler when
    # embedded mid-clause with no surrounding comma (semantic "in fact"/"in essence" use).
    for word in ["actually", "basically"]:
        count = 0
        for m in re.finditer(rf"\b{word}\b", lower):
            start, end = m.start(), m.end()
            before = lower[:start].rstrip()
            after = lower[end:].lstrip()
            sentence_initial = before == "" or re.search(r"[.!?]\s*$", before)
            followed_by_comma = after.startswith(",")
            if sentence_initial and followed_by_comma:
                count += 1
        counts[word] = count

    return counts


def transcribe(model: WhisperModel, path: Path) -> str:
    segments_iter, _info = model.transcribe(str(path), language="en")
    return " ".join(s.text.strip() for s in segments_iter if s.text.strip())


def score(predicted_words_present: set[str], expected_words: set[str], transcript_vocab_present: set[str]) -> dict:
    """Confusion matrix restricted to vocabulary items that actually appear in the transcript."""
    tp = fp = fn = 0
    for word in transcript_vocab_present:
        predicted = word in predicted_words_present
        actual = word in expected_words
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    fillers_refs = json.loads((HERE / "references" / "fillers.json").read_text())

    print(f"Loading model {MODEL_CONFIG}...", file=sys.stderr)
    model = WhisperModel(
        MODEL_CONFIG["model_size"], device=MODEL_CONFIG["device"], compute_type=MODEL_CONFIG["compute_type"]
    )

    all_vocab = SINGLE_WORD_VOCAB + PHRASE_VOCAB
    per_sample = []
    agg_a = {"tp": 0, "fp": 0, "fn": 0}
    agg_b = {"tp": 0, "fp": 0, "fn": 0}

    for ref in fillers_refs:
        name = ref["name"]
        path = SAMPLES_DIR / f"{name}.webm"
        print(f"Transcribing {name}...", file=sys.stderr)
        text = transcribe(model, path)

        counts_a = baseline_a_unconditional(text)
        counts_b = baseline_b_context_sensitive(text)
        predicted_a = {w for w, c in counts_a.items() if c > 0}
        predicted_b = {w for w, c in counts_b.items() if c > 0}
        expected = set(ref["expected_fillers"])
        vocab_present = {w for w in all_vocab if counts_a.get(w, 0) > 0}

        result_a = score(predicted_a, expected, vocab_present)
        result_b = score(predicted_b, expected, vocab_present)
        for k in ("tp", "fp", "fn"):
            agg_a[k] += result_a[k]
            agg_b[k] += result_b[k]

        per_sample.append(
            {
                "sample": name,
                "reference_text": ref["text"],
                "transcript_text": text,
                "expected_fillers": ref["expected_fillers"],
                "vocab_items_present_in_transcript": sorted(vocab_present),
                "baseline_a_counts": counts_a,
                "baseline_b_counts": counts_b,
                "baseline_a_scoring": result_a,
                "baseline_b_scoring": result_b,
            }
        )

    def summarize(agg: dict) -> dict:
        p = agg["tp"] / (agg["tp"] + agg["fp"]) if (agg["tp"] + agg["fp"]) else None
        r = agg["tp"] / (agg["tp"] + agg["fn"]) if (agg["tp"] + agg["fn"]) else None
        f1 = 2 * p * r / (p + r) if p is not None and r is not None and (p + r) > 0 else None
        return {**agg, "precision": p, "recall": r, "f1": f1}

    out = {
        "per_sample": per_sample,
        "aggregate_baseline_a": summarize(agg_a),
        "aggregate_baseline_b": summarize(agg_b),
    }
    out_path = RESULTS_DIR / "fillers.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}", file=sys.stderr)

    print("\n=== Per-sample ===", file=sys.stderr)
    for r in per_sample:
        print(
            f"{r['sample']:24s} expected={r['expected_fillers']} "
            f"A={r['baseline_a_scoring']} B={r['baseline_b_scoring']}",
            file=sys.stderr,
        )
    print(f"\nAggregate A: {out['aggregate_baseline_a']}", file=sys.stderr)
    print(f"Aggregate B: {out['aggregate_baseline_b']}", file=sys.stderr)


if __name__ == "__main__":
    main()
