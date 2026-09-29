import logging

from ..dates import parse_date
from ..models import Job
from .html import all_text, first, slugify, soup, text

log = logging.getLogger(__name__)

URL = "https://careerviet.vn/viec-lam/{slug}-k-vi.html"


def fetch(config, http) -> list[Job]:
    jobs = []
    for term in config["search_terms"]:
        resp = http.get(URL.format(slug=slugify(term)), timeout=30)
        resp.raise_for_status()
        found = parse(resp.text)
        if not found:
            log.warning("CareerViet: không đọc được job nào cho '%s' (có thể bị chặn hoặc đổi giao diện)", term)
        jobs.extend(found)
    return jobs


def parse(html: str) -> list[Job]:
    jobs = []
    for card in soup(html).select(".job-item"):
        link = first(card, ["a.job_link", ".title a", "h2 a"])
        if not link:
            continue
        jobs.append(Job(
            source="CareerViet",
            title=text(card, ["a.job_link", ".title a", "h2 a"]),
            company=text(card, ["a.company-name", ".company-name", ".caption .company"]),
            url=link.get("href", ""),
            location=all_text(card, ".location li") or text(card, [".location"]),
            salary=text(card, [".salary p", ".salary"]),
            posted_at=parse_date(text(card, ["time", ".time"])),
        ))
    return jobs
