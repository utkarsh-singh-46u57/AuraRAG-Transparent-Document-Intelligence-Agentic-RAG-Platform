from typing import Callable, Dict, Any, Type, Optional, List
import logging
from pydantic import BaseModel, ValidationError
from app.tools.date_time_tools import (
    RelativeDateInput,
    get_relative_date,
    CurrentDateTimeInput,
    get_current_datetime,
)
from app.tools.search_tool import SearchDocumentInput, search_document

logger = logging.getLogger(__name__)

class ToolDefinition:
    def __init__(self, name: str, func: Callable, schema: Type[BaseModel], description: str):
        self.name = name
        self.func = func
        self.schema = schema
        self.description = description

class ToolRegistry:
    """
    Central tool registry that validates inputs, executes deterministic tools,
    and builds provider-agnostic schemas for Gemini and OpenAI.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, name: str, func: Callable, schema: Type[BaseModel], description: str):
        self._tools[name] = ToolDefinition(name, func, schema, description)

    def _register_default_tools(self):
        self.register(
            name="get_relative_date",
            func=get_relative_date,
            schema=RelativeDateInput,
            description="Calculates a past or future date relative to the current date in a given IANA timezone. E.g. days_offset=0 for today, 1 for tomorrow, -1 for yesterday."
        )
        self.register(
            name="get_current_datetime",
            func=get_current_datetime,
            schema=CurrentDateTimeInput,
            description="Retrieves the current authoritative date, time, day of week, and ISO timestamp for a specified IANA timezone (e.g., 'Asia/Kolkata', 'UTC', 'America/New_York')."
        )
        self.register(
            name="search_document",
            func=search_document,
            schema=SearchDocumentInput,
            description="Searches the active PDF document for semantic passages or factual statements matching the query."
        )

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def execute(self, name: str, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        tool = self.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' is not registered."}

        context = context or {}
        # Auto-inject document_id or session_id into search_document if missing from model args
        call_args = dict(args)
        if name == "search_document":
            if "document_id" not in call_args or not call_args["document_id"]:
                if "document_id" in context:
                    call_args["document_id"] = context["document_id"]
            if "session_id" in context:
                call_args["session_id"] = context["session_id"]

        try:
            # Validate with Pydantic
            validated = tool.schema(**call_args)
            return tool.func(**validated.model_dump())
        except ValidationError as ve:
            logger.warning(f"Validation error calling tool {name}: {ve.errors()}")
            return {"success": False, "error": f"Invalid arguments for {name}: {ve.errors()}"}
        except Exception as e:
            logger.error(f"Error executing tool {name}: {str(e)}")
            return {"success": False, "error": f"Execution failure: {str(e)}"}

    def get_gemini_declarations(self) -> List[dict]:
        """
        Converts registered tools into function declaration dicts compatible with modern google-genai SDK.
        """
        declarations = []
        for name, tool in self._tools.items():
            schema_json = tool.schema.model_json_schema()
            properties = {}
            for prop_name, prop_data in schema_json.get("properties", {}).items():
                p_type = prop_data.get("type", "string").upper()
                if p_type == "INTEGER":
                    p_type = "INTEGER"
                elif p_type == "NUMBER":
                    p_type = "NUMBER"
                elif p_type == "BOOLEAN":
                    p_type = "BOOLEAN"
                else:
                    p_type = "STRING"

                properties[prop_name] = {
                    "type": p_type,
                    "description": prop_data.get("description", "")
                }

            declarations.append({
                "name": name,
                "description": tool.description,
                "parameters": {
                    "type": "OBJECT",
                    "properties": properties,
                    "required": schema_json.get("required", [])
                }
            })
        return declarations

    def get_openai_tools(self) -> List[dict]:
        """
        Converts registered tools into OpenAI format.
        """
        tools = []
        for name, tool in self._tools.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.schema.model_json_schema()
                }
            })
        return tools

tool_registry = ToolRegistry()
