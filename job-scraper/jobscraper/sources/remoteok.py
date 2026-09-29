from ..dates import parse_date
from ..models import Job

URL = "https://remoteok.com/api"


def fetch(config, http) -> list[Job]:
    data = http.get(URL, params={"tag": "marketing"}, timeout=30).json()
    jobs = []
    for j in data:
        if "position" not in j:  # phần tử đầu là thông báo pháp lý của RemoteOK
            continue
        lo, hi = j.get("salary_min"), j.get("salary_max")
        jobs.append(Job(
            source="RemoteOK",
            title=j.get("position", ""),
            company=j.get("company", ""),
            url=j.get("url", ""),
            location=j.get("location", ""),
            remote=True,
            salary=f"${lo:,}–${hi:,}" if lo and hi else "",
            posted_at=parse_date(j.get("date") or j.get("epoch")),
            description=" ".join(j.get("tags") or []) + " " + (j.get("description") or ""),
        ))
    return jobs
