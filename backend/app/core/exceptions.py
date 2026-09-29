from fastapi import HTTPException, status

class AuraRAGException(Exception):
    """Base exception for AuraRAG errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class AuthenticationException(AuraRAGException):
    """Raised when API key or authentication fails."""
    pass

class DocumentProcessingException(AuraRAGException):
    """Raised when PDF extraction, chunking or parsing fails."""
    pass

class DocumentNotFoundException(AuraRAGException):
    """Raised when requested document is not found in session."""
    pass

class ToolExecutionException(AuraRAGException):
    """Raised when dynamic tool invocation fails."""
    pass

class SecurityViolationException(AuraRAGException):
    """Raised when suspicious prompt injection or path traversal is detected."""
    pass

class VectorStoreException(AuraRAGException):
    """Raised when indexing or retrieval encounters vector DB errors."""
    pass
