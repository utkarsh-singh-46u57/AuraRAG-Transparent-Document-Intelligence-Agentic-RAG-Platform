import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AuraRAG"
    API_V1_PREFIX: str = "/api"
    
    # Base directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    CHROMA_PERSIST_DIR: Path = DATA_DIR / "chroma"
    
    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "gemini"
    DEFAULT_GEMINI_MODEL: str = "gemini-3.8-flash"
    DEFAULT_OPENAI_MODEL: str = "gpt-4o"
    
    # RAG Engine Settings
    DEFAULT_CHUNK_SIZE: int = 600
    DEFAULT_CHUNK_OVERLAP: int = 100
    DEFAULT_TOP_K: int = 5
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.65
    RRF_K: int = 60
    
    # Document Constraints
    MAX_FILE_SIZE_BYTES: int = 30 * 1024 * 1024  # 30 MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
