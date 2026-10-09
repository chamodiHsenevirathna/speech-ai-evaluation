#!/usr/bin/env python3
"""Generates the M6A evaluation sample set.

IMPORTANT / LIMITATION: this sandboxed development environment has no microphone
access, so these are NOT real human recordings. They are synthesized locally via
macOS `say` (text-to-speech), with silence inserted at precisely-controlled durations
via `ffmpeg`, and converted to the same WebM/Opus container the browser produces (see
`docs/decision-log.md` DEC-016). This lets us exercise the real decode -> transcribe ->
metrics pipeline end-to-end with *known* ground truth (we wrote the script and control
the silence duration exactly), but these are not real disfluency acoustics or a real
accent. See `experiments/m5_transcription/README.md` for the same caveat applied there,
and `conclusions.md` for how this experiment additionally lacks any real-human
recording (unlike M5, which had one ad hoc real-human qualitative check that was never
saved to disk, per that experiment's "keep raw audio gitignored" rule) - so results.md
values here are entirely synthetic and are documented as such.

Produces:
- samples/pause_*.webm      - two phrases separated by an exact silence duration
- samples/filler_*.webm     - single utterances covering filler/ambiguous cases
- samples/repetition_*.webm - immediate-repeat and restart patterns
- references/*.json         - machine-readable ground truth per sample (text, known
  pause interval, filler positions, repetition spans) consumed by the evaluate_*.py
  scripts

Requires: macOS `say`, `ffmpeg`/`ffprobe` on PATH.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
SAMPLES_DIR = HERE / "samples"
REFERENCES_DIR = HERE / "references"

VOICE = "Samantha"
SAMPLE_RATE = 24000


def run(*args: str) -> None:
    subprocess.run(args, check=True, capture_output=True)


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def say_to_wav(text: str, out_wav: Path) -> None:
    aiff = out_wav.with_suffix(".aiff")
    run("say", "-v", VOICE, "-o", str(aiff), text)
    run("ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff),
        "-ar", str(SAMPLE_RATE), "-ac", "1", str(out_wav))
    aiff.unlink()


def silence_wav(duration_seconds: float, out_wav: Path) -> None:
    run("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
        "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
        "-t", str(duration_seconds), str(out_wav))


def concat_to_webm(wavs: list[Path], out_webm: Path) -> None:
    list_file = out_webm.with_suffix(".txt")
    list_file.write_text("".join(f"file '{w.resolve()}'\n" for w in wavs))
    run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c:a", "libopus", "-b:a", "32k", str(out_webm))
    list_file.unlink()


def single_utterance(name: str, text: str) -> None:
    """One TTS phrase, no injected silence - for filler/repetition samples."""
    print(f"Generating {name}...")
    wav = SAMPLES_DIR / f"{name}.wav"
    say_to_wav(text, wav)
    concat_to_webm([wav], SAMPLES_DIR / f"{name}.webm")
    wav.unlink()


def pause_pair(name: str, phrase1: str, phrase2: str, pause_seconds: float) -> dict:
    """Two TTS phrases separated by an exact silence duration.

    Returns the reference dict (including the *actual measured* pre-pause duration,
    not the requested one, since `say`'s speaking rate/timing is not fully
    deterministic word-for-word).
    """
    print(f"Generating {name} (pause={pause_seconds}s)...")
    wav1 = SAMPLES_DIR / f"{name}_p1.wav"
    wav2 = SAMPLES_DIR / f"{name}_p2.wav"
    sil = SAMPLES_DIR / f"{name}_sil.wav"
    say_to_wav(phrase1, wav1)
    say_to_wav(phrase2, wav2)
    silence_wav(pause_seconds, sil)

    dur1 = probe_duration(wav1)
    dur2 = probe_duration(wav2)

    concat_to_webm([wav1, sil, wav2], SAMPLES_DIR / f"{name}.webm")
    for f in (wav1, wav2, sil):
        f.unlink()

    return {
        "name": name,
        "phrase1": phrase1,
        "phrase2": phrase2,
        "requested_pause_seconds": pause_seconds,
        "measured_phrase1_duration": round(dur1, 3),
        "measured_phrase2_duration": round(dur2, 3),
        "known_pause_interval": [round(dur1, 3), round(dur1 + pause_seconds, 3)],
        "full_text": f"{phrase1} {phrase2}",
    }


def main() -> None:
    SAMPLES_DIR.mkdir(exist_ok=True)
    REFERENCES_DIR.mkdir(exist_ok=True)

    # --- Pause samples: same two phrases, four different injected silence lengths,
    # plus a no-injected-pause control (natural TTS gap only) to check false positives.
    p1 = "I think the first point is really important."
    p2 = "The second point builds on that idea."
    pause_refs = []
    for label, seconds in [("0_5s", 0.5), ("1_0s", 1.0), ("2_0s", 2.0), ("3_0s", 3.0)]:
        pause_refs.append(pause_pair(f"pause_{label}", p1, p2, seconds))
    # Control: concatenate directly with zero injected silence (natural word-boundary
    # gap only, expected well under any realistic threshold).
    pause_refs.append(pause_pair("pause_control_0s", p1, p2, 0.0))
    (REFERENCES_DIR / "pauses.json").write_text(json.dumps(pause_refs, indent=2))

    # --- Filler / ambiguous-word samples.
    filler_samples = {
        "filler_um_uh": {
            "text": "So, um, I think the the best way to explain this is, uh, well, it's kind of complicated but let me try.",
            "expected_fillers": ["um", "uh"],
            "notes": "Same script as M5 natural_fillers.webm - reused for consistency, not regenerated identically (new TTS render).",
        },
        "filler_like_discourse": {
            "text": "Like, I don't really know what to say about that, it's kind of hard to explain.",
            "expected_fillers": ["like"],
            "notes": "Sentence-initial 'Like,' functioning as a discourse-marker filler, not a comparison.",
        },
        "filler_like_semantic": {
            "text": "She looks like her sister in almost every way.",
            "expected_fillers": [],
            "notes": "'like' used as a genuine comparison/preposition - must NOT be counted as filler.",
        },
        "filler_actually_hedge": {
            "text": "So, actually, um, I forgot what I was going to say.",
            "expected_fillers": ["actually", "um"],
            "notes": "'actually' used as a hedge/filler alongside 'um', not asserting a fact.",
        },
        "filler_actually_semantic": {
            "text": "The report was actually completed a week ahead of schedule.",
            "expected_fillers": [],
            "notes": "'actually' used semantically (asserting a surprising fact) - must NOT be counted as filler.",
        },
        "filler_basically": {
            "text": "Basically, we just need to finish the last section before Friday.",
            "expected_fillers": ["basically"],
            "notes": "Sentence-initial discourse-marker use.",
        },
        "filler_you_know": {
            "text": "It was, you know, kind of a weird situation for all of us.",
            "expected_fillers": ["you know"],
            "notes": "Multi-word filler phrase.",
        },
        "filler_none_clean": {
            "text": "The weather today is sunny with a light breeze, and it is a perfect afternoon for a walk.",
            "expected_fillers": [],
            "notes": "Clean fluent control sentence - no fillers, checks for false positives.",
        },
    }
    for name, spec in filler_samples.items():
        single_utterance(name, spec["text"])
    (REFERENCES_DIR / "fillers.json").write_text(
        json.dumps(
            [{"name": name, **spec} for name, spec in filler_samples.items()], indent=2
        )
    )

    # --- Repetition / restart samples.
    repetition_samples = {
        "repetition_immediate": {
            "text": "I think, I think we should leave now before the traffic gets worse.",
            "expected_repetition": True,
            "pattern": "immediate_repeated_bigram",
            "notes": "'I think, I think' - immediate exact repeat of a short phrase.",
        },
        "repetition_restart": {
            "text": "The main reason, the reason is that we ran out of time to finish properly.",
            "expected_repetition": True,
            "pattern": "restart",
            "notes": "'The main reason... the reason is' - restart with partial phrase overlap, not an exact repeat.",
        },
        "repetition_none_clean": {
            "text": "We finished the project early and celebrated with the whole team that evening.",
            "expected_repetition": False,
            "pattern": None,
            "notes": "Clean control sentence - no repetition, checks for false positives.",
        },
        "repetition_word_stutter": {
            "text": "So, um, I think the the best way to explain this is, uh, well, it's kind of complicated but let me try.",
            "expected_repetition": True,
            "pattern": "immediate_repeated_unigram",
            "notes": "'the the' - single-word stutter. Same script as filler_um_uh; M5 already found Whisper sometimes smooths this away (conclusions.md 'Repetition smoothing').",
        },
    }
    for name, spec in repetition_samples.items():
        single_utterance(name, spec["text"])
    (REFERENCES_DIR / "repetitions.json").write_text(
        json.dumps(
            [{"name": name, **spec} for name, spec in repetition_samples.items()], indent=2
        )
    )

    print("\nDone. Samples in samples/, references in references/.")


if __name__ == "__main__":
    main()
