import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    DocumentChunksResponse,
    DocumentDeleteResponse,
)
from app.models.domain import DocumentMetadata
from app.core.session import session_manager
from app.core.security import validate_session_id
from app.services.document_parser import document_parser
from app.services.chunking import chunker
from app.services.vector_store import vector_store

router = APIRouter(prefix="/documents", tags=["Document Intelligence"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form("default_session"),
    provider: str = Form("gemini"),
    api_key: Optional[str] = Form(None)
):
    """
    Handles PDF upload, coordinate-aware parsing, semantic chunking, and hybrid indexing.
    """
    clean_session = validate_session_id(session_id)

    # Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF files are allowed."
        )

    # Read bytes and check size
    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    session_dir = settings.UPLOAD_DIR / clean_session
    session_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = session_dir / f"{document_id}.pdf"

    with open(pdf_path, "wb") as f:
        f.write(file_bytes)

    # Extract text and layout coordinates
    try:
        parsed_doc = document_parser.parse_pdf_bytes(
            file_bytes=file_bytes,
            filename=file.filename,
            document_id=document_id
        )
    except Exception as e:
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse PDF document: {str(e)}"
        )

    # Generate structured recursive chunks
    chunks = chunker.chunk_document(parsed_doc)

    metadata = DocumentMetadata(
        document_id=document_id,
        session_id=clean_session,
        filename=file.filename,
        file_size_bytes=len(file_bytes),
        page_count=parsed_doc.total_pages,
        chunk_count=len(chunks),
        char_count=parsed_doc.total_characters,
        status="ready",
        created_at=datetime.utcnow().isoformat(),
        is_scanned=parsed_doc.is_scanned
    )

    # Register in session manager
    session_manager.register_document(metadata, chunks)

    # Initialize embedding provider with provided credentials
    from app.services.embeddings import get_embedding_provider
    embedding_provider = get_embedding_provider(provider=provider, api_key=api_key)

    # Index chunks in persistent vector store + BM25
    vector_store.index_chunks(chunks=chunks, session_id=clean_session, embedding_provider=embedding_provider)

    return DocumentUploadResponse(
        document_id=document_id,
        session_id=clean_session,
        filename=file.filename,
        page_count=parsed_doc.total_pages,
        chunk_count=len(chunks),
        char_count=parsed_doc.total_characters,
        status="ready",
        message="Document successfully processed and indexed for hybrid retrieval."
    )

@router.get("/status/{doc_id}", response_model=DocumentStatusResponse)
async def get_document_status(doc_id: str):
    """Returns indexing lifecycle status of a document."""
    doc = session_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found."
        )
    return DocumentStatusResponse(
        document_id=doc.document_id,
        status=doc.status,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message
    )

@router.get("/{doc_id}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(
    doc_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200)
):
    """Retrieves paginated chunks for inspection with bounding box coordinates."""
    chunks = session_manager.get_document_chunks(doc_id)
    total_chunks = len(chunks)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged = chunks[start_idx:end_idx]

    return DocumentChunksResponse(
        document_id=doc_id,
        total_chunks=total_chunks,
        page=page,
        page_size=page_size,
        chunks=paged
    )

@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(doc_id: str, session_id: Optional[str] = Query(default=None)):
    """
    Cascading deletion: removes raw PDF from disk, in-memory chunks,
    and vector embeddings from ChromaDB.
    """
    doc = session_manager.get_document(doc_id)
    session_id_clean = doc.session_id if doc else (validate_session_id(session_id) if session_id else None)

    # 1. Delete from vector store
    vector_store.delete_document(document_id=doc_id, session_id=session_id_clean)

    # 2. Delete from session manager
    deleted = session_manager.delete_document(doc_id)

    # 3. Delete file from disk
    if session_id_clean:
        pdf_path = settings.UPLOAD_DIR / session_id_clean / f"{doc_id}.pdf"
        if pdf_path.exists():
            pdf_path.unlink()

    return DocumentDeleteResponse(
        success=True,
        document_id=doc_id,
        message=f"Document '{doc_id}' and all associated chunks and embeddings were deleted."
    )

@router.get("/{doc_id}/file")
async def get_document_file(doc_id: str, session_id: Optional[str] = Query(default=None)):
    """Serves the PDF file bytes for in-browser canvas rendering."""
    doc = session_manager.get_document(doc_id)
    session_id_clean = doc.session_id if doc else (validate_session_id(session_id) if session_id else "default_session")
    pdf_path = settings.UPLOAD_DIR / session_id_clean / f"{doc_id}.pdf"

    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file for '{doc_id}' not found."
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=doc.filename if doc else f"{doc_id}.pdf"
    )
