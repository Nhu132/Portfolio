import argparse
import logging
import os
from pathlib import Path

import yaml

from . import output
from .filters import JobFilter
from .http import session
from .sources import SOURCES

log = logging.getLogger("jobscraper")

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Cào jobs Content Lead / Marketing Lead")
    parser.add_argument("--config", default=ROOT / "config.yaml")
    parser.add_argument("--csv", default=ROOT / "output" / f"jobs-{output.today_vn()}.csv")
    parser.add_argument("--only", nargs="*", help="chỉ chạy các nguồn này, vd: --only remotive topcv")
    parser.add_argument("--dry-run", action="store_true", help="không ghi vào Google Sheet")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    http = session()
    collected, stats = [], {}
    for name, fetch in SOURCES.items():
        if not config["sources"].get(name) or (args.only and name not in args.only):
            continue
        try:
            jobs = fetch(config, http)
            stats[name] = f"{len(jobs)} tin"
            collected.extend(jobs)
        except Exception as exc:  # một nguồn lỗi không làm hỏng cả lượt chạy
            log.exception("Nguồn %s lỗi", name)
            stats[name] = f"LỖI: {type(exc).__name__}: {exc}"[:200]
        log.info("%s: %s", name, stats[name])

    jobs = JobFilter(config).apply(collected)
    log.info("Sau khi lọc: %d / %d job", len(jobs), len(collected))
    output.write_csv(jobs, str(args.csv))
    log.info("Đã ghi %s", args.csv)

    new = jobs
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if args.dry_run:
        log.info("Dry run: không ghi Google Sheet")
    elif sheet_id and creds:
        new = output.write_sheet(jobs, sheet_id, config["sheet"]["worksheet"], creds)
    else:
        log.warning("Chưa có GOOGLE_SHEET_ID / GOOGLE_SERVICE_ACCOUNT_JSON: chỉ ghi CSV")

    _summary(stats, len(collected), jobs, new)


def _summary(stats: dict, total: int, jobs: list, new: list) -> None:
    """Tóm tắt hiện ở trang kết quả GitHub Actions."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = ["## Kết quả cào jobs", "", "| Nguồn | Kết quả |", "|---|---|"]
    lines += [f"| {k} | {v.replace('|', '/')} |" for k, v in stats.items()]
    lines += ["", f"**{total}** tin thô → **{len(jobs)}** job phù hợp → **{len(new)}** job mới", ""]
    if new:
        lines += ["| Vị trí | Công ty | Nguồn | B2B |", "|---|---|---|---|"]
        lines += [
            f"| [{j.title}]({j.url}) | {j.company} | {j.source} | {', '.join(j.b2b_signals)} |"
            for j in new[:50]
        ]
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
