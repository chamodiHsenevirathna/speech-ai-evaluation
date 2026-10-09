#!/usr/bin/env python3
"""M5 model-selection benchmark.

Hypothesis: a small local faster-whisper model can provide sufficiently useful
transcription for ~60-second impromptu speaking samples while keeping latency
acceptable for an interactive practice workflow.

Runs each candidate model against every sample in samples/, records latency/RTF/output,
and computes Word Error Rate against references/ where a reference exists. Writes
results.json and results.csv. This is a small, provisional local benchmark - see
conclusions.md, not a rigorous model evaluation.

Usage (from experiments/m5_transcription/, with the backend venv active):
    python benchmark.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from faster_whisper import WhisperModel

SAMPLES_DIR = Path(__file__).parent / "samples"
REFERENCES_DIR = Path(__file__).parent / "references"
RESULTS_DIR = Path(__file__).parent / "results"

CANDIDATES = [
    {"model_size": "tiny.en", "device": "cpu", "compute_type": "int8"},
    {"model_size": "base.en", "device": "cpu", "compute_type": "int8"},
]

FILLER_WORDS = {"um", "uh", "erm"}


def normalize(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def word_error_rate(reference: str, hypothesis: str) -> float | None:
    ref_words = normalize(reference)
    hyp_words = normalize(hypothesis)
    if not ref_words:
        return None  # no reference text (e.g. near-silent sample) - WER undefined

    # Standard Levenshtein distance over words.
    n, m = len(ref_words), len(hyp_words)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[n][m] / len(ref_words)


def count_fillers(words: list[str]) -> int:
    return sum(1 for w in words if w in FILLER_WORDS)


@dataclass
class SampleResult:
    candidate: str
    sample: str
    model_size: str
    device: str
    compute_type: str
    audio_duration_seconds: float
    transcription_seconds: float
    real_time_factor: float
    transcript_text: str
    segment_count: int
    has_timestamps: bool
    word_error_rate: float | None
    reference_filler_count: int
    transcript_filler_count: int
    approx_model_footprint_mb: float | None


def get_model_footprint_mb(model: WhisperModel) -> float | None:
    """Best-effort: sum the size of files under the model's local snapshot directory."""
    try:
        model_dir = getattr(getattr(model, "model", None), "_model_dir", None)
        if not model_dir:
            return None
        total = sum(f.stat().st_size for f in Path(model_dir).rglob("*") if f.is_file())
        return round(total / (1024 * 1024), 1)
    except Exception:
        return None


def run_candidate(candidate: dict) -> list[SampleResult]:
    name = f"{candidate['model_size']}-{candidate['device']}-{candidate['compute_type']}"
    print(f"\n=== Loading candidate: {name} ===", file=sys.stderr)
    load_start = time.monotonic()
    model = WhisperModel(
        candidate["model_size"], device=candidate["device"], compute_type=candidate["compute_type"]
    )
    load_seconds = time.monotonic() - load_start
    print(f"Model loaded in {load_seconds:.1f}s", file=sys.stderr)
    footprint = get_model_footprint_mb(model)

    results: list[SampleResult] = []
    for sample_path in sorted(SAMPLES_DIR.glob("*.webm")):
        sample_name = sample_path.stem
        reference_path = REFERENCES_DIR / f"{sample_name}.txt"
        reference_text = reference_path.read_text() if reference_path.exists() else ""

        print(f"  Transcribing {sample_name}...", file=sys.stderr)
        start = time.monotonic()
        segments_iter, info = model.transcribe(str(sample_path), language="en")
        segments = list(segments_iter)
        transcription_seconds = time.monotonic() - start

        text = " ".join(s.text.strip() for s in segments if s.text.strip())
        rtf = transcription_seconds / info.duration if info.duration else float("nan")

        ref_words = normalize(reference_text)
        hyp_words = normalize(text)

        results.append(
            SampleResult(
                candidate=name,
                sample=sample_name,
                model_size=candidate["model_size"],
                device=candidate["device"],
                compute_type=candidate["compute_type"],
                audio_duration_seconds=round(info.duration, 2),
                transcription_seconds=round(transcription_seconds, 2),
                real_time_factor=round(rtf, 3),
                transcript_text=text,
                segment_count=len(segments),
                has_timestamps=len(segments) > 0 and hasattr(segments[0], "start"),
                word_error_rate=(
                    round(wer, 3) if (wer := word_error_rate(reference_text, text)) is not None else None
                ),
                reference_filler_count=count_fillers(ref_words),
                transcript_filler_count=count_fillers(hyp_words),
                approx_model_footprint_mb=footprint,
            )
        )

    return results


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    all_results: list[SampleResult] = []
    for candidate in CANDIDATES:
        all_results.extend(run_candidate(candidate))

    results_dicts = [asdict(r) for r in all_results]

    json_path = RESULTS_DIR / "results.json"
    json_path.write_text(json.dumps(results_dicts, indent=2))

    csv_path = RESULTS_DIR / "results.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results_dicts[0].keys()))
        writer.writeheader()
        writer.writerows(results_dicts)

    print(f"\nWrote {json_path} and {csv_path}", file=sys.stderr)
    print("\n=== Summary ===", file=sys.stderr)
    for r in all_results:
        print(
            f"{r.candidate:20s} {r.sample:20s} "
            f"dur={r.audio_duration_seconds:6.2f}s  "
            f"transcribe={r.transcription_seconds:6.2f}s  "
            f"RTF={r.real_time_factor:5.3f}  "
            f"WER={r.word_error_rate}  "
            f"fillers(ref/hyp)={r.reference_filler_count}/{r.transcript_filler_count}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
