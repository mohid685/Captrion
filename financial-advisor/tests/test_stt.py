from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.voice.stt import STTError, transcribe_audio


def _fake_wav_bytes(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    import io

    import soundfile as sf

    samples = np.random.uniform(-0.1, 0.1, int(duration_seconds * sample_rate)).astype(np.float32)
    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, format="WAV")
    return buffer.getvalue()


class TestTranscribeAudio:
    def test_raises_on_undecodable_audio(self) -> None:
        with pytest.raises(STTError):
            transcribe_audio(b"not real audio data")

    @patch("app.voice.stt._get_whisper_pipeline")
    def test_raises_on_too_long_audio(self, mock_pipeline: MagicMock) -> None:
        long_audio = _fake_wav_bytes(duration_seconds=150)
        with pytest.raises(STTError):
            transcribe_audio(long_audio)

    @patch("app.voice.stt._get_whisper_pipeline")
    def test_raises_on_too_short_audio(self, mock_pipeline: MagicMock) -> None:
        short_audio = _fake_wav_bytes(duration_seconds=0.1)
        with pytest.raises(STTError):
            transcribe_audio(short_audio)

    @patch("app.voice.stt._get_whisper_pipeline")
    def test_raises_on_empty_transcription(self, mock_pipeline: MagicMock) -> None:
        mock_pipeline.return_value.return_value = {"text": ""}
        audio = _fake_wav_bytes(duration_seconds=2)
        with pytest.raises(STTError):
            transcribe_audio(audio)

    @patch("app.voice.stt._get_whisper_pipeline")
    def test_returns_transcribed_text(self, mock_pipeline: MagicMock) -> None:
        mock_pipeline.return_value.return_value = {"text": "What is AAPL's current price?"}
        audio = _fake_wav_bytes(duration_seconds=2)
        result = transcribe_audio(audio)
        assert result == "What is AAPL's current price?"