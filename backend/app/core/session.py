import time
import threading
from typing import Dict, Optional, List
from app.models.domain import DocumentMetadata, DocumentChunk

class SessionManager:
    """
    In-memory session manager that maintains document metadata and isolates
    tenants by session_id without storing sensitive user keys permanently.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._documents: Dict[str, DocumentMetadata] = {}  # doc_id -> metadata
        self._chunks: Dict[str, List[DocumentChunk]] = {}  # doc_id -> list of chunks
        self._session_docs: Dict[str, set[str]] = {}       # session_id -> set of doc_ids

    def register_document(self, metadata: DocumentMetadata, chunks: List[DocumentChunk]):
        with self._lock:
            doc_id = metadata.document_id
            session_id = metadata.session_id
            self._documents[doc_id] = metadata
            self._chunks[doc_id] = chunks
            if session_id not in self._session_docs:
                self._session_docs[session_id] = set()
            self._session_docs[session_id].add(doc_id)

    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        with self._lock:
            return self._documents.get(doc_id)

    def get_document_chunks(self, doc_id: str) -> List[DocumentChunk]:
        with self._lock:
            return self._chunks.get(doc_id, [])

    def get_session_documents(self, session_id: str) -> List[DocumentMetadata]:
        with self._lock:
            doc_ids = self._session_docs.get(session_id, set())
            return [self._documents[doc_id] for doc_id in doc_ids if doc_id in self._documents]

    def update_status(self, doc_id: str, status: str, error_message: Optional[str] = None):
        with self._lock:
            doc = self._documents.get(doc_id)
            if doc:
                doc.status = status
                if error_message:
                    doc.error_message = error_message

    def delete_document(self, doc_id: str) -> bool:
        with self._lock:
            if doc_id in self._documents:
                session_id = self._documents[doc_id].session_id
                if session_id in self._session_docs and doc_id in self._session_docs[session_id]:
                    self._session_docs[session_id].remove(doc_id)
                del self._documents[doc_id]
                if doc_id in self._chunks:
                    del self._chunks[doc_id]
                return True
            return False

session_manager = SessionManager()
