from . import careerviet, google_jobs, himalayas, jobspy_sites, remoteok, remotive, topcv, vietnamworks, weworkremotely

# Tên nguồn trong config.yaml -> hàm fetch(config, session) trả về list[Job]
SOURCES = {
    "remotive": remotive.fetch,
    "remoteok": remoteok.fetch,
    "weworkremotely": weworkremotely.fetch,
    "himalayas": himalayas.fetch,
    "vietnamworks": vietnamworks.fetch,
    "topcv": topcv.fetch,
    "careerviet": careerviet.fetch,
    "linkedin": jobspy_sites.fetch_linkedin,
    "indeed": jobspy_sites.fetch_indeed,
    "google_jobs": google_jobs.fetch,
}
