from ..dates import parse_date
from ..models import Job

# Remotive giới hạn khoảng 4 request/ngày: gọi 1 lần cho cả nhóm Marketing rồi lọc tiêu đề sau.
URL = "https://remotive.com/api/remote-jobs"


def fetch(config, http) -> list[Job]:
    data = http.get(URL, params={"category": "marketing"}, timeout=30).json()
    return [
        Job(
            source="Remotive",
            title=j.get("title", ""),
            company=j.get("company_name", ""),
            url=j.get("url", ""),
            location=j.get("candidate_required_location", ""),
            remote=True,
            salary=j.get("salary", "") or "",
            posted_at=parse_date(j.get("publication_date")),
            description=j.get("description", ""),
        )
        for j in data.get("jobs", [])
    ]
