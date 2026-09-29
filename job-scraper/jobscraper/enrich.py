"""Lấy mô tả chi tiết cho job còn thiếu JD (LinkedIn, CareerViet...) để đọc yêu cầu kinh nghiệm.

Chỉ chạy trên các job đã qua bộ lọc tiêu đề/địa điểm nên số request nhỏ."""
import logging
import re
import time

from .models import Job
from .sources.html import plain, soup

log = logging.getLogger(__name__)

MIN_DESCRIPTION = 300  # JD ngắn hơn thế này thì coi như chưa có
MAX_FETCH = 60

_LINKEDIN_ID = re.compile(r"linkedin\.com/jobs/view/(?:[^/?]*-)?(\d{6,})")
_LINKEDIN_API = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{id}"
# Vùng nội dung chính, thử lần lượt; không khớp thì lấy cả trang
_MAIN = [
    ".show-more-less-html__markup", ".description__text",  # LinkedIn
    ".job-detail-content", ".detail-row", ".job-description", "#tab-1", "article", "main",
]


def enrich(jobs: list[Job], http) -> None:
    fetched = 0
    for job in jobs:
        if fetched >= MAX_FETCH:
            break
        if len(plain(job.description)) >= MIN_DESCRIPTION:
            continue
        url = detail_url(job)
        if not url:
            continue
        fetched += 1
        try:
            resp = http.get(url, timeout=20)
            if resp.status_code == 200:
                job.description = f"{job.description} {page_text(resp.text)}"
        except Exception as exc:
            log.info("Không lấy được JD %s: %s", url, exc)
        time.sleep(1)  # nhẹ tay để không bị LinkedIn giới hạn
    log.info("Đã lấy JD chi tiết cho %d job", fetched)


def detail_url(job: Job) -> str:
    m = _LINKEDIN_ID.search(job.url)
    if m:
        return _LINKEDIN_API.format(id=m.group(1))
    if "topcv.vn" in job.url:  # Cloudflare chặn
        return ""
    return job.url


def page_text(html: str) -> str:
    doc = soup(html)
    for tag in doc(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    parts = []
    for sel in _MAIN:
        for node in doc.select(sel):
            parts.append(node.get_text(" "))
        if sum(map(len, parts)) >= MIN_DESCRIPTION:
            break
    # LinkedIn: "Seniority level: Mid-Senior level / Director..."
    parts += [n.get_text(" ") for n in doc.select(".description__job-criteria-item")]
    text = " ".join(parts) if sum(map(len, parts)) >= MIN_DESCRIPTION else doc.get_text(" ")
    return " ".join(text.split())[:20000]
