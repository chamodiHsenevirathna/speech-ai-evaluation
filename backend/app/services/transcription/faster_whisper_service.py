"""Local faster-whisper transcription implementation.

The model is loaded lazily (on first real use, not at import/module load time) and
reused across requests via a module-level singleton - see _get_model(). This keeps
FastAPI startup fast and understandable (no model load on `uvicorn app.main:app`
startup) while avoiding reloading the model for every request.

Audio is decoded directly from in-memory bytes via faster-whisper's own PyAV-based
decoder (no ffmpeg subprocess, no temp files) - see docs/decision-log.md for the M5
audio-decoding investigation.
"""

import io
import logging
import time

from app.config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_MODEL_SIZE
from app.services.transcription.base import (
    TranscriptionFailure,
    TranscriptionOutcome,
    TranscriptionSuccess,
    TranscriptSegmentResult,
    TranscriptWordResult,
)

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        # Imported lazily too - importing faster_whisper (and transitively
        # ctranslate2/onnxruntime) has non-trivial cost and isn't needed until a
        # transcription is actually requested.
        from faster_whisper import WhisperModel

        logger.info(
            "Loading faster-whisper model=%s device=%s compute_type=%s",
            WHISPER_MODEL_SIZE,
            WHISPER_DEVICE,
            WHISPER_COMPUTE_TYPE,
        )
        _model = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)
    return _model


class FasterWhisperTranscriptionService:
    def transcribe(self, audio_bytes: bytes) -> TranscriptionOutcome:
        if not audio_bytes:
            return TranscriptionFailure("AUDIO_EMPTY", "No audio to transcribe.")

        try:
            model = _get_model()
        except Exception:
            logger.exception("Failed to load faster-whisper model")
            return TranscriptionFailure(
                "MODEL_UNAVAILABLE", "The transcription model could not be loaded."
            )

        try:
            start = time.monotonic()
            # word_timestamps=True per DEC-020 (accepted at M6A, enabled here at M6B) -
            # pause detection (app/services/metrics/) needs word-level gaps, not just
            # segment-level timestamps. Measured overhead (~7.5% average across the
            # M6A sample set) is documented in experiments/m6_speech_metrics/
            # conclusions.md; re-measured on a real local request in the M6B report.
            segments_iter, info = model.transcribe(
                io.BytesIO(audio_bytes), language="en", word_timestamps=True
            )
            segments = []
            words: list[TranscriptWordResult] = []
            for segment in segments_iter:
                segments.append(
                    TranscriptSegmentResult(
                        start_time=segment.start,
                        end_time=segment.end,
                        text=segment.text.strip(),
                    )
                )
                for word in segment.words or []:
                    words.append(
                        TranscriptWordResult(
                            text=word.word,
                            start_time=word.start,
                            end_time=word.end,
                        )
                    )
            transcription_seconds = time.monotonic() - start
        except Exception:
            # Covers PyAV decode failures (invalid/corrupt audio) and any other
            # unexpected model/runtime error - never exposed to the client as raw
            # exception text (see docs/context.md "API Contract").
            logger.exception("Transcription failed")
            return TranscriptionFailure(
                "TRANSCRIPTION_FAILED", "Transcription failed for this recording."
            )

        text = " ".join(segment.text for segment in segments if segment.text).strip()

        return TranscriptionSuccess(
            text=text,
            language=info.language,
            segments=segments,
            words=words,
            model=WHISPER_MODEL_SIZE,
            duration_seconds=info.duration,
            transcription_seconds=transcription_seconds,
        )
