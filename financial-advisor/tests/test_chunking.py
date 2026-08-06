from app.ingestion.chunking import chunk_text, clean_text


class TestCleanText:
    def test_strips_html_tags(self) -> None:
        raw = "<p>Revenue grew <b>10%</b> this quarter.</p>"
        assert clean_text(raw) == "Revenue grew 10% this quarter."

    def test_collapses_whitespace(self) -> None:
        raw = "Line one\n\n\nLine   two"
        assert clean_text(raw) == "Line one Line two"


class TestChunkText:
    def test_empty_text_returns_no_chunks(self) -> None:
        assert chunk_text("") == []

    def test_short_text_returns_single_chunk(self) -> None:
        text = " ".join(["word"] * 50)
        chunks = chunk_text(text, chunk_size_words=400, overlap_words=50)
        assert len(chunks) == 1

    def test_long_text_produces_overlapping_chunks(self) -> None:
        text = " ".join(f"word{i}" for i in range(1000))
        chunks = chunk_text(text, chunk_size_words=400, overlap_words=50)
        assert len(chunks) > 1
        # the overlap region is exactly `overlap_words` wide: the tail of
        # chunk 1 and the head of chunk 2 should match exactly there
        chunk1_tail = chunks[0].split()[-50:]
        chunk2_head = chunks[1].split()[:50]
        assert chunk1_tail == chunk2_head

    def test_invalid_overlap_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            chunk_text("some text", chunk_size_words=50, overlap_words=50)