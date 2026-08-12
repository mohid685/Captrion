from unittest.mock import MagicMock, patch

import pytest

from app.voice.tts import TTSError, synthesize_speech


class TestSynthesizeSpeech:
    @patch("app.voice.tts.get_settings")
    def test_raises_without_api_key(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value.camb_api_key = None
        with pytest.raises(TTSError):
            synthesize_speech("Hello world")

    @patch("app.voice.tts.get_settings")
    @patch("app.voice.tts.requests.post")
    def test_returns_audio_bytes_on_success(self, mock_post: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.return_value.camb_api_key = "fake-key"
        mock_settings.return_value.camb_voice_id = 147320
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b"fake-audio-bytes"

        result = synthesize_speech("Hello world")

        assert result == b"fake-audio-bytes"

    @patch("app.voice.tts.get_settings")
    @patch("app.voice.tts.requests.post")
    def test_raises_on_non_200_status(self, mock_post: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.return_value.camb_api_key = "fake-key"
        mock_settings.return_value.camb_voice_id = 147320
        mock_post.return_value.status_code = 429
        mock_post.return_value.text = "Rate limited"

        with pytest.raises(TTSError):
            synthesize_speech("Hello world")

    @patch("app.voice.tts.get_settings")
    @patch("app.voice.tts.requests.post")
    def test_raises_on_empty_audio_content(self, mock_post: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.return_value.camb_api_key = "fake-key"
        mock_settings.return_value.camb_voice_id = 147320
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b""

        with pytest.raises(TTSError):
            synthesize_speech("Hello world")