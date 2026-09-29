from fastapi import APIRouter, HTTPException, status
from app.models.schemas import LLMVerifyRequest, LLMVerifyResponse
from app.providers import get_llm_provider
from app.core.security import sanitize_user_input

router = APIRouter(prefix="/llm", tags=["LLM Configuration"])

@router.post("/verify", response_model=LLMVerifyResponse)
async def verify_llm_key(request: LLMVerifyRequest):
    """
    Validates ephemeral API keys and connection health without persisting keys to disk or logs.
    """
    clean_provider = sanitize_user_input(request.provider).lower()
    clean_key = request.api_key.strip()
    clean_model = sanitize_user_input(request.model_name) if request.model_name else None

    if not clean_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key cannot be empty."
        )

    provider = get_llm_provider(clean_provider)
    result = await provider.verify_connection(clean_key, clean_model)

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("message", "LLM validation failed.")
        )

    return LLMVerifyResponse(
        success=True,
        provider=clean_provider,
        model_name=result.get("model_name", clean_model or "default"),
        message=result.get("message", "Connected successfully"),
        available_models=result.get("available_models", [])
    )
