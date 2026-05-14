"""Workout record storage using Vercel KV (Redis) or local JSON fallback."""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tokyo"))
_LOCAL_PATH = "/tmp/fitness_records.json"


def _today() -> str:
    return datetime.now(_TZ).strftime("%Y-%m-%d")


def _get_redis():
    """Return a Redis client if KV_URL is configured, else None."""
    kv_url = os.getenv("KV_URL")
    if not kv_url:
        return None
    try:
        import redis
        return redis.from_url(kv_url, decode_responses=True)
    except Exception:
        return None


def _load_local() -> dict:
    if os.path.exists(_LOCAL_PATH):
        with open(_LOCAL_PATH) as f:
            return json.load(f)
    return {}


def _save_local(data: dict) -> None:
    with open(_LOCAL_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_record(did_workout: bool, note: str = "") -> None:
    """Save today's workout result."""
    date = _today()
    record = {
        "date": date,
        "did_workout": did_workout,
        "note": note,
        "recorded_at": datetime.now(_TZ).isoformat(),
    }

    r = _get_redis()
    if r:
        r.set(f"fitness:{date}", json.dumps(record, ensure_ascii=False))
    else:
        data = _load_local()
        data[date] = record
        _save_local(data)


def get_recent_summary(days: int = 7) -> str:
    """Return a brief summary of recent workout records for Claude context."""
    r = _get_redis()
    records: list[dict] = []

    from datetime import timedelta
    for i in range(days):
        from datetime import date
        d = (datetime.now(_TZ) - timedelta(days=i)).strftime("%Y-%m-%d")
        if r:
            raw = r.get(f"fitness:{d}")
            if raw:
                records.append(json.loads(raw))
        else:
            data = _load_local()
            if d in data:
                records.append(data[d])

    if not records:
        return "記録なし（初回利用）"

    done = sum(1 for rec in records if rec.get("did_workout"))
    total = len(records)
    streak = 0
    for rec in records:
        if rec.get("did_workout"):
            streak += 1
        else:
            break

    return (
        f"直近{total}日のうち{done}日実施。"
        f"現在の連続記録: {streak}日。"
    )


def get_today_record() -> dict | None:
    """Return today's record if it exists."""
    date = _today()
    r = _get_redis()
    if r:
        raw = r.get(f"fitness:{date}")
        return json.loads(raw) if raw else None
    else:
        data = _load_local()
        return data.get(date)
