from ..dates import parse_date
from ..models import Job

URL = "https://ms.vietnamworks.com/job-search/v1.0/search"


def fetch(config, http) -> list[Job]:
    jobs = []
    for term in config["search_terms"]:
        payload = {
            "userId": 0,
            "query": term,
            "filter": [],
            "ranges": [],
            "order": [],
            "hitsPerPage": 50,
            "page": 0,
        }
        headers = {"Origin": "https://www.vietnamworks.com", "Referer": "https://www.vietnamworks.com/"}
        data = http.post(URL, json=payload, headers=headers, timeout=30).json()
        for j in data.get("data", []):
            places = j.get("workingLocations") or []
            location = ", ".join(
                p.get("cityNameVI") or p.get("cityName") or p.get("address") or "" for p in places
            )
            url = j.get("jobUrl") or f"https://www.vietnamworks.com/{j.get('alias', '')}-{j.get('jobId')}-jv"
            jobs.append(Job(
                source="VietnamWorks",
                title=j.get("jobTitle", ""),
                company=j.get("companyName", ""),
                url=url,
                location=location,
                salary=j.get("prettySalary", "") or "",
                posted_at=parse_date(j.get("approvedOn") or j.get("createdOn")),
                description=_description(j),
            ))
    return jobs


def _description(j: dict) -> str:
    parts = [j.get("jobDescription") or "", j.get("jobRequirement") or ""]
    years = j.get("yearsOfExperience")
    if isinstance(years, int) and years > 0:
        parts.append(f"Yêu cầu {years} năm kinh nghiệm")
    return " ".join(parts)
