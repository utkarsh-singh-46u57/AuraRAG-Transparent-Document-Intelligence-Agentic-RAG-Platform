import pytest
from app.services.document_parser import document_parser
from app.services.chunking import chunker
from app.services.vector_store import vector_store
from app.services.rag_engine import rag_engine

def test_hybrid_search_and_rrf(sample_apollo_pdf_bytes):
    doc_id = "doc_rag_test"
    session_id = "sess_rag_test"

    parsed = document_parser.parse_pdf_bytes(sample_apollo_pdf_bytes, "apollo.pdf", doc_id)
    chunks = chunker.chunk_document(parsed)
    vector_store.index_chunks(chunks=chunks, session_id=session_id)

    # Search for specific lexical terms: "Saturn V rocket"
    results = vector_store.hybrid_search(
        query="Saturn V rocket thrust",
        document_id=doc_id,
        session_id=session_id,
        top_k=3
    )

    assert len(results) > 0
    top_hit = results[0]
    assert "Saturn V" in top_hit.text or "rocket" in top_hit.text
    assert top_hit.page_number == 2
    assert top_hit.score >= 0.65

    # Clean up
    vector_store.delete_document(doc_id, session_id)

def test_rag_engine_untrusted_xml_isolation(sample_apollo_pdf_bytes):
    doc_id = "doc_rag_xml"
    session_id = "sess_rag_xml"

    parsed = document_parser.parse_pdf_bytes(sample_apollo_pdf_bytes, "apollo.pdf", doc_id)
    chunks = chunker.chunk_document(parsed)
    vector_store.index_chunks(chunks=chunks, session_id=session_id)

    citations = rag_engine.retrieve(
        query="Apollo 11 Eagle Neil Armstrong",
        document_id=doc_id,
        session_id=session_id,
        top_k=2
    )

    prompt = rag_engine.build_system_prompt(citations=citations, rag_mode="auto")

    assert "<system_policy>" in prompt
    assert "<untrusted_document_context>" in prompt
    assert "</untrusted_document_context>" in prompt
    assert 'page="1"' in prompt
    assert "Neil Armstrong" in prompt

    # Clean up
    vector_store.delete_document(doc_id, session_id)
