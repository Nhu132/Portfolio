import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from jobscraper.dates import parse_date
from jobscraper.filters import JobFilter
from jobscraper.models import Job
from jobscraper.output import HEADER, to_row
from jobscraper.sources import careerviet, google_jobs, remoteok, remotive, topcv, vietnamworks, weworkremotely

CONFIG = yaml.safe_load((Path(__file__).parent.parent / "config.yaml").read_text(encoding="utf-8"))
NOW = datetime.now(timezone.utc)


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body

    @property
    def text(self):
        return self.body

    @property
    def content(self):
        return self.body.encode()

    def raise_for_status(self):
        pass


class FakeHttp:
    def __init__(self, body):
        self.body = body
        self.calls = []

    def get(self, url, **kw):
        self.calls.append((url, kw))
        return FakeResponse(self.body)

    post = get


def job(title, location="Hồ Chí Minh", remote=False, company="KVY", **kw):
    return Job(source="t", title=title, company=company, url="https://x/" + title, location=location, remote=remote, **kw)


# --- Bộ lọc ---------------------------------------------------------------

def test_title_filter():
    f = JobFilter(CONFIG)
    keep = ["B2B Content Lead", "Head of Content", "Content Marketing Lead", "Marketing Lead (SaaS)",
            "Trưởng nhóm Content", "Trưởng phòng Marketing", "Content Team Leader", "Lead, Content Marketing"]
    drop = ["Content Writer", "Marketing Intern", "Junior Content Lead", "Sales Executive", "Thực tập sinh Marketing",
            "Trade Marketing Lead", "SEO/ Performance Marketing Team Lead", "BW Influencer Marketing Lead",
            "[Ha Noi] Education Content Manager", "Trưởng phòng Marketing tại Hà Nội"]
    assert all(f.title_ok(job(t)) for t in keep)
    assert not any(f.title_ok(job(t)) for t in drop)


def test_location_filter():
    f = JobFilter(CONFIG)
    assert f.location_ok(job("x", "Hồ Chí Minh"))
    assert f.location_ok(job("x", "Ho Chi Minh City, Vietnam"))
    assert f.location_ok(job("x", "Hà Nội, Hồ Chí Minh"))
    assert not f.location_ok(job("x", "Hà Nội"))
    assert not f.location_ok(job("x", "Hanoi, Vietnam"))
    assert f.location_ok(job("x", "Remote"))
    assert f.location_ok(job("x", "Remote - Vietnam"))
    assert not f.location_ok(job("x", "Remote, US"))
    assert f.location_ok(job("x", "", remote=True))
    assert f.location_ok(job("x", "Worldwide", remote=True))
    assert f.location_ok(job("x", "APAC", remote=True))
    assert not f.location_ok(job("x", "USA Only", remote=True))


def test_apply_dedupes_filters_and_sorts():
    f = JobFilter(CONFIG)
    jobs = [
        job("Content Lead", company="A", posted_at=NOW - timedelta(days=1)),
        job("Content Lead", company="A "),  # trùng với job trên
        job("Marketing Lead", company="B", description="B2B SaaS company", posted_at=NOW - timedelta(days=3)),
        job("Head of Content", company="C", posted_at=NOW - timedelta(days=60)),  # quá cũ
        job("Content Writer", company="D"),
    ]
    kept = f.apply(jobs)
    assert [j.company for j in kept] == ["B", "A"]
    assert kept[0].b2b_signals == ["b2b", "saas"]


def test_dedupe_key_ignores_accents_and_case():
    assert job("Trưởng nhóm Content", company="Công ty ABC").key == job("truong nhom content", company="CONG TY ABC").key


def test_parse_date():
    assert parse_date("2026-09-20T10:00:00Z").day == 20
    assert parse_date("Mon, 21 Sep 2026 10:00:00 +0000").day == 21
    assert parse_date("22/09/2026").month == 9
    assert parse_date(1790000000).year == 2026
    assert round((NOW - parse_date("3 days ago")).total_seconds() / 86400) == 3
    assert round((NOW - parse_date("2 ngày trước")).total_seconds() / 86400) == 2
    assert parse_date("không rõ") is None


def test_row_matches_header():
    assert len(to_row(job("Content Lead"), "2026-09-29")) == len(HEADER)


# --- Các nguồn ------------------------------------------------------------

def test_remotive():
    body = {"jobs": [{"title": "Content Lead", "company_name": "Acme", "url": "https://remotive.com/1",
                      "candidate_required_location": "Worldwide", "publication_date": "2026-09-25T00:00:00"}]}
    [j] = remotive.fetch(CONFIG, FakeHttp(body))
    assert (j.title, j.company, j.remote, j.location) == ("Content Lead", "Acme", True, "Worldwide")


def test_remoteok_skips_legal_notice():
    body = [{"legal": "notice"}, {"position": "Head of Content", "company": "Acme", "url": "https://remoteok.com/1",
                                  "salary_min": 80000, "salary_max": 100000, "date": "2026-09-25T00:00:00+00:00"}]
    [j] = remoteok.fetch(CONFIG, FakeHttp(body))
    assert j.salary == "$80,000–$100,000"


def test_weworkremotely():
    rss = """<rss><channel><item><title>Acme Inc: Content Marketing Lead</title>
    <link>https://weworkremotely.com/1</link><region>Anywhere in the World</region>
    <pubDate>Mon, 21 Sep 2026 10:00:00 +0000</pubDate></item></channel></rss>"""
    [j] = weworkremotely.fetch(CONFIG, FakeHttp(rss))
    assert (j.company, j.title) == ("Acme Inc", "Content Marketing Lead")


def test_vietnamworks():
    body = {"data": [{"jobTitle": "Content Lead", "companyName": "KVY", "jobUrl": "https://www.vietnamworks.com/a-1-jv",
                      "workingLocations": [{"cityNameVI": "Hồ Chí Minh"}], "prettySalary": "Thương lượng"}]}
    http = FakeHttp(body)
    jobs = vietnamworks.fetch(CONFIG, http)
    assert jobs[0].location == "Hồ Chí Minh"
    assert len(http.calls) == len(CONFIG["search_terms"])


def test_topcv_parse():
    html = """<div class="job-item-search-result"><h3 class="title"><a href="https://www.topcv.vn/viec-lam/content-lead/1.html?ta_source=x">
    <span>Content Lead (B2B)</span></a></h3><a class="company"><span class="company-name">Công ty ABC</span></a>
    <label class="address"><span class="city-text">Hồ Chí Minh</span></label><label class="salary">20 - 30 triệu</label></div>"""
    [j] = topcv.parse(html)
    assert (j.title, j.company, j.location, j.salary) == ("Content Lead (B2B)", "Công ty ABC", "Hồ Chí Minh", "20 - 30 triệu")
    assert j.url == "https://www.topcv.vn/viec-lam/content-lead/1.html"


def test_careerviet_parse():
    html = """<div class="job-item"><div class="title"><h2><a class="job_link" href="https://careerviet.vn/vi/1.html"
    title="Marketing Lead">Marketing Lead</a></h2></div><a class="company-name">XYZ</a>
    <div class="location"><ul><li>Hồ Chí Minh</li><li>Hà Nội</li></ul></div><div class="salary"><p>Cạnh tranh</p></div>
    <time>25/09/2026</time></div>"""
    [j] = careerviet.parse(html)
    assert (j.title, j.location, j.posted_at.day) == ("Marketing Lead", "Hồ Chí Minh, Hà Nội", 25)


def test_google_jobs_skips_without_key(monkeypatch):
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    assert google_jobs.fetch(CONFIG, FakeHttp({})) == []


def test_google_jobs(monkeypatch):
    monkeypatch.setenv("SERPAPI_KEY", "k")
    body = {"jobs_results": [{"title": "Head of Content", "company_name": "Acme", "location": "Ho Chi Minh City",
                              "via": "via LinkedIn", "apply_options": [{"link": "https://linkedin.com/1"}],
                              "detected_extensions": {"posted_at": "2 days ago"}}]}
    jobs = google_jobs.fetch(CONFIG, FakeHttp(body))
    assert jobs[0].source == "Google Jobs (LinkedIn)"
    assert jobs[0].url == "https://linkedin.com/1"
