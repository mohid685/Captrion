from unittest.mock import patch

from app.voice.summarizer import MAX_VOICE_SUMMARY_CHARS, summarize_for_speech


class TestSummarizeForSpeech:
    @patch("app.voice.summarizer.generate_response")
    def test_returns_llm_summary_when_short_enough(self, mock_generate) -> None:
        mock_generate.return_value = "AAPL is trading around three hundred five dollars and looks moderately risky."
        result = summarize_for_speech("What's AAPL's price?", "Full detailed answer with tables...")
        assert result == mock_generate.return_value

    @patch("app.voice.summarizer.generate_response")
    def test_truncates_if_llm_exceeds_limit(self, mock_generate) -> None:
        mock_generate.return_value = "word " * 200  # way over 400 chars
        result = summarize_for_speech("question", "answer")
        assert len(result) <= MAX_VOICE_SUMMARY_CHARS

    @patch("app.voice.summarizer.generate_response")
    def test_strips_whitespace(self, mock_generate) -> None:
        mock_generate.return_value = "  A short summary.  "
        result = summarize_for_speech("q", "a")
        assert result == "A short summary."