import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime


def parse_date(value) -> datetime | None:
    """Đọc ngày ở nhiều định dạng (ISO, RFC 822, unix, dd/mm/yyyy, '3 days ago')."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        if value > 1e12:  # mili giây
            value /= 1000
        return datetime.fromtimestamp(value, tz=timezone.utc)
    text = str(value).strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError):
        pass
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m:
        d, mo, y = map(int, m.groups())
        return datetime(y, mo, d, tzinfo=timezone.utc)
    return _relative(text)


_UNITS = {
    "minute": 1 / 1440, "phút": 1 / 1440,
    "hour": 1 / 24, "giờ": 1 / 24,
    "day": 1, "ngày": 1,
    "week": 7, "tuần": 7,
    "month": 30, "tháng": 30,
}


def _relative(text: str) -> datetime | None:
    m = re.search(r"(\d+)\+?\s*(minute|hour|day|week|month|phút|giờ|ngày|tuần|tháng)", text.lower())
    if not m:
        return None
    return datetime.now(timezone.utc) - timedelta(days=int(m.group(1)) * _UNITS[m.group(2)])
