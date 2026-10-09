#!/usr/bin/env python3
"""EXP-M6-002: pause detection - word-timestamp gaps (A) vs VAD (B).

Hypothesis: gaps between faster-whisper word-level timestamps can reliably localize a
known injected silence of >=0.5s, without needing a separate VAD pass; VAD (Approach B)
would be a more direct measurement of true silence but is expected to be blocked on
this specific machine by the onnxruntime ABI issue already documented at M5
(experiments/m5_transcription/conclusions.md "VAD investigation").

Approach A: transcribe each pause_*.webm sample with word_timestamps=True, compute
every inter-word gap, and check which gaps exceed a range of candidate thresholds.
Compare against the *known* injected pause interval from generate_samples.py to see
which threshold correctly flags true pauses (0.5s/1.0s/2.0s/3.0s) while not flagging
the natural-gap control sample (pause_control_0s, no injected silence).

Approach B: attempt model.transcribe(..., vad_filter=True) on the same samples. If it
crashes with the known onnxruntime dlopen/ABI error, record that explicitly rather than
forcing a workaround - this environment finding was already established at M5 and is
not re-litigated here, just re-confirmed against the current environment.

Writes results/pauses.json.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

from faster_whisper import WhisperModel

HERE = Path(__file__).parent
SAMPLES_DIR = HERE / "samples"
RESULTS_DIR = HERE / "results"

MODEL_CONFIG = {"model_size": "base.en", "device": "cpu", "compute_type": "int8"}
CANDIDATE_THRESHOLDS = [0.3, 0.5, 0.75, 1.0, 1.5, 2.0]


def approach_a_word_gaps(model: WhisperModel, path: Path) -> dict:
    start = time.monotonic()
    segments_iter, info = model.transcribe(str(path), language="en", word_timestamps=True)
    segments = list(segments_iter)
    elapsed = time.monotonic() - start

    words = []
    for seg in segments:
        if getattr(seg, "words", None):
            for w in seg.words:
                words.append({"word": w.word, "start": float(w.start), "end": float(w.end)})

    gaps = []
    for a, b in zip(words, words[1:]):
        gap = b["start"] - a["end"]
        if gap > 0:
            gaps.append({"start": round(a["end"], 3), "end": round(b["start"], 3), "duration": round(gap, 3)})

    detected_by_threshold = {
        str(t): [g for g in gaps if g["duration"] >= t] for t in CANDIDATE_THRESHOLDS
    }

    return {
        "transcription_seconds": round(elapsed, 3),
        "all_gaps": sorted(gaps, key=lambda g: -g["duration"]),
        "detected_pauses_by_threshold": detected_by_threshold,
    }


def approach_b_vad(model: WhisperModel, path: Path) -> dict:
    try:
        start = time.monotonic()
        segments_iter, info = model.transcribe(str(path), language="en", vad_filter=True)
        segments = list(segments_iter)
        elapsed = time.monotonic() - start
        return {
            "status": "ok",
            "transcription_seconds": round(elapsed, 3),
            "segment_count": len(segments),
        }
    except Exception as exc:  # noqa: BLE001 - deliberately broad, this is a diagnostic probe
        return {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback_tail": traceback.format_exc().strip().splitlines()[-3:],
        }


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    pause_refs = json.loads((HERE / "references" / "pauses.json").read_text())

    print(f"Loading model {MODEL_CONFIG}...", file=sys.stderr)
    model = WhisperModel(
        MODEL_CONFIG["model_size"], device=MODEL_CONFIG["device"], compute_type=MODEL_CONFIG["compute_type"]
    )

    # Approach B is attempted once up front (not per-sample) since if it fails, it
    # fails identically every time - one representative probe is sufficient and avoids
    # repeating a known-broken call across every sample.
    print("Probing Approach B (VAD) on one sample...", file=sys.stderr)
    vad_probe = approach_b_vad(model, SAMPLES_DIR / "pause_2_0s.webm")
    print(f"  VAD probe result: {vad_probe['status']}", file=sys.stderr)

    results = []
    for ref in pause_refs:
        name = ref["name"]
        path = SAMPLES_DIR / f"{name}.webm"
        print(f"Approach A on {name}...", file=sys.stderr)
        a_result = approach_a_word_gaps(model, path)

        known_start, known_end = ref["known_pause_interval"]
        requested = ref["requested_pause_seconds"]

        # For each threshold: did Approach A find a gap overlapping the known interval,
        # and did it avoid flagging anything when there was no injected pause?
        threshold_verdicts = {}
        for t in CANDIDATE_THRESHOLDS:
            flagged = a_result["detected_pauses_by_threshold"][str(t)]
            overlaps_known = any(
                g["start"] < known_end and g["end"] > known_start for g in flagged
            )
            threshold_verdicts[str(t)] = {
                "flagged_count": len(flagged),
                "correctly_flags_known_pause": overlaps_known if requested > 0 else None,
                "false_positive_on_control": len(flagged) > 0 if requested == 0 else None,
            }

        results.append(
            {
                "sample": name,
                "requested_pause_seconds": requested,
                "known_pause_interval": ref["known_pause_interval"],
                "approach_a": a_result,
                "threshold_verdicts": threshold_verdicts,
            }
        )

    out = {
        "approach_b_vad_probe": vad_probe,
        "approach_a_results": results,
    }
    out_path = RESULTS_DIR / "pauses.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}", file=sys.stderr)

    print("\n=== Threshold verdict summary ===", file=sys.stderr)
    print(f"{'sample':22s} {'requested':>9s} " + " ".join(f"{t:>6}" for t in CANDIDATE_THRESHOLDS), file=sys.stderr)
    for r in results:
        row = []
        for t in CANDIDATE_THRESHOLDS:
            v = r["threshold_verdicts"][str(t)]
            if v["correctly_flags_known_pause"] is True:
                row.append("  OK  ")
            elif v["correctly_flags_known_pause"] is False:
                row.append(" MISS ")
            elif v["false_positive_on_control"] is True:
                row.append("  FP  ")
            elif v["false_positive_on_control"] is False:
                row.append("  ok  ")
            else:
                row.append("   -  ")
        print(f"{r['sample']:22s} {r['requested_pause_seconds']:>9} " + " ".join(row), file=sys.stderr)


if __name__ == "__main__":
    main()
