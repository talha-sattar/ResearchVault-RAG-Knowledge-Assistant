from app.llm.generation import parse_citations
from app.retrieval.retriever import RetrievedChunk


def _chunk(i: int) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"chunk-{i}",
        document_id=f"doc-{i}",
        arxiv_id=f"2606.0000{i}",
        title=f"Paper {i}",
        section_type="results",
        page_start=i,
        page_end=i,
        content="content",
        parent_content=None,
        rerank_score=1.0,
    )


def test_parse_citations_resolves_doc_index_and_page():
    chunks = [_chunk(1), _chunk(2)]
    text = "The model achieves 90% accuracy [Doc 1, p.3]. It outperforms baselines [Doc 2, p.5]."
    citations = parse_citations(text, chunks)
    assert len(citations) == 2
    assert citations[0].chunk_id == "chunk-1"
    assert citations[0].page == 3
    assert citations[1].chunk_id == "chunk-2"
    assert citations[1].page == 5


def test_parse_citations_defaults_page_to_chunk_page_start_when_omitted():
    chunks = [_chunk(1)]
    citations = parse_citations("Some claim [Doc 1].", chunks)
    assert len(citations) == 1
    assert citations[0].page == chunks[0].page_start


def test_parse_citations_drops_hallucinated_doc_index():
    chunks = [_chunk(1)]
    # Doc 5 was never provided - this is exactly the "unsupported citation" case the eval
    # harness's citation-precision metric is designed to catch.
    citations = parse_citations("Some claim [Doc 5, p.1].", chunks)
    assert citations == []


def test_parse_citations_handles_no_citations():
    assert parse_citations("No citations here.", [_chunk(1)]) == []


def test_parse_citations_handles_page_range():
    # Context blocks render multi-page chunks as "p.19-20" and the LLM mirrors that format -
    # regression test for a real bug where such citations were silently dropped.
    chunks = [_chunk(1)]
    citations = parse_citations("Some claim [Doc 1, p.19-20].", chunks)
    assert len(citations) == 1
    assert citations[0].page == 19


def test_parse_citations_handles_multiple_docs_in_one_bracket():
    # Real model output combines citations into one bracket: "[Doc 1, p.1; Doc 5, p.16]" -
    # regression test for a bug where the whole bracket was silently dropped.
    chunks = [_chunk(1), _chunk(2), _chunk(3), _chunk(4), _chunk(5)]
    citations = parse_citations("A claim [Doc 1, p.1; Doc 5, p.16].", chunks)
    assert len(citations) == 2
    assert (citations[0].doc_index, citations[0].page) == (1, 1)
    assert (citations[1].doc_index, citations[1].page) == (5, 16)
