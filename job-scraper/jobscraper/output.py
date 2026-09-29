import csv
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from .models import Job

log = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))

HEADER = [
    "ID", "Ngày tìm thấy", "Điểm phù hợp", "Vị trí", "Công ty", "Địa điểm", "Remote", "Lương",
    "Ngày đăng", "KN yêu cầu", "Vì sao phù hợp", "Nguồn", "Link", "Trạng thái", "Ghi chú",
]
LAST_COL = chr(ord("A") + len(HEADER) - 1)


def to_row(job: Job, today: str) -> list:
    posted = job.posted_at.astimezone(VN_TZ).strftime("%Y-%m-%d") if job.posted_at else ""
    return [
        job.key, today, job.score, job.title, job.company, job.location,
        "Có" if job.remote else "", job.salary, posted, job.years_required, " · ".join(job.reasons),
        job.source, job.url, "Mới", "",
    ]


def today_vn() -> str:
    return datetime.now(VN_TZ).strftime("%Y-%m-%d")


def write_csv(jobs: list[Job], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    today = today_vn()
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig để Excel đọc đúng tiếng Việt
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(to_row(j, today) for j in jobs)


def write_sheet(jobs: list[Job], sheet_id: str, worksheet: str, credentials_json: str) -> list[Job]:
    """Thêm job chưa có trong Sheet lên đầu bảng. Trả về danh sách job mới."""
    import gspread

    client = gspread.service_account_from_dict(json.loads(credentials_json))
    book = client.open_by_key(sheet_id)
    try:
        ws = book.worksheet(worksheet)
    except gspread.WorksheetNotFound:
        ws = book.add_worksheet(worksheet, rows=1000, cols=len(HEADER))

    if ws.row_values(1) != HEADER:
        if ws.row_values(1):
            raise RuntimeError(
                f"Dòng 1 của tab '{worksheet}' không phải header của tool. "
                "Hãy dùng tab trống hoặc đổi tên tab trong config.yaml."
            )
        ws.update([HEADER], "A1")
        ws.freeze(rows=1)
        ws.format(f"A1:{LAST_COL}1", {"textFormat": {"bold": True}})

    existing = set(ws.col_values(1)[1:])
    new = [j for j in jobs if j.key not in existing]
    if new:
        today = today_vn()
        ws.insert_rows([to_row(j, today) for j in new], row=2, value_input_option="USER_ENTERED")
    log.info("Google Sheet: thêm %d job mới (%d job đã có sẵn)", len(new), len(jobs) - len(new))
    return new
