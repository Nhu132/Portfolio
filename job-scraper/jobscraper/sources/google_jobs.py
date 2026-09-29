"""Google Jobs qua SerpAPI (gói free ~100 lượt/tháng). Google Jobs gom tin từ LinkedIn,
Indeed, TopCV, trang careers của công ty..."""
import logging
import os

from ..dates import parse_date
from ..models import Job

log = logging.getLogger(__name__)

URL = "https://serpapi.com/search.json"

# Mỗi ngày 2 lượt tìm để nằm trong gói free (2 x 30 = 60 lượt/tháng).
QUERIES = [
    ("content lead OR head of content OR content marketing lead", "Ho Chi Minh City, Vietnam"),
    ("marketing lead OR head of marketing B2B", "Ho Chi Minh City, Vietnam"),
]


def fetch(config, http) -> list[Job]:
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        log.info("Google Jobs: chưa có SERPAPI_KEY, bỏ qua")
        return []
    jobs = []
    for query, location in QUERIES:
        params = {"engine": "google_jobs", "q": query, "location": location, "hl": "en", "api_key": key}
        data = http.get(URL, params=params, timeout=60).json()
        if "error" in data:
            log.warning("Google Jobs: %s", data["error"])
            continue
        for j in data.get("jobs_results", []):
            ext = j.get("detected_extensions") or {}
            apply = j.get("apply_options") or [{}]
            jobs.append(Job(
                source=f"Google Jobs ({j.get('via', '').removeprefix('via ')})".replace(" ()", ""),
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                url=apply[0].get("link") or j.get("share_link", ""),
                location=j.get("location", ""),
                remote=bool(ext.get("work_from_home")),
                salary=ext.get("salary", ""),
                posted_at=parse_date(ext.get("posted_at")),
                description=j.get("description", ""),
            ))
    return jobs
