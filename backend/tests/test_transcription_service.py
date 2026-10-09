"""Unit tests for FasterWhisperTranscriptionService itself.

These mock faster_whisper.WhisperModel so no real model is ever downloaded or loaded -
only the service's own logic (error mapping, segment conversion, singleton reuse) is
under test. Real-model behaviour is exercised separately by
experiments/m5_transcription/ (see M5 requirement 13).
"""

from types import SimpleNamespace
from unittest.mock import patch

import app.services.transcription.faster_whisper_service as service_module
from app.services.transcription.base import TranscriptionFailure, TranscriptionSuccess
from app.services.transcription.faster_whisper_service import FasterWhisperTranscriptionService


def _fake_word(word, start, end):
    return SimpleNamespace(word=word, start=start, end=end)


def _fake_segment(start, end, text, words=None):
    return SimpleNamespace(start=start, end=end, text=text, words=words or [])


def setup_function():
    # _get_model() memoizes into this module-level global - reset between tests so
    # each test's mock is the one actually used.
    service_module._model = None


def test_empty_audio_is_a_failure_without_touching_the_model():
    service = FasterWhisperTranscriptionService()

    with patch("faster_whisper.WhisperModel") as mock_model_cls:
        outcome = service.transcribe(b"")

    assert isinstance(outcome, TranscriptionFailure)
    assert outcome.code == "AUDIO_EMPTY"
    mock_model_cls.assert_not_called()


def test_model_load_failure_is_reported_as_model_unavailable():
    service = FasterWhisperTranscriptionService()

    with patch("faster_whisper.WhisperModel", side_effect=RuntimeError("boom")):
        outcome = service.transcribe(b"some-audio-bytes")

    assert isinstance(outcome, TranscriptionFailure)
    assert outcome.code == "MODEL_UNAVAILABLE"


def test_successful_transcription_maps_segments_and_metadata():
    mock_model = SimpleNamespace(
        transcribe=lambda audio, language, word_timestamps: (
            [
                _fake_segment(0.0, 1.2, " hello ", words=[_fake_word(" hello", 0.0, 1.2)]),
                _fake_segment(1.2, 2.5, " world ", words=[_fake_word(" world", 1.2, 2.5)]),
            ],
            SimpleNamespace(language="en", duration=2.5),
        )
    )

    service = FasterWhisperTranscriptionService()
    with patch("faster_whisper.WhisperModel", return_value=mock_model):
        outcome = service.transcribe(b"some-audio-bytes")

    assert isinstance(outcome, TranscriptionSuccess)
    assert outcome.text == "hello world"
    assert outcome.language == "en"
    assert outcome.duration_seconds == 2.5
    assert len(outcome.segments) == 2
    assert outcome.segments[0].start_time == 0.0
    assert outcome.segments[0].end_time == 1.2
    assert outcome.segments[0].text == "hello"
    assert outcome.transcription_seconds >= 0


def test_word_timestamps_are_requested_and_mapped():
    mock_model = SimpleNamespace(
        transcribe=lambda audio, language, word_timestamps: (
            [_fake_segment(0.0, 1.2, " hello world ", words=[_fake_word(" hello", 0.0, 0.5), _fake_word(" world", 0.5, 1.2)])],
            SimpleNamespace(language="en", duration=1.2),
        )
    )

    service = FasterWhisperTranscriptionService()
    with patch("faster_whisper.WhisperModel", return_value=mock_model):
        outcome = service.transcribe(b"some-audio-bytes")

    assert isinstance(outcome, TranscriptionSuccess)
    assert len(outcome.words) == 2
    assert outcome.words[0].text == " hello"
    assert outcome.words[0].start_time == 0.0
    assert outcome.words[0].end_time == 0.5
    assert outcome.words[1].text == " world"


def test_decode_or_inference_failure_is_reported_as_transcription_failed():
    mock_model = SimpleNamespace(
        transcribe=lambda audio, language, word_timestamps: (_ for _ in ()).throw(RuntimeError("bad audio"))
    )

    service = FasterWhisperTranscriptionService()
    with patch("faster_whisper.WhisperModel", return_value=mock_model):
        outcome = service.transcribe(b"corrupt-bytes")

    assert isinstance(outcome, TranscriptionFailure)
    assert outcome.code == "TRANSCRIPTION_FAILED"


def test_model_is_constructed_once_and_reused_across_transcribe_calls():
    mock_model = SimpleNamespace(
        transcribe=lambda audio, language, word_timestamps: ([], SimpleNamespace(language="en", duration=0.0))
    )

    service = FasterWhisperTranscriptionService()
    with patch("faster_whisper.WhisperModel", return_value=mock_model) as mock_model_cls:
        service.transcribe(b"clip-one")
        service.transcribe(b"clip-two")

    mock_model_cls.assert_called_once()


def test_no_speech_produces_a_success_with_empty_segments_and_text():
    mock_model = SimpleNamespace(
        transcribe=lambda audio, language, word_timestamps: ([], SimpleNamespace(language="en", duration=3.0))
    )

    service = FasterWhisperTranscriptionService()
    with patch("faster_whisper.WhisperModel", return_value=mock_model):
        outcome = service.transcribe(b"silence-bytes")

    assert isinstance(outcome, TranscriptionSuccess)
    assert outcome.text == ""
    assert outcome.segments == []
