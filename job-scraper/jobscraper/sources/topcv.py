import logging

from ..models import Job
from .html import first, slugify, soup, text

log = logging.getLogger(__name__)

URL = "https://www.topcv.vn/tim-viec-lam-{slug}"


def fetch(config, http) -> list[Job]:
    jobs = []
    for term in config["search_terms"]:
        resp = http.get(URL.format(slug=slugify(term)), params={"type_keyword": 1, "sba": 1}, timeout=30)
        resp.raise_for_status()
        found = parse(resp.text)
        if not found:
            log.warning("TopCV: không đọc được job nào cho '%s' (có thể bị chặn hoặc đổi giao diện)", term)
        jobs.extend(found)
    return jobs


def parse(html: str) -> list[Job]:
    jobs = []
    for card in soup(html).select(".job-item-search-result, .job-item-2, .job-list-search-result .job-item"):
        link = first(card, ["h3.title a", ".title a", "a[href*='/viec-lam/']"])
        if not link:
            continue
        jobs.append(Job(
            source="TopCV",
            title=text(card, ["h3.title a span", "h3.title a", ".title a"]),
            company=text(card, [".company-name", "a.company span", "a.company", ".company"]),
            url=link.get("href", "").split("?")[0],
            location=text(card, [".city-text", ".address", ".label-address"]),
            salary=text(card, [".salary", ".title-salary", ".label-salary"]),
        ))
    return jobs
