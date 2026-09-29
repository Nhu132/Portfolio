import xml.etree.ElementTree as ET

from ..dates import parse_date
from ..models import Job

URL = "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss"


def fetch(config, http) -> list[Job]:
    root = ET.fromstring(http.get(URL, timeout=30).content)
    jobs = []
    for item in root.iter("item"):
        raw_title = item.findtext("title", "")
        # Tiêu đề RSS có dạng "Tên công ty: Vị trí"
        company, _, title = raw_title.partition(":")
        if not title:
            company, title = "", raw_title
        jobs.append(Job(
            source="We Work Remotely",
            title=title.strip(),
            company=company.strip(),
            url=item.findtext("link", ""),
            location=item.findtext("region", ""),
            remote=True,
            posted_at=parse_date(item.findtext("pubDate")),
            description=item.findtext("description", ""),
        ))
    return jobs
