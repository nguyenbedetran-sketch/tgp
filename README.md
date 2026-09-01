# Trần Gia Phát — Website doanh nghiệp

Website chính thức cho **CÔNG TY TNHH TƯ VẤN THIẾT KẾ XÂY DỰNG TRẦN GIA PHÁT**: giới thiệu công ty, dịch vụ, dự án tiêu biểu, blog kiến thức, công cụ ước tính chi phí xây dựng (tính toán thật bằng module C++), form nhận tư vấn, và trang quản trị (admin dashboard) đầy đủ chức năng CRUD.

Toàn bộ hệ thống là **mã nguồn chạy thật**, không phải bản demo tĩnh: form liên hệ ghi vào database thật, công cụ ước tính gọi một chương trình C++ đã biên dịch qua subprocess, trang quản trị xuất báo cáo CSV/JSON thông qua một service Java riêng, và đăng nhập quản trị dùng JWT thật.

---

## 1. Kiến trúc hệ thống

```
Frontend (HTML/CSS/JS thuần)
        │  fetch() → REST API (JSON)
        ▼
Python Backend (Flask) ──── phục vụ luôn frontend tĩnh (dev) ────┐
        │                                                         │
        ├── SQLite database (database/tgp.db)                    │
        ├── subprocess ──► C++ calculation engine (cpp/tgp_calculator)
        └── subprocess ──► Java report service (java/target/tgp-report-service.jar)
```

- **Frontend**: HTML5/CSS3/JavaScript thuần (không framework, không bước build), 10 trang, responsive hoàn toàn (1920 → 360px).
- **Backend**: Flask (Python), REST API `/api/*`, xác thực JWT cho khu vực quản trị, validation, xử lý lỗi tập trung, logging ra file + console.
- **C++**: module tính toán chi phí xây dựng độc lập (`cpp/`), giao tiếp với Python qua JSON trên stdin/stdout.
- **Java**: service xuất báo cáo (CSV/JSON) cho danh sách dự án và yêu cầu tư vấn (`java/`), giao tiếp với Python qua JSON trên stdin/stdout.
- **Database**: SQLite (`database/schema.sql`), không dùng dữ liệu giả lập cứng trong code — mọi nội dung hiển thị trên site đều đọc từ database qua API.

### Vì sao Flask thay vì FastAPI, vì sao sqlite3 thay vì SQLAlchemy?

Bản build này được thực hiện trong môi trường **không có quyền truy cập PyPI/Maven Central** (không cài được `fastapi`, `sqlalchemy`, `passlib`...). Đề bài cho phép "ưu tiên Flask hoặc FastAPI", nên dự án chuyển sang dùng **Flask** (đã có sẵn) làm backend chính, và một lớp truy cập dữ liệu mỏng bằng **`sqlite3`** (thư viện chuẩn của Python) thay cho SQLAlchemy. Mật khẩu được băm bằng `hashlib.pbkdf2_hmac` (chuẩn NIST/OWASP khi không có bcrypt), JWT dùng `PyJWT`.

Nếu môi trường của bạn **có** quyền truy cập PyPI, file `backend/requirements.txt` có ghi chú danh sách gói FastAPI/SQLAlchemy/passlib tương đương để bạn có thể chuyển đổi nếu muốn — kiến trúc route/service đã được tách lớp rõ ràng (`app/routes`, `app/services`, `app/models`) để việc thay thế lớp dữ liệu không ảnh hưởng đến logic nghiệp vụ.

Tương tự, `java/` có sẵn `pom.xml` chuẩn Maven; nếu môi trường của bạn không có Maven Central, dùng `java/build.sh` (chỉ cần JDK, không cần Internet).

---

## 2. Cấu trúc thư mục

```
trangia-phat/
├── frontend/                 # Website tĩnh (HTML/CSS/JS)
│   ├── index.html
│   ├── pages/                # gioi-thieu, dich-vu, du-an, du-an-chi-tiet,
│   │                         # quy-trinh, uoc-tinh-chi-phi, tin-tuc, bai-viet,
│   │                         # lien-he, admin
│   ├── css/                  # style.css (design system), admin.css
│   ├── js/                   # api.js, main.js, admin.js, constants.js, icons.js...
│   └── assets/images/        # logo + ảnh phối cảnh dự án
│
├── backend/                  # Python (Flask) REST API
│   ├── main.py                # entry point
│   ├── create_admin.py        # script tạo/reset tài khoản quản trị
│   ├── requirements.txt
│   └── app/
│       ├── config/settings.py # đọc cấu hình từ .env
│       ├── models/db.py       # lớp truy cập sqlite3 + init schema
│       ├── routes/            # 1 file blueprint / nhóm tài nguyên
│       ├── services/          # security (JWT/hash), cpp_bridge, java_bridge, seed
│       └── utils/             # validation, rate limiting, logging, slugify...
│
├── cpp/                      # Module tính chi phí xây dựng (C++17)
│   ├── calculator.h/.cpp      # logic tính toán thuần, không I/O
│   ├── main.cpp                # CLI: đọc JSON stdin, in JSON stdout
│   └── CMakeLists.txt
│
├── java/                     # Service xuất báo cáo (Java 17)
│   ├── pom.xml
│   ├── build.sh                # build thay thế không cần Maven Central
│   └── src/main/java/com/trangiaphat/report/
│
├── database/
│   └── schema.sql             # DDL đầy đủ (users, projects, services, blog_posts,
│                               # contacts, testimonials, team_members, estimates,
│                               # site_settings, page_views)
│
├── .env.example
├── .gitignore
├── Dockerfile
└── README.md                  # (file này)
```

---

## 3. Chạy dự án ở local

### 3.1. Build module C++ (bắt buộc trước khi chạy backend)

```bash
cd cpp
g++ -std=c++17 -O2 -Wall -Wextra -o tgp_calculator main.cpp calculator.cpp
# hoặc dùng CMake:
#   mkdir build && cd build && cmake .. && cmake --build .
```

Kiểm tra nhanh:
```bash
echo '{"construction_type":"biet_thu","footprint_area_m2":120,"floors":2,"foundation_type":"bang","roof_type":"thai_nhat","finish_level":"trung_binh","location":"TP.HCM"}' | ./tgp_calculator
```

### 3.2. Build service Java

```bash
cd java
mvn -q package                 # nếu có Maven + Internet
# hoặc, nếu môi trường offline:
./build.sh                     # chỉ cần javac/jar (JDK) — không cần Internet
```

### 3.3. Cài & chạy backend Python

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt      # xem ghi chú ở mục 1 nếu môi trường offline

cp ../.env.example ../.env           # rồi chỉnh sửa các giá trị thật
python3 main.py                      # chạy tại http://localhost:8000
```

Backend sẽ:
- Tự tạo `database/tgp.db` và áp dụng `database/schema.sql` nếu chưa tồn tại.
- Tự seed dữ liệu mẫu (8 dịch vụ, 1 dự án thật từ ảnh phối cảnh công ty cung cấp, 3 bài blog, placeholder đội ngũ/đánh giá) **nếu database đang trống**.
- Phục vụ luôn `frontend/` tại `/` để chạy thử nhanh (1 lệnh, 1 cổng). Production nên tách frontend ra CDN/nginx (xem mục 5).

Mở trình duyệt tại **http://localhost:8000**.

### 3.4. Tạo tài khoản quản trị

Có thể tạo tài khoản thủ công bằng script tương tác:

```bash
cd backend
python3 create_admin.py
# nhập username / email / họ tên / mật khẩu khi được hỏi
```

Ngoài ra, phiên bản này hỗ trợ bootstrap admin ở lần chạy đầu bằng các biến `ADMIN_BOOTSTRAP_USERNAME`, `ADMIN_BOOTSTRAP_EMAIL` và `ADMIN_BOOTSTRAP_PASSWORD` trong file `.env`. Mật khẩu chỉ được đọc từ môi trường, sau đó băm bằng PBKDF2-HMAC-SHA256 cùng salt ngẫu nhiên; mật khẩu dạng rõ không được ghi vào source hoặc database. Không đưa file `.env` thật lên Git hay máy chủ chia sẻ công khai.

Đăng nhập tại **http://localhost:8000/pages/admin.html**.

---

## 4. Tài liệu API

Xem chi tiết đầy đủ tại [`docs/API.md`](docs/API.md). Tóm tắt:

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| GET | `/api/health` | - | Kiểm tra service |
| GET/POST | `/api/projects` | GET công khai, POST cần admin | Danh sách / tạo dự án |
| GET/PUT/DELETE | `/api/projects/{id\|slug}` | PUT/DELETE cần admin | Chi tiết / sửa / xóa dự án |
| GET/POST | `/api/services` | GET công khai, POST cần admin | Dịch vụ |
| GET/POST | `/api/blog` | GET công khai, POST cần admin | Bài viết |
| POST | `/api/contact` | công khai (rate-limited) | Gửi yêu cầu tư vấn |
| POST | `/api/estimate` | công khai (rate-limited) | Ước tính chi phí (gọi module C++) |
| POST | `/api/auth/login` | công khai | Đăng nhập quản trị (trả JWT) |
| GET | `/api/admin/dashboard` | admin | Thống kê tổng quan |
| GET | `/api/admin/export/{projects\|contacts}` | admin | Xuất CSV/JSON (gọi service Java) |

---

## 5. Hướng dẫn deploy production

1. **Biến môi trường**: đặt `APP_ENV=production`, `APP_DEBUG=false`, và **bắt buộc** đặt `SECRET_KEY` cố định (không để backend tự sinh ngẫu nhiên mỗi lần khởi động — token sẽ mất hiệu lực khi restart).
2. **WSGI server thật** thay vì `python main.py` (dev server):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 "main:app"
   ```
3. **Reverse proxy** (nginx/Caddy) phía trước gunicorn, phục vụ `frontend/` trực tiếp qua static file serving hoặc CDN thay vì qua Flask, bật HTTPS.
4. **Database**: với lượng truy cập lớn, cân nhắc chuyển từ SQLite sang PostgreSQL — lớp `app/models/db.py` được cô lập nên chỉ cần thay file này.
5. Đặt `CORS_ORIGINS` về đúng domain thật thay vì `*`.
6. Không commit `.env` — dùng secret manager của nền tảng hosting.

### Docker

```bash
docker build -t trangia-phat .
docker run -p 8000:8000 --env-file .env trangia-phat
```

`Dockerfile` build cả module C++, service Java (qua `build.sh`, không cần Internet lúc build) và backend Python trong cùng image.

---

## 6. Bảo mật đã triển khai

- Băm mật khẩu PBKDF2-HMAC-SHA256 (260.000 vòng lặp) + salt ngẫu nhiên mỗi user.
- Xác thực JWT (HS256) cho toàn bộ route `/api/admin/*` và các thao tác ghi (POST/PUT/DELETE).
- Validation input ở mọi endpoint nhận dữ liệu từ người dùng (bắt buộc trường, định dạng SĐT/email, giới hạn độ dài chuỗi, whitelist enum).
- Chống spam: rate limiting theo IP (sliding window) cho `/api/contact` và `/api/estimate`; honeypot field ẩn trên form liên hệ.
- Upload ảnh: whitelist phần mở rộng + kiểm tra magic bytes thực tế của file (không tin filename), đổi tên file ngẫu nhiên (UUID), giới hạn dung lượng.
- Không dùng string interpolation cho SQL — toàn bộ truy vấn dùng parameterized query (`?`) qua `sqlite3`.
- CORS được cấu hình rõ ràng qua `CORS_ORIGINS`, không hard-code.
- `.env` nằm trong `.gitignore`; không có secret nào trong source code.
- Log tập trung (`logs/app.log`, xoay vòng theo dung lượng) cho mọi lỗi hệ thống và các sự kiện xác thực quan trọng.

---

## 7. Ghi chú về dữ liệu công ty

Theo yêu cầu, dự án **không tự bịa** thông tin công ty chưa được cung cấp. Các trường sau đang là placeholder rõ ràng trong `site_settings` (sửa được ngay tại trang quản trị → "Thông tin công ty", không cần sửa code):

- `[SỐ ĐIỆN THOẠI]`, `[EMAIL CÔNG TY]`, `[ĐỊA CHỈ CÔNG TY]`, `[MÃ SỐ THUẾ]`, `[GIỜ LÀM VIỆC]`
- Các số liệu "10 năm kinh nghiệm / 100 dự án / 50 khách hàng / 20 kỹ sư" ở trang chủ là **số liệu minh họa lấy từ chính bản mô tả yêu cầu ban đầu**, được đánh dấu `stats_is_demo_data=true` trong `site_settings` — công ty cần xác nhận và cập nhật số liệu thật trước khi đưa site vào vận hành chính thức.
- Đội ngũ và đánh giá khách hàng đang là placeholder (`[Tên kiến trúc sư]`...) — cập nhật qua trang quản trị khi có thông tin thật.
- Dự án duy nhất đã seed sẵn ("Biệt thự mái Nhật một tầng") dùng đúng 7 ảnh phối cảnh do công ty cung cấp; các trường vị trí/diện tích/năm thực hiện để `[Địa điểm dự án]` / trống vì chưa được cung cấp — cập nhật qua trang quản trị.
