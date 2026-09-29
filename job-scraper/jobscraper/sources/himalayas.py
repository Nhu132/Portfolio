from ..dates import parse_date
from ..models import Job

URL = "https://himalayas.app/jobs/api/search"


def fetch(config, http) -> list[Job]:
    jobs = []
    for term in config["search_terms"]:
        data = http.get(URL, params={"q": term}, timeout=30).json()
        for j in data.get("jobs", []):
            lo, hi = j.get("minSalary"), j.get("maxSalary")
            cur = j.get("currency") or ""
            jobs.append(Job(
                source="Himalayas",
                title=j.get("title", ""),
                company=j.get("companyName", ""),
                url=j.get("applicationLink") or j.get("guid", ""),
                location=", ".join(j.get("locationRestrictions") or []),
                remote=True,
                salary=f"{lo:,}–{hi:,} {cur}".strip() if lo and hi else "",
                posted_at=parse_date(j.get("pubDate")),
                description=(j.get("excerpt") or "") + " " + " ".join(j.get("categories") or []),
            ))
    return jobs
