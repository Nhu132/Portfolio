"""Chấm điểm độ phù hợp của job với hồ sơ trong config.yaml (mục `profile`)."""
import re
from datetime import datetime, timezone

from .models import Job
from .sources.html import plain

_NUM = r"(?<!\d)(\d{1,2})\s*\+?\s*(?:(?:-|–|to|đến)\s*(\d{1,2}))?\s*\+?"
_EXP_PATTERNS = [
    # "5+ years of B2B marketing experience", "3-5 years in content marketing"
    re.compile(_NUM + r"\s*(?:years?|yrs?)['’]?\s+(?:of\s+|in\s+)?(?:[\w&/-]+\s+){0,4}?"
               r"(?:experience|marketing|content|leadership|management)", re.I),
    # "Experience: minimum 3 years"
    re.compile(r"experience[^.\n]{0,30}?" + _NUM + r"\s*(?:years?|yrs?)", re.I),
    # "Ít nhất 3 năm kinh nghiệm"
    re.compile(_NUM + r"\s*năm\s+(?:kinh\s+nghiệm|kn\b)", re.I),
    # "Kinh nghiệm: 3 - 5 năm"
    re.compile(r"kinh\s+nghiệm[^.\n]{0,40}?" + _NUM + r"\s*năm", re.I),
]
_SENIOR_TITLE = re.compile(r"head\s+of|director|giám\s+đốc|trưởng\s+phòng|\bvp\b|chief|\bcmo\b", re.I)
_SENIOR_LEVEL = re.compile(r"seniority\s+level\s*(director|executive)", re.I)


def extract_years(text: str) -> tuple[int, int | None] | None:
    """Số năm kinh nghiệm yêu cầu trong JD, dạng (tối thiểu, tối đa).

    Bỏ qua số >= 10 vì JD tiếng Việt hay có câu kiểu "công ty hơn 10 năm kinh nghiệm".
    Nếu JD nhắc nhiều mốc, lấy mốc tối thiểu cao nhất (yêu cầu khắt khe nhất)."""
    found = []
    for pattern in _EXP_PATTERNS:
        for m in pattern.finditer(text):
            lo = int(m.group(1))
            hi = int(m.group(2)) if m.group(2) else None
            if 1 <= lo <= 9 and (hi is None or lo <= hi <= 15):
                found.append((lo, hi))
    return max(found, key=lambda r: r[0]) if found else None


def _fmt_years(lo: int, hi: int | None) -> str:
    return f"{lo}–{hi} năm" if hi and hi != lo else f"{lo}+ năm"


class Scorer:
    def __init__(self, config: dict):
        profile = config["profile"]
        self.years = profile["years_experience"]
        self.max_above = profile.get("max_years_above", 2)
        self.min_score = profile.get("min_score", 0)
        self.strengths = [(s["label"], re.compile(s["pattern"], re.I), s["points"]) for s in profile["strengths"]]
        self.avoid = [(s["label"], re.compile(s["pattern"], re.I), s["points"]) for s in profile["avoid"]]

    def score(self, job: Job, now: datetime | None = None) -> bool:
        """Điền job.score / reasons / years_required. Trả về False nếu job yêu cầu quá nhiều kinh nghiệm."""
        desc = plain(job.description)
        text = f"{job.title} {desc}"
        score, reasons = 0, []

        matched = [(label, pts) for label, pat, pts in self.strengths if pat.search(text)]
        if matched:
            score += sum(pts for _, pts in matched)
            reasons.append(", ".join(label for label, _ in matched))

        # Ngành B2C: chỉ xét tiêu đề + tên công ty, vì JD B2B hay nhắc tên ngành của khách hàng
        bad = [(label, pts) for label, pat, pts in self.avoid if pat.search(f"{job.title} {job.company}")]
        if bad:
            score += sum(pts for _, pts in bad)
            reasons.append("B2C: " + ", ".join(label for label, _ in bad))

        req = extract_years(desc)
        if req:
            lo, hi = req
            job.years_required = _fmt_years(lo, hi)
            if lo > self.years + self.max_above:
                return False
            if lo <= self.years:
                score += 3
                reasons.append(f"KN {job.years_required}: vừa sức")
            elif lo <= self.years + 1:
                score += 1
                reasons.append(f"KN {job.years_required}: hơi cao")
            else:
                score -= 1
                reasons.append(f"KN {job.years_required}: cao")
        elif _SENIOR_TITLE.search(job.title) or _SENIOR_LEVEL.search(desc):
            score -= 1
            reasons.append("vị trí cấp cao, thường cần 5+ năm")

        if job.posted_at:
            days = ((now or datetime.now(timezone.utc)) - job.posted_at).days
            if days <= 1:
                score += 3
                reasons.append("mới đăng (≤1 ngày)")
            elif days <= 3:
                score += 2
                reasons.append(f"đăng {days} ngày trước")
            elif days <= 7:
                score += 1
                reasons.append(f"đăng {days} ngày trước")

        job.score, job.reasons = score, reasons
        return True

    def rank(self, jobs: list[Job], now: datetime | None = None) -> list[Job]:
        kept = [j for j in jobs if self.score(j, now) and j.score >= self.min_score]
        epoch = datetime.min.replace(tzinfo=timezone.utc)
        kept.sort(key=lambda j: (j.score, j.posted_at or epoch), reverse=True)
        return kept
