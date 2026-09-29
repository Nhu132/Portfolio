import logging

from ..http import USER_AGENT
from ..models import Job
from .html import first, slugify, soup, text

log = logging.getLogger(__name__)

URL = "https://www.topcv.vn/tim-viec-lam-{slug}"


def fetch(config, http) -> list[Job]:
    # TopCV dùng Cloudflare, chặn requests thường (403): giả lập TLS fingerprint của Chrome
    import tls_client

    browser = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    jobs = []
    for term in config["search_terms"]:
        resp = browser.get(URL.format(slug=slugify(term)), params={"type_keyword": 1, "sba": 1},
                           headers=headers, timeout_seconds=30)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} cho '{term}'")
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
