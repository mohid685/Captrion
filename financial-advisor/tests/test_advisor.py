from unittest.mock import MagicMock, patch

from app.reasoning.advisor import build_user_prompt


SAMPLE_ML_SIGNALS = {
    "trend_prediction": "upward",
    "trend_confidence": 0.72,
    "risk_level": "moderate",
    "sharpe_ratio_estimate": 1.1,
    "volatility": "medium",
    "trend_reliability_tier": "very low — barely distinguishable from random guessing",
    "note": "MOCK DATA — test",
}

SAMPLE_SENTIMENT = {
    "overall_label": "positive",
    "overall_confidence": 0.85,
    "source": "FinBERT (real model — not mocked)",
    "per_chunk": [],
}


class TestBuildUserPrompt:
    def test_includes_rag_chunks_ml_signals_and_sentiment(self) -> None:
        rag_chunks = [
            {"source": "sec_filing", "doc_type": "10-Q", "date": "2026-07-31", "text": "Revenue grew 20%."}
        ]

        prompt = build_user_prompt(
            "How is revenue trending?", "AAPL", rag_chunks, SAMPLE_ML_SIGNALS, SAMPLE_SENTIMENT
        )

        assert "Revenue grew 20%." in prompt
        assert "upward" in prompt
        assert "positive" in prompt
        assert "AAPL" in prompt
        assert "How is revenue trending?" in prompt

    def test_handles_no_chunks(self) -> None:
        prompt = build_user_prompt("Any news?", "TSLA", [], SAMPLE_ML_SIGNALS, SAMPLE_SENTIMENT)
        assert "No relevant documents found." in prompt

    def test_includes_user_context_when_provided(self) -> None:
        rag_chunks = []
        user_context = {
            "risk_tolerance": "low",
            "investment_goals": "capital preservation",
            "holding": {"shares": 20, "cost_basis": 275.0},
        }
        prompt = build_user_prompt(
            "Should I sell?", "AAPL", rag_chunks, SAMPLE_ML_SIGNALS, SAMPLE_SENTIMENT, user_context
        )
        assert "low" in prompt
        assert "capital preservation" in prompt
        assert "20 shares" in prompt


class TestAskAdvisor:
    @patch("app.reasoning.advisor.get_ml_signals")
    @patch("app.reasoning.advisor.score_texts")
    @patch("app.reasoning.advisor.generate_response")
    @patch("app.reasoning.advisor.query_similar")
    @patch("app.reasoning.advisor.embed_query")
    def test_full_flow_returns_expected_structure(
        self,
        mock_embed: MagicMock,
        mock_query: MagicMock,
        mock_generate: MagicMock,
        mock_score: MagicMock,
        mock_ml_signals: MagicMock,
    ) -> None:
        from app.reasoning.advisor import ask_advisor

        mock_embed.return_value = [0.1, 0.2, 0.3]
        mock_query.return_value = [
            {"source": "news", "doc_type": "news_article", "date": "2026-08-01", "text": "Good news.", "score": 0.9}
        ]
        mock_score.return_value = [{"label": "positive", "confidence": 0.9}]
        mock_generate.return_value = "AAPL looks strong based on the evidence."
        mock_ml_signals.return_value = {
            "ticker": "AAPL",
            "trend_prediction": "upward",
            "trend_confidence": 0.72,
            "risk_level": "moderate",
            "sharpe_ratio_estimate": 1.1,
            "volatility": "medium",
            "trend_reliability_tier": "very low — barely distinguishable from random guessing",
            "note": "MOCK DATA — test",
        }

        result = ask_advisor("AAPL", "Is AAPL a good buy?")

        assert result["ticker"] == "AAPL"
        assert result["answer"] == "AAPL looks strong based on the evidence."
        assert len(result["sources_used"]) == 1
        assert result["ml_signals"]["trend_prediction"] == "upward"
        assert result["sentiment_analysis"]["overall_label"] == "positive"
        assert result["sentiment_analysis"]["source"] == "FinBERT (real model — not mocked)"