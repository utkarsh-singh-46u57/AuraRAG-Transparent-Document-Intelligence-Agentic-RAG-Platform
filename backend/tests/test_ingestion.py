import pytest
from app.services.document_parser import document_parser
from app.services.chunking import chunker
from app.core.session import session_manager
from app.models.domain import DocumentMetadata

def test_document_parser_coordinates(sample_apollo_pdf_bytes):
    parsed = document_parser.parse_pdf_bytes(
        file_bytes=sample_apollo_pdf_bytes,
        filename="apollo.pdf",
        document_id="doc_test_123"
    )

    assert parsed.total_pages == 2
    assert parsed.total_characters > 100
    assert len(parsed.blocks) >= 3
    assert not parsed.is_scanned

    # Check bounding box normalization
    first_block = parsed.blocks[0]
    assert len(first_block.bbox) == 4
    # All normalized coordinates must be between 0 and 100
    for coord in first_block.bbox:
        assert 0.0 <= coord <= 100.0

def test_chunking_structural_integrity(sample_apollo_pdf_bytes):
    parsed = document_parser.parse_pdf_bytes(
        file_bytes=sample_apollo_pdf_bytes,
        filename="apollo.pdf",
        document_id="doc_test_123"
    )
    chunks = chunker.chunk_document(parsed)

    assert len(chunks) >= 3
    first_chunk = chunks[0]
    assert first_chunk.document_id == "doc_test_123"
    assert first_chunk.chunk_id.startswith("chk_p01_b")
    assert first_chunk.page_number == 1
    assert first_chunk.bbox is not None
    assert len(first_chunk.text) > 0

def test_session_manager_registration(sample_apollo_pdf_bytes):
    parsed = document_parser.parse_pdf_bytes(
        file_bytes=sample_apollo_pdf_bytes,
        filename="apollo.pdf",
        document_id="doc_session_test"
    )
    chunks = chunker.chunk_document(parsed)

    meta = DocumentMetadata(
        document_id="doc_session_test",
        session_id="test_session_1",
        filename="apollo.pdf",
        file_size_bytes=len(sample_apollo_pdf_bytes),
        page_count=parsed.total_pages,
        chunk_count=len(chunks),
        char_count=parsed.total_characters,
        status="ready",
        created_at="2026-09-28T00:00:00"
    )

    session_manager.register_document(meta, chunks)

    retrieved_meta = session_manager.get_document("doc_session_test")
    assert retrieved_meta is not None
    assert retrieved_meta.filename == "apollo.pdf"

    retrieved_chunks = session_manager.get_document_chunks("doc_session_test")
    assert len(retrieved_chunks) == len(chunks)

    # Clean up
    session_manager.delete_document("doc_session_test")
    assert session_manager.get_document("doc_session_test") is None
