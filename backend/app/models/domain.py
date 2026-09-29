from typing import Optional, List
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float
    page_width: float = 0.0
    page_height: float = 0.0

    def to_normalized_list(self) -> list[float]:
        return [round(self.x0, 2), round(self.y0, 2), round(self.x1, 2), round(self.y1, 2)]

class DocumentChunk(BaseModel):
    document_id: str
    chunk_id: str
    page_number: int
    paragraph_number: int
    section_heading: Optional[str] = None
    text: str
    bbox: Optional[list[float]] = None
    char_count: int = 0
    token_estimate: int = 0

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "paragraph_number": self.paragraph_number,
            "section_heading": self.section_heading,
            "text": self.text,
            "bbox": self.bbox,
            "char_count": len(self.text),
            "token_estimate": len(self.text) // 4
        }

class DocumentMetadata(BaseModel):
    document_id: str
    session_id: str
    filename: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    char_count: int
    status: str = "ready"  # uploading, extracting, chunking, embedding, ready, error
    error_message: Optional[str] = None
    created_at: str
    is_scanned: bool = False

class Citation(BaseModel):
    chunk_id: str
    page_number: int
    paragraph_number: Optional[int] = None
    score: float
    text: str
    bbox: Optional[list[float]] = None
    section_heading: Optional[str] = None
