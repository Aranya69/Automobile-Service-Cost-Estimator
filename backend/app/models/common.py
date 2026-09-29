from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    """ISO 8601 string in UTC. SQLite drops the timezone, so add it back."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")
