#!/usr/bin/env python3
"""EXP-M6-001: revisit DEC-020 (word-level vs segment-level timestamps).

Hypothesis: word-level timestamps (`word_timestamps=True`) cost a measurable but
acceptable amount of extra latency, and their timing is plausible enough to be useful
for M6 pause detection and future filler localization / transcript click-to-audio -
enough to justify enabling them, now that M6 actually has a consumer for them (unlike
M5, which deferred this exact question with no consumer yet - see decision-log.md
DEC-020).

Experiment: run the same base.en/cpu/int8 model against the same sample set twice -
once with word_timestamps=False (M5's current default) and once True. Compare latency,
RTF, transcript text (should be identical - the flag only affects what's returned
alongside the text, not decoding), and, for the pause_*.webm samples (which have a
*known* injected silence interval from generate_samples.py), whether the word-level
gap that should span the pause lands inside the known interval.

Uses the M5 samples (experiments/m5_transcription/samples/) plus this experiment's own
pause_*.webm samples. Writes results/word_timestamps.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel

HERE = Path(__file__).parent
M5_SAMPLES = HERE.parent / "m5_transcription" / "samples"
OWN_SAMPLES = HERE / "samples"
RESULTS_DIR = HERE / "results"

MODEL_CONFIG = {"model_size": "base.en", "device": "cpu", "compute_type": "int8"}


def sample_paths() -> list[Path]:
    paths = sorted(M5_SAMPLES.glob("*.webm")) + sorted(OWN_SAMPLES.glob("pause_*.webm"))
    return paths


def transcribe(model: WhisperModel, path: Path, word_timestamps: bool) -> dict:
    start = time.monotonic()
    segments_iter, info = model.transcribe(
        str(path), language="en", word_timestamps=word_timestamps
    )
    segments = list(segments_iter)
    elapsed = time.monotonic() - start

    text = " ".join(s.text.strip() for s in segments if s.text.strip())
    words = []
    if word_timestamps:
        for seg in segments:
            if getattr(seg, "words", None):
                for w in seg.words:
                    words.append({"word": w.word, "start": round(float(w.start), 3), "end": round(float(w.end), 3)})

    return {
        "audio_duration_seconds": round(info.duration, 3) if info.duration else None,
        "transcription_seconds": round(elapsed, 3),
        "real_time_factor": round(elapsed / info.duration, 4) if info.duration else None,
        "transcript_text": text,
        "segment_count": len(segments),
        "word_count": len(words),
        "words": words,
    }


def find_word_gap_covering(words: list[dict], point_hint: float) -> dict | None:
    """Find the largest inter-word gap near point_hint (used to locate our injected pause)."""
    if len(words) < 2:
        return None
    best = None
    for a, b in zip(words, words[1:]):
        gap = b["start"] - a["end"]
        if gap <= 0:
            continue
        if best is None or gap > best["gap"]:
            best = {"gap": round(gap, 3), "start": a["end"], "end": b["start"]}
    return best


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    print(f"Loading model {MODEL_CONFIG}...", file=sys.stderr)
    model = WhisperModel(
        MODEL_CONFIG["model_size"], device=MODEL_CONFIG["device"], compute_type=MODEL_CONFIG["compute_type"]
    )

    pause_refs = json.loads((HERE / "references" / "pauses.json").read_text())
    pause_ref_by_name = {r["name"]: r for r in pause_refs}

    results = []
    for path in sample_paths():
        name = path.stem
        print(f"Transcribing {name} (segment-level)...", file=sys.stderr)
        seg_result = transcribe(model, path, word_timestamps=False)
        print(f"Transcribing {name} (word-level)...", file=sys.stderr)
        word_result = transcribe(model, path, word_timestamps=True)

        text_identical = seg_result["transcript_text"] == word_result["transcript_text"]
        overhead_pct = (
            round(
                100
                * (word_result["transcription_seconds"] - seg_result["transcription_seconds"])
                / seg_result["transcription_seconds"],
                1,
            )
            if seg_result["transcription_seconds"]
            else None
        )

        entry = {
            "sample": name,
            "segment_level": {
                "transcription_seconds": seg_result["transcription_seconds"],
                "real_time_factor": seg_result["real_time_factor"],
                "segment_count": seg_result["segment_count"],
            },
            "word_level": {
                "transcription_seconds": word_result["transcription_seconds"],
                "real_time_factor": word_result["real_time_factor"],
                "word_count": word_result["word_count"],
            },
            "latency_overhead_percent": overhead_pct,
            "transcript_text_identical": text_identical,
            "transcript_text": seg_result["transcript_text"],
        }

        if name in pause_ref_by_name:
            ref = pause_ref_by_name[name]
            known_start, known_end = ref["known_pause_interval"]
            detected_gap = find_word_gap_covering(word_result["words"], known_start)
            entry["pause_localization"] = {
                "known_pause_interval": ref["known_pause_interval"],
                "requested_pause_seconds": ref["requested_pause_seconds"],
                "largest_detected_word_gap": detected_gap,
                "gap_overlaps_known_interval": bool(
                    detected_gap is not None
                    and detected_gap["start"] < known_end
                    and detected_gap["end"] > known_start
                ),
            }

        results.append(entry)

    out_path = RESULTS_DIR / "word_timestamps.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out_path}", file=sys.stderr)

    print("\n=== Summary ===", file=sys.stderr)
    for r in results:
        loc = r.get("pause_localization")
        loc_str = ""
        if loc:
            loc_str = (
                f"  known=[{loc['known_pause_interval'][0]:.2f},{loc['known_pause_interval'][1]:.2f}]"
                f" detected_gap={loc['largest_detected_word_gap']}"
                f" overlap={loc['gap_overlaps_known_interval']}"
            )
        print(
            f"{r['sample']:25s} seg_rtf={r['segment_level']['real_time_factor']:.3f} "
            f"word_rtf={r['word_level']['real_time_factor']:.3f} "
            f"overhead={r['latency_overhead_percent']:>6}% "
            f"text_identical={r['transcript_text_identical']}{loc_str}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
