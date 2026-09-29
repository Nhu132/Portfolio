"""LinkedIn và Indeed qua thư viện JobSpy (github.com/speedyapply/JobSpy)."""
import logging
import math

from ..dates import parse_date
from ..models import Job

log = logging.getLogger(__name__)

# (địa điểm, có phải tìm job remote không)
SEARCHES = [("Ho Chi Minh City, Vietnam", False), ("Vietnam", True)]


def fetch_linkedin(config, http) -> list[Job]:
    return _fetch("linkedin", "LinkedIn", config)


def fetch_indeed(config, http) -> list[Job]:
    return _fetch("indeed", "Indeed", config)


def _fetch(site: str, label: str, config) -> list[Job]:
    from jobspy import scrape_jobs  # import muộn: thư viện nặng, chỉ tải khi nguồn được bật

    jobs = []
    for term in config["search_terms"]:
        for location, remote in SEARCHES:
            try:
                df = scrape_jobs(
                    site_name=[site],
                    search_term=term,
                    location=location,
                    is_remote=remote,
                    results_wanted=25,
                    hours_old=config.get("max_age_days", 14) * 24,
                    country_indeed="vietnam",
                    linkedin_fetch_description=False,
                )
            except Exception as exc:  # JobSpy hay lỗi khi bị rate limit; bỏ qua lượt này
                log.warning("%s: lỗi khi tìm '%s' @ %s: %s", label, term, location, exc)
                continue
            for row in df.to_dict("records"):
                # Lượt tìm "Vietnam + remote" trả cả job onsite ở tỉnh khác: chỉ giữ job thực sự remote
                if remote and not _flag(row.get("is_remote")):
                    continue
                jobs.append(Job(
                    source=label,
                    title=_s(row.get("title")),
                    company=_s(row.get("company")),
                    url=_s(row.get("job_url")),
                    location=_s(row.get("location")),
                    remote=_flag(row.get("is_remote")),
                    salary=_salary(row),
                    posted_at=parse_date(_s(row.get("date_posted"))),
                    description=_s(row.get("description")),
                ))
    return jobs


def _flag(value) -> bool:
    return value is not None and value == True  # noqa: E712 (NaN của pandas phải tính là False)


def _s(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value)


def _salary(row) -> str:
    lo, hi = row.get("min_amount"), row.get("max_amount")
    if not _s(lo) or not _s(hi):
        return ""
    return f"{lo:,.0f}–{hi:,.0f} {_s(row.get('currency'))}/{_s(row.get('interval'))}".strip("/ ")
