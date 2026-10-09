"""Transcription service interface.

Kept separate from any concrete implementation (see faster_whisper_service.py) so the
API layer (app/api/attempts.py) never touches model-loading/inference code directly, and
so tests can substitute a fake implementation without loading a real model
(see docs/context.md "STT Layer").
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class TranscriptSegmentResult:
    start_time: float
    end_time: float
    text: str


@dataclass(frozen=True)
class TranscriptWordResult:
    """One word-level timestamp, per DEC-020 (accepted at M6A, enabled in production

    at M6B). Deliberately minimal - text/start/end only, not every faster-whisper
    `Word` field (e.g. `probability` is not exposed - see docs/context.md "STT
    Layer" for why only the minimum needed for downstream metrics is surfaced).
    """

    text: str
    start_time: float
    end_time: float


@dataclass(frozen=True)
class TranscriptionSuccess:
    text: str
    language: str | None
    segments: list[TranscriptSegmentResult] = field(default_factory=list)
    words: list[TranscriptWordResult] = field(default_factory=list)
    model: str = ""
    duration_seconds: float = 0.0
    transcription_seconds: float = 0.0


@dataclass(frozen=True)
class TranscriptionFailure:
    code: str
    message: str


TranscriptionOutcome = TranscriptionSuccess | TranscriptionFailure


class TranscriptionService(Protocol):
    def transcribe(self, audio_bytes: bytes) -> TranscriptionOutcome:
        """Transcribes raw audio bytes (any container faster-whisper/PyAV can decode).

        Never raises for expected failure modes (decode failure, empty audio, model
        unavailable) - those are represented as `TranscriptionFailure`. A genuinely
        unexpected exception is still possible and must be handled by the caller (see
        app/api/attempts.py), never surfaced to the client as raw exception text.
        """
        ...
