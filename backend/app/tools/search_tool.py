from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.services.rag_engine import rag_engine

class SearchDocumentInput(BaseModel):
    query: str = Field(..., description="Semantic or lexical search query to find passages in the document")
    document_id: str = Field(..., description="Identifier of the indexed PDF document")
    top_k: int = Field(default=5, ge=1, le=10, description="Maximum number of relevant passages to retrieve")

def search_document(query: str, document_id: str, top_k: int = 5, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Searches the indexed PDF document for passages semantically and lexically matching the query."""
    results = rag_engine.retrieve(query=query, document_id=document_id, session_id=session_id, top_k=top_k)
    return {
        "success": True,
        "query": query,
        "document_id": document_id,
        "retrieved_chunks": [
            {
                "chunk_id": r.chunk_id,
                "page_number": r.page_number,
                "paragraph_number": r.paragraph_number,
                "score": r.score,
                "text": r.text,
                "bbox": r.bbox,
                "section_heading": r.section_heading
            }
            for r in results
        ]
    }
