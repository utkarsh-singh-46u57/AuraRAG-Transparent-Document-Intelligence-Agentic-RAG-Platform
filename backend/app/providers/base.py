from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.models.schemas import ChatStreamRequest

class BaseLLMProvider(ABC):
    """Abstract interface for LLM chat and function-calling providers."""

    @abstractmethod
    async def verify_connection(self, api_key: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Validates API credentials and checks model availability."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        request: ChatStreamRequest,
        system_prompt: str,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streams chat tokens and tool events via SSE."""
        pass
