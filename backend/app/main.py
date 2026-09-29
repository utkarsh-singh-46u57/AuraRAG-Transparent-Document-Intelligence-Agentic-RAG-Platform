import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import llm_router, documents_router, tools_router, chat_router
from app.core.exceptions import AuraRAGException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aurarag")

app = FastAPI(
    title="AuraRAG API",
    description="Production-grade Transparent Document Intelligence & Agentic RAG Platform",
    version="1.0.0"
)

# CORS middleware for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(AuraRAGException)
async def aurarag_exception_handler(request: Request, exc: AuraRAGException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"success": False, "error": exc.message, "details": exc.details}
    )

# Include API Routers
app.include_router(llm_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(tools_router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
@app.get(f"{settings.API_V1_PREFIX}/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AuraRAG",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to AuraRAG Document Intelligence & Agentic RAG API",
        "docs": "/docs"
    }
