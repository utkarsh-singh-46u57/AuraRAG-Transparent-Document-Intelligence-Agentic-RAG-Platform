from datetime import datetime, timezone
import pytest
from app.tools.date_time_tools import get_relative_date, get_current_datetime
from app.tools.registry import tool_registry

def test_relative_date_today():
    res = get_relative_date(days_offset=0, timezone="UTC")
    assert res["success"] is True
    assert res["days_offset"] == 0
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert res["calculated_date"] == now_str
    assert "day_of_week" in res
    assert "formatted" in res

def test_relative_date_tomorrow():
    res = get_relative_date(days_offset=1, timezone="UTC")
    assert res["success"] is True
    assert res["days_offset"] == 1
    # Day diff check
    today_res = get_relative_date(days_offset=0, timezone="UTC")
    d1 = datetime.strptime(today_res["calculated_date"], "%Y-%m-%d")
    d2 = datetime.strptime(res["calculated_date"], "%Y-%m-%d")
    assert (d2 - d1).days == 1

def test_relative_date_yesterday():
    res = get_relative_date(days_offset=-1, timezone="UTC")
    assert res["success"] is True
    assert res["days_offset"] == -1
    today_res = get_relative_date(days_offset=0, timezone="UTC")
    d1 = datetime.strptime(today_res["calculated_date"], "%Y-%m-%d")
    d2 = datetime.strptime(res["calculated_date"], "%Y-%m-%d")
    assert (d1 - d2).days == 1

def test_relative_date_future_offset():
    res = get_relative_date(days_offset=4, timezone="Asia/Kolkata")
    assert res["success"] is True
    assert res["days_offset"] == 4
    today_res = get_relative_date(days_offset=0, timezone="Asia/Kolkata")
    d1 = datetime.strptime(today_res["calculated_date"], "%Y-%m-%d")
    d2 = datetime.strptime(res["calculated_date"], "%Y-%m-%d")
    assert (d2 - d1).days == 4

def test_current_datetime_timezone():
    res = get_current_datetime(timezone="Asia/Kolkata")
    assert res["success"] is True
    assert res["timezone"] == "Asia/Kolkata"
    assert "date" in res
    assert "time" in res
    assert "iso" in res
    assert "day_of_week" in res

def test_tool_registry_execution():
    result = tool_registry.execute("get_relative_date", {"days_offset": 2, "timezone": "UTC"})
    assert result["success"] is True
    assert result["days_offset"] == 2

def test_tool_registry_validation_error():
    # Invalid argument type or missing required
    result = tool_registry.execute("get_relative_date", {"days_offset": "invalid_offset"})
    assert result["success"] is False
    assert "error" in result
