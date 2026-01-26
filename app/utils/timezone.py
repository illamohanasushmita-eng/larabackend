from datetime import datetime, timedelta, timezone

def get_ist_time():
    """Returns the current time in IST (UTC+5:30) as an aware datetime object."""
    return datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
