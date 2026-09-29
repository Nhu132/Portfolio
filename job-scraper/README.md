# Job scraper: B2B Content Lead / Marketing Lead

Mỗi sáng lúc 8:07 (giờ VN), GitHub Actions tự cào jobs **Content Lead / Head of Content / Marketing Lead** ở **TP.HCM hoặc Remote**, lọc bỏ tin trùng rồi thêm job mới lên đầu Google Sheet.

| Nguồn | Cách lấy | Ghi chú |
|---|---|---|
| Remotive, RemoteOK, We Work Remotely, Himalayas | API / RSS công khai | Job remote quốc tế, chỉ giữ tin tuyển Worldwide/APAC/Asia/Vietnam hoặc không giới hạn khu vực |
| VietnamWorks | API tìm kiếm của trang | |
| TopCV, CareerViet | Đọc HTML | Có thể bị chặn hoặc hỏng khi trang đổi giao diện |
| LinkedIn, Indeed | Thư viện [JobSpy](https://github.com/speedyapply/JobSpy) | Hai trang này chống bot; thỉnh thoảng sẽ bị giới hạn |
| Google Jobs | [SerpAPI](https://serpapi.com) (gói free) | Chỉ chạy khi có `SERPAPI_KEY` |

Mỗi nguồn chạy độc lập: nguồn nào lỗi thì bỏ qua và ghi vào bảng tóm tắt, các nguồn khác vẫn chạy.

## Google Sheet

| ID | Ngày tìm thấy | Nguồn | Vị trí | Công ty | Địa điểm | Remote | Lương | Ngày đăng | Tín hiệu B2B | Link | Trạng thái | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

- Job có từ khoá B2B/SaaS/software/outsourcing… được ghi ở cột **Tín hiệu B2B** và xếp lên trên.
- Cùng vị trí + công ty xuất hiện ở nhiều nguồn chỉ ghi **một lần**. Job đã có trong Sheet sẽ không bị thêm lại, nên cột **Trạng thái / Ghi chú** bạn tự sửa (đã apply, phỏng vấn…) được giữ nguyên.

## Cài đặt (làm một lần, khoảng 15 phút)

### 1. Tạo service account Google
1. Vào <https://console.cloud.google.com>, tạo project mới (vd: `job-scraper`).
2. **APIs & Services → Library**, bật **Google Sheets API**.
3. **APIs & Services → Credentials → Create credentials → Service account**, đặt tên rồi bấm Done.
4. Mở service account vừa tạo → tab **Keys → Add key → Create new key → JSON**. File JSON sẽ được tải về.

### 2. Tạo Google Sheet
1. Tạo một Google Sheet mới.
2. Bấm **Share**, dán email của service account (dạng `...@....iam.gserviceaccount.com`, có trong file JSON ở trường `client_email`), cấp quyền **Editor**.
3. Copy **Sheet ID** từ URL: `https://docs.google.com/spreadsheets/d/`**`<SHEET_ID>`**`/edit`

Tool tự tạo tab `Jobs` và dòng tiêu đề ở lần chạy đầu tiên.

### 3. (Tuỳ chọn) SerpAPI cho Google Jobs
Đăng ký miễn phí tại <https://serpapi.com>, lấy API key. Tool dùng khoảng 60 lượt/tháng.

### 4. Thêm secrets vào GitHub
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Tên | Giá trị |
|---|---|
| `GOOGLE_SHEET_ID` | Sheet ID ở bước 2 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Toàn bộ nội dung file JSON ở bước 1 |
| `SERPAPI_KEY` | (tuỳ chọn) key SerpAPI |

### 5. Chạy thử
Tab **Actions → Job scraper → Run workflow**. Khi chạy xong, mở lượt chạy để xem bảng tóm tắt (số tin từng nguồn, job mới). File CSV nằm trong mục **Artifacts**.

> Lịch chạy tự động chỉ hoạt động khi file workflow đã nằm trên nhánh mặc định (`main`) của repo.

## Tuỳ chỉnh

Sửa `config.yaml`:
- `search_terms`: từ khoá tìm kiếm.
- `title_include` / `title_exclude`: lọc theo tiêu đề (regex).
- `locations`, `remote_regions`: lọc địa điểm.
- `b2b_signals`: từ khoá đánh dấu B2B.
- `sources`: bật/tắt từng nguồn.

## Chạy trên máy

```bash
cd job-scraper
pip install -r requirements.txt
python -m pytest -q
python -m jobscraper.main --dry-run                     # chỉ ghi CSV vào output/
python -m jobscraper.main --dry-run --only topcv remotive
```
