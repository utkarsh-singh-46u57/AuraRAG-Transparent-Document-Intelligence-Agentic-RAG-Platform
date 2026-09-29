from fastapi import APIRouter, Query
from app.models.schemas import TimeToolResponse, RelativeDateResponse
from app.tools.date_time_tools import get_current_datetime, get_relative_date, RelativeDateInput
from app.tools.registry import tool_registry

router = APIRouter(prefix="/tools", tags=["Deterministic Tools"])

@router.get("/time", response_model=TimeToolResponse)
async def check_current_time(timezone: str = Query(default="UTC", description="IANA timezone identifier")):
    """
    Direct health check endpoint for authoritative timezone-aware date and time calculations.
    """
    result = get_current_datetime(timezone=timezone)
    return TimeToolResponse(**result)

@router.post("/relative-date", response_model=RelativeDateResponse)
async def calculate_relative_date(payload: RelativeDateInput):
    """
    Direct calculation of relative past/future dates.
    """
    result = get_relative_date(days_offset=payload.days_offset, timezone=payload.timezone)
    return RelativeDateResponse(**result)

@router.get("/list")
async def list_available_tools():
    """Lists registered tools with schemas for agent inspection."""
    tools = []
    for name, tool in tool_registry._tools.items():
        tools.append({
            "name": name,
            "description": tool.description,
            "parameters": tool.schema.model_json_schema()
        })
    return {"tools": tools}
