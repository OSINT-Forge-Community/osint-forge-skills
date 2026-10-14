"""Preserve original timestamps. Never invent a missing timezone."""

from datetime import datetime, timedelta, timezone


def timestamp(value: object) -> dict:
    original = "" if value is None else str(value)
    if not original:
        return {"original_timestamp": original, "utc": None, "time_status": "missing"}
    try:
        parsed = datetime.fromisoformat(original.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return {"original_timestamp": original, "utc": None, "time_status": "invalid"}
    if parsed.tzinfo is None:
        return {"original_timestamp": original, "utc": None,
                "time_status": "timezone_unknown"}
    return {"original_timestamp": original,
            "utc": parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "time_status": "normalized"}


def browser_timestamp(value: object, family: str) -> dict:
    try:
        epoch = datetime(1601 if family == "chromium" else 1970, 1, 1,
                         tzinfo=timezone.utc)
        parsed = epoch + timedelta(microseconds=int(value))
        return {"original_timestamp": str(value), "utc": parsed.isoformat().replace(
            "+00:00", "Z"), "time_status": "normalized",
            "timestamp_encoding": family + "_microseconds"}
    except (ValueError, TypeError, OverflowError):
        return {"original_timestamp": str(value), "utc": None, "time_status": "invalid"}
