import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from app.providers.base import BaseLLMProvider
from app.models.schemas import ChatStreamRequest
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI Function-calling provider fallback.
    """

    async def verify_connection(self, api_key: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        target_model = model_name or "gpt-4o"
        if api_key in ["mock_key", "test_key", "mock"]:
            return {
                "success": True,
                "provider": "openai",
                "model_name": target_model,
                "message": "Connection verified (Test/Mock environment)",
                "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            models = await asyncio.to_thread(client.models.list)
            return {
                "success": True,
                "provider": "openai",
                "model_name": target_model,
                "message": "Successfully connected to OpenAI",
                "available_models": [m.id for m in models.data if "gpt" in m.id][:5]
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "openai",
                "model_name": target_model,
                "message": f"Connection failed: {str(e)}",
                "available_models": []
            }

    async def stream_chat(
        self,
        request: ChatStreamRequest,
        system_prompt: str,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        api_key = request.api_key
        model_name = request.model_name or "gpt-4o"

        if not api_key or api_key in ["mock_key", "test_key", "mock"]:
            from app.providers.gemini_provider import gemini_provider
            async for ev in gemini_provider._mock_chat_stream(request, system_prompt, context):
                yield ev
            return

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            messages = [{"role": "system", "content": system_prompt}]
            for h in request.history:
                messages.append({"role": h.role, "content": h.content})
            messages.append({"role": "user", "content": f"[Client Timezone: {request.timezone}]\n{request.query}"})

            tools = tool_registry.get_openai_tools() if request.rag_mode != "general_ai" else None

            # First turn: check tool calls
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto" if tools else None,
                stream=False
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except Exception:
                        fn_args = {}

                    yield {
                        "event": "tool_start",
                        "data": {"tool": fn_name, "args": fn_args}
                    }

                    res = tool_registry.execute(fn_name, fn_args, context)

                    yield {
                        "event": "tool_end",
                        "data": {"tool": fn_name, "result": res}
                    }

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": json.dumps(res)
                    })

                # Stream second turn
                stream = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=model_name,
                    messages=messages,
                    stream=True
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta else None
                    if delta:
                        yield {"event": "delta", "data": {"text": delta}}
            else:
                if msg.content:
                    yield {"event": "delta", "data": {"text": msg.content}}

            yield {"event": "done", "data": {"finish_reason": "stop"}}

        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            yield {"event": "delta", "data": {"text": f"\n\n*[OpenAI Error: {str(e)}]*"}}
            yield {"event": "done", "data": {"finish_reason": "error"}}

openai_provider = OpenAIProvider()
