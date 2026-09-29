import re
from datetime import datetime, timedelta, timezone

from .models import Job

REMOTE_WORDS = re.compile(r"remote|từ\s+xa|work\s+from\s+home|wfh", re.I)


def _any(patterns: list[str]) -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.I)


class JobFilter:
    def __init__(self, config: dict):
        self.include = _any(config["title_include"])
        self.exclude = _any(config["title_exclude"])
        self.locations = _any(config["locations"])
        self.remote_regions = _any(config["remote_regions"])
        self.b2b = _any(config["b2b_signals"])
        self.max_age = timedelta(days=config.get("max_age_days", 14))

    def title_ok(self, job: Job) -> bool:
        return bool(self.include.search(job.title)) and not self.exclude.search(job.title)

    def location_ok(self, job: Job) -> bool:
        loc = job.location.strip()
        if job.remote or REMOTE_WORDS.search(loc) or REMOTE_WORDS.search(job.title):
            job.remote = True
            # Job remote: giữ nếu không giới hạn khu vực, hoặc khu vực phù hợp múi giờ VN
            region = REMOTE_WORDS.sub("", loc).strip(" ,-–()/")
            return not region or bool(self.remote_regions.search(region) or self.locations.search(region))
        # Trang VN đôi khi không ghi địa điểm: giữ lại để tự xem
        return not loc or bool(self.locations.search(loc))

    def fresh(self, job: Job, now: datetime | None = None) -> bool:
        if not job.posted_at:
            return True
        return (now or datetime.now(timezone.utc)) - job.posted_at <= self.max_age

    def tag_b2b(self, job: Job) -> None:
        found = {m.group(0).lower() for m in self.b2b.finditer(f"{job.title} {job.description}")}
        job.b2b_signals = sorted(found)

    def apply(self, jobs: list[Job]) -> list[Job]:
        kept, seen = [], set()
        for job in jobs:
            if not (job.title and job.url) or job.key in seen:
                continue
            if self.title_ok(job) and self.location_ok(job) and self.fresh(job):
                seen.add(job.key)
                self.tag_b2b(job)
                kept.append(job)
        # Job có tín hiệu B2B lên trước, rồi tới job mới đăng
        epoch = datetime.min.replace(tzinfo=timezone.utc)
        kept.sort(key=lambda j: (bool(j.b2b_signals), j.posted_at or epoch), reverse=True)
        return kept
