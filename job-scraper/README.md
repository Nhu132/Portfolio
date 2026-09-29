# Job scraper: B2B Content Lead / Marketing Lead

Mỗi ngày 2 lần (8:07 và 14:07 giờ VN), GitHub Actions tự cào jobs **Content Lead / Head of Content / Marketing Lead** ở **TP.HCM hoặc Remote** đăng trong 7 ngày gần nhất, chấm điểm độ phù hợp với hồ sơ của bạn, ẩn job quá tầm kinh nghiệm, rồi thêm job mới lên đầu Google Sheet (job điểm cao nhất nằm trên cùng).

| Nguồn | Cách lấy | Ghi chú |
|---|---|---|
| Remotive, RemoteOK, We Work Remotely, Himalayas | API / RSS công khai | Job remote quốc tế, chỉ giữ tin tuyển Worldwide/APAC/Asia/Vietnam hoặc không giới hạn khu vực |
| VietnamWorks | API tìm kiếm của trang | |
| CareerViet | Đọc HTML | Có thể hỏng khi trang đổi giao diện |
| TopCV | Đọc HTML | **Tắt mặc định**: Cloudflare chặn IP của GitHub Actions. Tin TopCV vẫn xuất hiện qua Google Jobs |
| LinkedIn, Indeed | Thư viện [JobSpy](https://github.com/speedyapply/JobSpy) | Hai trang này chống bot; thỉnh thoảng sẽ bị giới hạn |
| Google Jobs | [SerpAPI](https://serpapi.com) (gói free) | Chỉ chạy khi có `SERPAPI_KEY` |

Mỗi nguồn chạy độc lập: nguồn nào lỗi thì bỏ qua và ghi vào bảng tóm tắt, các nguồn khác vẫn chạy.

## Google Sheet

| ID | Ngày tìm thấy | Điểm phù hợp | Vị trí | Công ty | Địa điểm | Remote | Lương | Ngày đăng | KN yêu cầu | Vì sao phù hợp | Nguồn | Link | Trạng thái | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

- Cùng vị trí + công ty xuất hiện ở nhiều nguồn chỉ ghi **một lần**. Job đã có trong Sheet sẽ không bị thêm lại, nên cột **Trạng thái / Ghi chú** bạn tự sửa (đã apply, phỏng vấn…) được giữ nguyên.

## Cách chấm "Điểm phù hợp"

Hồ sơ nằm ở mục `profile` trong `config.yaml` (lấy từ portfolio: B2B content, tech/industrial, viết tiếng Anh, SEO, LinkedIn, HubSpot, product launch).

| Tiêu chí | Điểm |
|---|---|
| JD nhắc tới thế mạnh của bạn (B2B +3, Tech/SaaS/IT +2, Industrial +2, tiếng Anh +2, SEO/LinkedIn/HubSpot/Lead gen/Launch/Thought leadership +1 mỗi mục) | cộng dồn |
| Tiêu đề hoặc tên công ty thuộc ngành B2C (FMCG, mỹ phẩm/clinic, F&B, bất động sản, thời trang) | −3 |
| Kinh nghiệm yêu cầu ≤ số năm của bạn / hơn 1 năm / hơn 2 năm | +3 / +1 / −1 |
| Yêu cầu nhiều hơn 2 năm so với bạn | **ẩn** |
| Không ghi số năm nhưng là vị trí cấp cao (Head of, Trưởng phòng, Director) | −1 |
| Đăng ≤1 ngày / ≤3 ngày / ≤7 ngày | +3 / +2 / +1 |

Job có điểm âm bị ẩn (`min_score: 0`). Với job LinkedIn, CareerViet… không kèm JD, tool mở trang chi tiết để đọc yêu cầu kinh nghiệm.

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
- `max_age_days`: chỉ lấy tin đăng trong N ngày.
- `profile`: số năm kinh nghiệm, thế mạnh (cộng điểm), ngành muốn tránh (trừ điểm), điểm tối thiểu.
- `sources`: bật/tắt từng nguồn.

## Chạy trên máy

```bash
cd job-scraper
pip install -r requirements.txt
python -m pytest -q
python -m jobscraper.main --dry-run                     # chỉ ghi CSV vào output/
python -m jobscraper.main --dry-run --only topcv remotive
```
