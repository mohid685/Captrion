from app.core.embeddings import embed_query, embed_texts


class TestEmbeddings:
    """
    These load the real local model, so the first run will download it
    (~1.3GB) and may be slow. Subsequent runs use the cached model.
    """

    def test_embed_texts_returns_correct_shape(self) -> None:
        vectors = embed_texts(["Apple reported strong quarterly revenue."])
        assert len(vectors) == 1
        assert len(vectors[0]) == 1024

    def test_embed_texts_empty_input(self) -> None:
        assert embed_texts([]) == []

    def test_embed_query_returns_single_vector(self) -> None:
        vector = embed_query("What was Tesla's revenue growth?")
        assert len(vector) == 1024

    def test_similar_texts_have_higher_cosine_similarity(self) -> None:
        import numpy as np

        vectors = embed_texts(
            [
                "The company's revenue grew 20% year over year.",
                "Quarterly sales increased twenty percent from last year.",
                "The weather in Paris was sunny today.",
            ]
        )
        v0, v1, v2 = (np.array(v) for v in vectors)
        sim_related = np.dot(v0, v1)
        sim_unrelated = np.dot(v0, v2)
        assert sim_related > sim_unrelated