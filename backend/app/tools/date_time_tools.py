from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Dict, Any
from pydantic import BaseModel, Field
import pytz

class RelativeDateInput(BaseModel):
    days_offset: int = Field(
        ..., 
        description="Number of days relative to today. 0=today, 1=tomorrow, -1=yesterday, positive=future, negative=past."
    )
    timezone: str = Field(
        default="UTC", 
        description="Valid IANA timezone string, e.g., 'Asia/Kolkata', 'America/New_York', 'UTC', 'Asia/Tokyo'."
    )

def _get_tz(tz_str: str):
    cleaned = tz_str.strip() if tz_str else "UTC"
    try:
        return pytz.timezone(cleaned), cleaned
    except Exception:
        return pytz.UTC, "UTC (fallback)"

def get_relative_date(days_offset: int, timezone: str = "UTC") -> Dict[str, Any]:
    """Calculates a past or future date relative to the authoritative current time in the given timezone."""
    tz, tz_name = _get_tz(timezone)
    now = datetime.now(tz)
    target_date = now + timedelta(days=days_offset)
    
    return {
        "success": True,
        "days_offset": days_offset,
        "calculated_date": target_date.strftime("%Y-%m-%d"),
        "day_of_week": target_date.strftime("%A"),
        "formatted": target_date.strftime("%B %d, %Y"),
        "timezone": tz_name
    }

class CurrentDateTimeInput(BaseModel):
    timezone: str = Field(
        default="UTC",
        description="Valid IANA timezone string, e.g., 'Asia/Kolkata', 'America/New_York', 'UTC', 'Asia/Tokyo'."
    )

def get_current_datetime(timezone: str = "UTC") -> Dict[str, Any]:
    """Retrieves authoritative current date and time for a given timezone."""
    tz, tz_name = _get_tz(timezone)
    now = datetime.now(tz)
    return {
        "success": True,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%I:%M:%S %p"),
        "iso": now.isoformat(),
        "day_of_week": now.strftime("%A"),
        "timezone": tz_name
    }
