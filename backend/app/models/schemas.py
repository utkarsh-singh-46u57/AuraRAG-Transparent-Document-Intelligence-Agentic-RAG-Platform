from typing import Optional, List, Any
from pydantic import BaseModel, Field
from app.models.domain import DocumentChunk, Citation

class LLMVerifyRequest(BaseModel):
    provider: str = Field(default="gemini", description="LLM provider: gemini or openai")
    api_key: str = Field(..., description="User's ephemeral API key")
    model_name: Optional[str] = Field(default=None, description="Model ID to verify")

class LLMVerifyResponse(BaseModel):
    success: bool
    provider: str
    model_name: str
    message: str
    available_models: List[str] = []

class DocumentUploadResponse(BaseModel):
    document_id: str
    session_id: str
    filename: str
    page_count: int
    chunk_count: int
    char_count: int
    status: str
    message: str = "Document successfully ingested and indexed"

class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    page_count: int = 0
    chunk_count: int = 0
    error_message: Optional[str] = None

class DocumentChunksResponse(BaseModel):
    document_id: str
    total_chunks: int
    page: int = 1
    page_size: int = 50
    chunks: List[DocumentChunk]

class DocumentDeleteResponse(BaseModel):
    success: bool
    document_id: str
    message: str

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str
    timestamp: Optional[str] = None

class ChatStreamRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question or instruction")
    session_id: str = Field(default="default_session", description="Session identifier for multi-tenant isolation")
    document_id: Optional[str] = Field(default=None, description="Active document ID for RAG context")
    rag_mode: str = Field(default="auto", description="'auto', 'document_only', or 'general_ai'")
    provider: str = Field(default="gemini", description="'gemini' or 'openai'")
    model_name: str = Field(default="gemini-2.5-flash", description="Configured model name")
    api_key: Optional[str] = Field(default=None, description="Ephemeral user API key (zero-storage)")
    timezone: str = Field(default="UTC", description="Client IANA timezone string")
    history: List[ChatMessage] = Field(default_factory=list, description="Recent conversation turns")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.65, ge=0.0, le=1.0, description="Minimum relevance threshold")

class TimeToolResponse(BaseModel):
    success: bool
    date: str
    time: str
    iso: str
    day_of_week: str
    timezone: str

class RelativeDateResponse(BaseModel):
    success: bool
    days_offset: int
    calculated_date: str
    day_of_week: str
    formatted: str
    timezone: str
