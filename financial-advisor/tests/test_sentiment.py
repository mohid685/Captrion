from app.ml.sentiment import aggregate_sentiment, score_texts


class TestScoreTexts:
    """
    Loads the real FinBERT model, so first run downloads it and may be
    slow. Subsequent runs use the cached model.
    """

    def test_empty_input_returns_empty(self) -> None:
        assert score_texts([]) == []

    def test_positive_text_scores_positive(self) -> None:
        result = score_texts(["The company reported record profits and strong revenue growth."])
        assert len(result) == 1
        assert result[0]["label"] == "positive"
        assert 0 <= result[0]["confidence"] <= 1

    def test_negative_text_scores_negative(self) -> None:
        result = score_texts(["The company reported massive losses and declining sales."])
        assert result[0]["label"] == "negative"

    def test_batch_returns_one_result_per_text(self) -> None:
        texts = [
            "Profits soared this quarter.",
            "The stock crashed after the announcement.",
            "The meeting is scheduled for Tuesday.",
        ]
        results = score_texts(texts)
        assert len(results) == 3


class TestAggregateSentiment:
    def test_empty_returns_neutral_default(self) -> None:
        result = aggregate_sentiment([])
        assert result["overall_label"] == "neutral"
        assert result["overall_confidence"] == 0.0

    def test_majority_label_wins(self) -> None:
        scored = [
            {"label": "positive", "confidence": 0.9},
            {"label": "positive", "confidence": 0.8},
            {"label": "negative", "confidence": 0.95},
        ]
        result = aggregate_sentiment(scored)
        assert result["overall_label"] == "positive"
        assert result["overall_confidence"] == 0.85  # avg of the two positive confidences