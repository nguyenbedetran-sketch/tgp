# API Documentation — Trần Gia Phát Backend

Base URL (local dev): `http://localhost:8000`

All responses are JSON with a consistent envelope:

```json
{ "success": true, "data": { ... } }
{ "success": false, "error": "Thông báo lỗi", "errors": { "field": "chi tiết" } }
```

Authenticated endpoints require an `Authorization: Bearer <token>` header, where `<token>` is the JWT returned by `POST /api/auth/login`.

---

## Health

### `GET /api/health`
No auth. Returns `{ "success": true, "status": "ok", "service": "tgp-backend" }`.

---

## Auth

### `POST /api/auth/login`
Body: `{ "username": "admin", "password": "..." }`
Returns: `{ "token": "...", "user": { "id", "username", "full_name", "role" } }`
Rate limited (10 req / 60s / IP).

### `POST /api/auth/logout`
Auth required. Stateless JWT — client should discard the token.

### `GET /api/auth/me`
Auth required. Returns the decoded token payload.

---

## Projects (`/api/projects`)

### `GET /api/projects`
Query params: `category` (nha_pho|biet_thu|van_phong|noi_that|thuong_mai|khac|all), `status` (draft|published|all, default published), `limit`.
Public.

### `GET /api/projects/{id|slug}`
Public. Returns project + `images[]`.

### `POST /api/projects` — admin
Body fields: `title*`, `category*`, `location`, `area_m2`, `year`, `cost_display`, `summary`, `concept`, `design_notes`, `progress_notes`, `result_notes`, `cover_image`, `status` (draft|published), `sort_order`.

### `PUT /api/projects/{id}` — admin
Partial update, any subset of the fields above.

### `DELETE /api/projects/{id}` — admin

### `POST /api/projects/{id}/images` — admin
Body: `{ "image_url": "...", "caption": "...", "sort_order": 0 }`

### `DELETE /api/projects/images/{image_id}` — admin

---

## Services (`/api/services`)
`GET /api/services` (public) · `GET /api/services/{slug|code}` (public) · `POST` / `PUT /{id}` / `DELETE /{id}` (admin).
Fields: `title*`, `code`, `slug`, `icon`, `short_description`, `description`, `sort_order`.

## Blog (`/api/blog`)
`GET /api/blog?category=&status=&limit=` (public) · `GET /api/blog/{id|slug}` (public) · `POST` / `PUT /{id}` / `DELETE /{id}` (admin).
Fields: `title*`, `content*`, `slug`, `category`, `author`, `excerpt`, `thumbnail_url`, `seo_title`, `seo_description`, `status`.

## Team (`/api/team`)
`GET /api/team` (public) · `POST` / `PUT /{id}` / `DELETE /{id}` (admin).
Fields: `full_name*`, `position*`, `specialty`, `photo_url`, `sort_order`.

## Testimonials (`/api/testimonials`)
`GET /api/testimonials` (public) · `POST` / `PUT /{id}` / `DELETE /{id}` (admin).
Fields: `customer_name*`, `content*`, `project_name`, `rating` (1-5), `avatar_url`, `sort_order`.

## Site settings (`/api/settings`, `/api/admin/settings`)
`GET /api/settings` (public) — returns the full key/value map used to render company info, hero text and homepage counters.
`PUT /api/admin/settings` (admin) — body: `{ "key1": "value1", "key2": "value2" }`, upserts each key.

---

## Contact form (`/api/contact`, `/api/admin/contacts`)

### `POST /api/contact`
Public, rate limited (8 req / 60s / IP), honeypot field `website` (must stay empty).
Body: `full_name*`, `phone*` (validated format), `email` (validated if present), `location`, `construction_type`, `area_expected`, `budget`, `message`.

### `GET /api/admin/contacts?status=` — admin
### `PUT /api/admin/contacts/{id}` — admin — body `{ "status": "new"|"contacted"|"closed" }`
### `DELETE /api/admin/contacts/{id}` — admin

---

## Cost estimate tool (`/api/estimate`)

### `POST /api/estimate`
Public, rate limited (8 req / 60s / IP). Delegates the actual calculation to the compiled C++ engine (`cpp/tgp_calculator`) via subprocess — see `app/services/cpp_bridge.py`.

Body:
```json
{
  "construction_type": "biet_thu",       // nha_pho | biet_thu | van_phong | nha_xuong | cai_tao
  "land_area_m2": 200,
  "footprint_area_m2": 150,               // required, > 0
  "floors": 1,                            // required, 1-20
  "foundation_type": "bang",              // don | bang | be | coc
  "roof_type": "thai_nhat",               // bang | thai_nhat | ton
  "finish_level": "cao_cap",              // tho | co_ban | trung_binh | cao_cap
  "location": "TP.HCM"
}
```

Response `data`:
```json
{
  "footprint_area_m2": 150,
  "total_construction_area_m2": 285,
  "unit_price_vnd_per_m2": 7500000,
  "estimated_cost_vnd": 2458125000,
  "cost_range_min_vnd": 2212312500,
  "cost_range_max_vnd": 2826843750,
  "disclaimer": "Kết quả chỉ mang tính chất tham khảo..."
}
```

Every call is also logged to the `estimates` table (input + output JSON) for later analysis.

---

## Pageviews (`/api/visit`)

### `POST /api/visit`
Public, rate limited (60 req / 60s / IP). Body: `{ "path": "/index.html" }`. Called once per page load by `frontend/js/main.js`. Powers the real (non-fabricated) "Lượt truy cập" metric on the admin dashboard.

---

## Admin dashboard & export (`/api/admin`)

### `GET /api/admin/dashboard` — admin
Returns aggregate counts (projects, contacts, blog posts, estimates, page views), monthly breakdowns, and the 5 most recent contact requests.

### `GET /api/admin/export/{projects|contacts}?format=csv|json` — admin
Delegates rendering to the Java report service (`java/target/tgp-report-service.jar`) via subprocess — see `app/services/java_bridge.py`. Returns a file download (`Content-Disposition: attachment`).

---

## Uploads (`/api/admin/upload`)

### `POST /api/admin/upload` — admin
`multipart/form-data`, field name `file`. Validates extension allow-list AND real file content (magic bytes), renames to a random UUID, enforces `MAX_UPLOAD_SIZE_MB`. Returns `{ "url": "/uploads/xxxx.jpg", "filename": "...", "size_bytes": ... }`.
