import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import ChatStreamRequest
from app.core.security import validate_session_id, sanitize_user_input
from app.services.rag_engine import rag_engine
from app.services.embeddings import get_embedding_provider
from app.providers import get_llm_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Agentic Chat & Streaming"])

@router.post("/stream")
async def chat_stream_endpoint(request: ChatStreamRequest):
    """
    Primary agentic chat endpoint with SSE streaming.
    Streams tool invocation events, citations, and output deltas.
    """
    clean_query = sanitize_user_input(request.query)
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )

    clean_session = validate_session_id(request.session_id)
    request.session_id = clean_session

    async def event_generator() -> AsyncGenerator[dict, None]:
        # 1. Hybrid Retrieval (if document attached and not general_ai)
        citations = []
        if request.document_id and request.rag_mode != "general_ai":
            try:
                emb_provider = get_embedding_provider(
                    provider=request.provider,
                    api_key=request.api_key
                )
                citations = rag_engine.retrieve(
                    query=clean_query,
                    document_id=request.document_id,
                    session_id=clean_session,
                    top_k=request.top_k,
                    similarity_threshold=request.similarity_threshold,
                    embedding_provider=emb_provider
                )
            except Exception as e:
                logger.error(f"Error during retrieval: {str(e)}")

        # 2. Emit citation payload event to frontend
        if citations:
            citation_payload = {
                "citations": [
                    {
                        "chunk_id": c.chunk_id,
                        "page": c.page_number,
                        "paragraph": c.paragraph_number,
                        "score": c.score,
                        "text": c.text,
                        "bbox": c.bbox,
                        "heading": c.section_heading
                    }
                    for c in citations
                ]
            }
            yield {
                "event": "citation",
                "data": json.dumps(citation_payload)
            }

        # 3. Assemble secure isolated system prompt
        system_prompt = rag_engine.build_system_prompt(citations=citations, rag_mode=request.rag_mode)

        context = {
            "session_id": clean_session,
            "document_id": request.document_id,
            "citations": citations,
            "timezone": request.timezone
        }

        # 4. Stream response from LLM Provider
        provider = get_llm_provider(request.provider)
        try:
            async for ev in provider.stream_chat(request=request, system_prompt=system_prompt, context=context):
                yield {
                    "event": ev.get("event", "delta"),
                    "data": json.dumps(ev.get("data", {}))
                }
        except Exception as e:
            logger.error(f"Error during LLM stream: {str(e)}")
            yield {
                "event": "delta",
                "data": json.dumps({"text": f"\n\n*[Processing Error: {str(e)}]*"})
            }
            yield {
                "event": "done",
                "data": json.dumps({"finish_reason": "error"})
            }

    return EventSourceResponse(event_generator())
