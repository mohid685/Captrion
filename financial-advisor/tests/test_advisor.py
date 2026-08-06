from unittest.mock import MagicMock, patch

from app.reasoning.advisor import build_user_prompt


class TestBuildUserPrompt:
    def test_includes_rag_chunks_and_ml_signals(self) -> None:
        rag_chunks = [
            {"source": "sec_filing", "doc_type": "10-Q", "date": "2026-07-31", "text": "Revenue grew 20%."}
        ]
        ml_signals = {
            "trend_prediction": "upward",
            "trend_confidence": 0.72,
            "risk_level": "moderate",
            "sharpe_ratio_estimate": 1.1,
            "volatility": "medium",
            "note": "MOCK DATA — test",
        }

        prompt = build_user_prompt("How is revenue trending?", "AAPL", rag_chunks, ml_signals)

        assert "Revenue grew 20%." in prompt
        assert "upward" in prompt
        assert "AAPL" in prompt
        assert "How is revenue trending?" in prompt

    def test_handles_no_chunks(self) -> None:
        ml_signals = {
            "trend_prediction": "upward",
            "trend_confidence": 0.72,
            "risk_level": "moderate",
            "sharpe_ratio_estimate": 1.1,
            "volatility": "medium",
            "note": "MOCK DATA — test",
        }
        prompt = build_user_prompt("Any news?", "TSLA", [], ml_signals)
        assert "No relevant documents found." in prompt


class TestAskAdvisor:
    @patch("app.reasoning.advisor.generate_response")
    @patch("app.reasoning.advisor.query_similar")
    @patch("app.reasoning.advisor.embed_query")
    def test_full_flow_returns_expected_structure(
        self,
        mock_embed: MagicMock,
        mock_query: MagicMock,
        mock_generate: MagicMock,
    ) -> None:
        from app.reasoning.advisor import ask_advisor

        mock_embed.return_value = [0.1, 0.2, 0.3]
        mock_query.return_value = [
            {"source": "news", "doc_type": "news_article", "date": "2026-08-01", "text": "Good news.", "score": 0.9}
        ]
        mock_generate.return_value = "AAPL looks strong based on the evidence."

        result = ask_advisor("AAPL", "Is AAPL a good buy?")

        assert result["ticker"] == "AAPL"
        assert result["answer"] == "AAPL looks strong based on the evidence."
        assert len(result["sources_used"]) == 1
        assert result["ml_signals"]["trend_prediction"] == "upward"