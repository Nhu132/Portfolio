import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Job:
    source: str
    title: str
    company: str
    url: str
    location: str = ""
    remote: bool = False
    salary: str = ""
    posted_at: datetime | None = None
    description: str = ""
    # Điền bởi bước chấm điểm (matching.py)
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    years_required: str = ""

    @property
    def key(self) -> str:
        """Khoá chống trùng: cùng vị trí + công ty ở nhiều nguồn chỉ giữ một."""
        raw = f"{_norm(self.title)}|{_norm(self.company)}"
        return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").lower()
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()
