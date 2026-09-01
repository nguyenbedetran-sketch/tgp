"""
Seed the database with initial content so the website is browsable out of
the box: services, one real portfolio project (built from the architectural
renders supplied by the company), sample testimonials/team placeholders,
a few genuinely-written blog articles, and site-wide settings.

IMPORTANT - per project requirements, company facts that were not provided
(phone, email, address, tax code, real staff names, real years of
experience, real project count) are seeded as clearly bracketed placeholders
such as "[SO DIEN THOAI]" - NEVER as invented real-looking data. The admin
dashboard (Quan ly thong tin cong ty / Quan ly du an / Quan ly doi ngu) is
where the company replaces these with real information.

The homepage counters (+10 nam kinh nghiem, +100 du an, +50 khach hang,
+20 ky su) come directly from the site brief and are seeded as editable
`site_settings` rows - they are DEMO figures until the company confirms and
updates the real numbers via the admin dashboard.
"""
import json
import logging

from app.config.settings import config
from app.models.db import get_db
from app.services.security import hash_password

logger = logging.getLogger("tgp.seed")

SERVICES = [
    ("tu_van_xay_dung", "01", "Tư vấn xây dựng",
     "Đồng hành cùng khách hàng ngay từ bước lên ý tưởng: phân tích nhu cầu, khảo sát hiện trạng và đề xuất giải pháp xây dựng phù hợp ngân sách."),
    ("thiet_ke_kien_truc", "02", "Thiết kế kiến trúc",
     "Thiết kế phối cảnh, mặt bằng công năng và hồ sơ xin phép xây dựng cho nhà phố, biệt thự, văn phòng và công trình thương mại."),
    ("thiet_ke_noi_that", "03", "Thiết kế nội thất",
     "Giải pháp nội thất đồng bộ với kiến trúc tổng thể, tối ưu công năng sử dụng và thẩm mỹ không gian sống."),
    ("thiet_ke_ket_cau", "04", "Thiết kế kết cấu",
     "Tính toán kết cấu an toàn, tối ưu chi phí vật liệu, phù hợp điều kiện địa chất từng công trình."),
    ("thi_cong_xay_dung", "05", "Thi công xây dựng",
     "Triển khai thi công theo đúng hồ sơ thiết kế, kiểm soát chất lượng và tiến độ trong suốt quá trình xây dựng."),
    ("giam_sat_cong_trinh", "06", "Giám sát công trình",
     "Giám sát kỹ thuật độc lập, đảm bảo thi công đúng bản vẽ, đúng quy chuẩn và minh bạch khối lượng thực tế."),
    ("cai_tao_nang_cap", "07", "Cải tạo & nâng cấp",
     "Cải tạo, sửa chữa và nâng cấp công trình hiện hữu, tối ưu công năng mà vẫn kiểm soát tốt chi phí."),
    ("tu_van_chi_phi", "08", "Tư vấn chi phí xây dựng",
     "Bóc tách khối lượng và ước tính chi phí xây dựng sơ bộ, giúp chủ đầu tư chủ động kế hoạch tài chính."),
]

TEAM_PLACEHOLDERS = [
    ("[Tên kiến trúc sư]", "Kiến trúc sư trưởng", "Thiết kế kiến trúc nhà ở & công trình thương mại"),
    ("[Tên kỹ sư xây dựng]", "Kỹ sư xây dựng", "Quản lý thi công phần thô & hoàn thiện"),
    ("[Tên kỹ sư kết cấu]", "Kỹ sư kết cấu", "Tính toán kết cấu & nền móng"),
    ("[Tên quản lý dự án]", "Quản lý dự án", "Điều phối tiến độ & ngân sách dự án"),
    ("[Tên giám sát công trình]", "Giám sát công trình", "Giám sát chất lượng thi công tại hiện trường"),
]

TESTIMONIAL_PLACEHOLDERS = [
    ("[Tên khách hàng]", "[Tên dự án]",
     "[Nội dung đánh giá thực tế của khách hàng sẽ được cập nhật tại đây qua trang quản trị.]", 5),
]

PROJECT_IMAGE_FILES = [
    "villa-mainhat-01.jpg", "villa-mainhat-02.jpg", "villa-mainhat-03.jpg",
    "villa-mainhat-04.jpg", "villa-mainhat-05.jpg", "villa-mainhat-06.jpg",
    "villa-mainhat-07.jpg",
]

BLOG_POSTS = [
    {
        "title": "Cách chọn loại móng nhà phù hợp với nền đất",
        "slug": "cach-chon-loai-mong-nha-phu-hop-voi-nen-dat",
        "category": "Kinh nghiệm xây nhà",
        "author": "Đội ngũ kỹ thuật TGP",
        "excerpt": "Móng đơn, móng băng, móng bè hay móng cọc - lựa chọn sai loại móng có thể khiến chi phí đội lên đáng kể hoặc ảnh hưởng an toàn công trình.",
        "content": (
            "Việc lựa chọn loại móng phụ thuộc chủ yếu vào ba yếu tố: tải trọng công trình, "
            "điều kiện địa chất tại vị trí xây dựng và số tầng dự kiến.\n\n"
            "Móng đơn phù hợp với công trình tải trọng nhẹ, nền đất tốt. Móng băng thường dùng cho "
            "nhà phố nhiều tầng trên nền đất trung bình. Móng bè phù hợp khi nền đất yếu và cần phân "
            "bố đều tải trọng. Móng cọc là lựa chọn an toàn cho nền đất yếu hoặc công trình cao tầng, "
            "tuy chi phí cao hơn nhưng đảm bảo độ lún đồng đều.\n\n"
            "Trước khi quyết định, chủ đầu tư nên khảo sát địa chất thực tế thay vì chỉ dựa vào kinh "
            "nghiệm khu vực lân cận, vì nền đất có thể khác nhau đáng kể chỉ trong phạm vi vài chục mét."
        ),
    },
    {
        "title": "5 xu hướng thiết kế kiến trúc nhà ở được ưa chuộng",
        "slug": "5-xu-huong-thiet-ke-kien-truc-nha-o-duoc-ua-chuong",
        "category": "Xu hướng thiết kế",
        "author": "Đội ngũ kiến trúc TGP",
        "excerpt": "Từ mái Thái - mái Nhật cổ điển đến phong cách hiện đại tối giản, mỗi xu hướng phù hợp với một gu thẩm mỹ và ngân sách khác nhau.",
        "content": (
            "1. Phong cách tân cổ điển với mái Thái/mái Nhật, phào chỉ hoa văn tinh tế, phù hợp "
            "biệt thự và nhà vườn.\n\n"
            "2. Phong cách hiện đại tối giản, mảng khối vuông vắn, ít chi tiết trang trí, tối ưu chi "
            "phí hoàn thiện.\n\n"
            "3. Nhà phố mặt tiền kính lớn, tận dụng ánh sáng tự nhiên cho không gian đô thị.\n\n"
            "4. Không gian xanh tích hợp: sân trong, giếng trời, ban công cây xanh.\n\n"
            "5. Vật liệu bền vững, thân thiện môi trường ngày càng được ưu tiên trong các thiết kế mới."
        ),
    },
    {
        "title": "Ước tính chi phí xây nhà: nên bắt đầu từ đâu?",
        "slug": "uoc-tinh-chi-phi-xay-nha-nen-bat-dau-tu-dau",
        "category": "Vật liệu xây dựng",
        "author": "Đội ngũ kỹ thuật TGP",
        "excerpt": "Chi phí xây dựng phụ thuộc vào diện tích xây dựng thực tế (không chỉ là diện tích đất), loại móng, loại mái và mức độ hoàn thiện.",
        "content": (
            "Nhiều chủ đầu tư nhầm lẫn giữa diện tích đất và diện tích xây dựng tính phí. Diện tích "
            "xây dựng tính phí thường bao gồm diện tích sàn các tầng cộng thêm hệ số cho phần móng và "
            "phần mái.\n\n"
            "Mức hoàn thiện (thô, cơ bản, trung bình, cao cấp) là yếu tố ảnh hưởng lớn nhất đến đơn "
            "giá mỗi mét vuông. Bên cạnh đó, vị trí công trình và loại hình (nhà phố, biệt thự, văn "
            "phòng...) cũng làm thay đổi tổng chi phí.\n\n"
            "Công cụ Ước tính chi phí xây dựng trên website chỉ mang tính tham khảo ở bước đầu lên kế "
            "hoạch. Để có con số chính xác, chủ đầu tư cần được tư vấn dựa trên hồ sơ thiết kế cụ thể."
        ),
    },
]


def _slugify_exists(cur, table, slug_value):
    cur.execute(f"SELECT 1 FROM {table} WHERE slug = ?", (slug_value,))
    return cur.fetchone() is not None


def seed_if_empty():
    db = get_db()
    cur = db.cursor()

    _seed_services(cur)
    _seed_team(cur)
    _seed_testimonials(cur)
    _seed_projects(cur)
    _seed_blog(cur)
    _seed_hero_slides(cur)
    _seed_home_strengths(cur)
    _seed_settings(cur)
    _ensure_bootstrap_admin()

    db.commit()


def _ensure_bootstrap_admin():
    """Create one admin account on first boot when explicitly configured.

    The plaintext password is read only from the environment, hashed with the
    same PBKDF2 routine as the interactive admin script, and never logged or
    written to source control.
    """
    username = (config.ADMIN_BOOTSTRAP_USERNAME or "").strip()
    email = (config.ADMIN_BOOTSTRAP_EMAIL or "").strip()
    password = config.ADMIN_BOOTSTRAP_PASSWORD or ""
    if not username or not email or len(password) < 8:
        return

    db = get_db()
    existing = db.execute(
        "SELECT id, is_active FROM users WHERE username = ? OR email = ?",
        (username, email),
    ).fetchone()
    if existing:
        if not existing["is_active"]:
            db.execute(
                "UPDATE users SET is_active = 1, role = 'admin' WHERE id = ?",
                (existing["id"],),
            )
        return

    password_hash, salt = hash_password(password)
    db.execute(
        """INSERT INTO users
           (username, email, password_hash, password_salt, full_name, role)
           VALUES (?, ?, ?, ?, ?, 'admin')""",
        (username, email, password_hash, salt, "Quản trị Trần Gia Phát"),
    )
    logger.info("Created configured bootstrap admin account: %s", username)


def _seed_services(cur):
    cur.execute("SELECT COUNT(*) AS c FROM services")
    if cur.fetchone()["c"] > 0:
        return
    for i, (code, num, title, desc) in enumerate(SERVICES):
        slug = code.replace("_", "-")
        cur.execute(
            """INSERT INTO services (code, title, slug, icon, short_description, description, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (code, f"{num}. {title}", slug, num, desc, desc, i),
        )
    logger.info("Seeded %d services", len(SERVICES))


def _seed_team(cur):
    cur.execute("SELECT COUNT(*) AS c FROM team_members")
    if cur.fetchone()["c"] > 0:
        return
    for i, (name, position, specialty) in enumerate(TEAM_PLACEHOLDERS):
        cur.execute(
            """INSERT INTO team_members (full_name, position, specialty, photo_url, sort_order)
               VALUES (?, ?, ?, ?, ?)""",
            (name, position, specialty, None, i),
        )
    logger.info("Seeded %d team placeholders", len(TEAM_PLACEHOLDERS))


def _seed_testimonials(cur):
    cur.execute("SELECT COUNT(*) AS c FROM testimonials")
    if cur.fetchone()["c"] > 0:
        return
    for i, (name, project, content, rating) in enumerate(TESTIMONIAL_PLACEHOLDERS):
        cur.execute(
            """INSERT INTO testimonials (customer_name, project_name, content, rating, sort_order)
               VALUES (?, ?, ?, ?, ?)""",
            (name, project, content, rating, i),
        )
    logger.info("Seeded %d testimonial placeholders", len(TESTIMONIAL_PLACEHOLDERS))


def _seed_projects(cur):
    cur.execute("SELECT COUNT(*) AS c FROM projects")
    if cur.fetchone()["c"] > 0:
        return

    cover = f"/assets/images/projects/{PROJECT_IMAGE_FILES[0]}"
    cur.execute(
        """INSERT INTO projects
           (title, slug, category, location, area_m2, year, cost_display, summary, concept,
            design_notes, cover_image, status, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'published', 0)""",
        (
            "Biệt thự mái Nhật một tầng",
            "biet-thu-mai-nhat-mot-tang",
            "biet_thu",
            "[Địa điểm dự án]",
            None,
            None,
            "Liên hệ",
            "Phối cảnh thiết kế biệt thự một tầng mái Nhật, tiền sảnh cột trụ cổ điển, "
            "sân vườn và lối vào rộng rãi.",
            "Thiết kế theo phong cách tân cổ điển: mái Nhật nhiều lớp, hệ cột trụ và phào chỉ "
            "tạo điểm nhấn cho mặt tiền, kết hợp sân vườn và bậc thềm đá tự nhiên.",
            "Thông tin diện tích, vị trí và tiến độ thi công thực tế sẽ được công ty cập nhật "
            "qua trang quản trị.",
            cover,
        ),
    )
    project_id = cur.lastrowid
    for i, filename in enumerate(PROJECT_IMAGE_FILES):
        cur.execute(
            """INSERT INTO project_images (project_id, image_url, caption, sort_order)
               VALUES (?, ?, ?, ?)""",
            (project_id, f"/assets/images/projects/{filename}", "Phối cảnh thiết kế", i),
        )
    logger.info("Seeded 1 featured project with %d images", len(PROJECT_IMAGE_FILES))


def _seed_blog(cur):
    cur.execute("SELECT COUNT(*) AS c FROM blog_posts")
    if cur.fetchone()["c"] > 0:
        return
    for post in BLOG_POSTS:
        cur.execute(
            """INSERT INTO blog_posts
               (title, slug, category, author, excerpt, content, thumbnail_url,
                seo_title, seo_description, status, published_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'published', datetime('now'))""",
            (
                post["title"], post["slug"], post["category"], post["author"],
                post["excerpt"], post["content"], None,
                post["title"] + " | Trần Gia Phát", post["excerpt"],
            ),
        )
    logger.info("Seeded %d blog posts", len(BLOG_POSTS))


def _seed_hero_slides(cur):
    cur.execute("SELECT COUNT(*) AS c FROM hero_slides")
    if cur.fetchone()["c"] > 0:
        return
    cur.execute(
        """INSERT INTO hero_slides
           (image_url, eyebrow, title_line1, title_line2, subtitle,
            button1_text, button1_link, button2_text, button2_link, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
        (
            "/assets/images/projects/villa-mainhat-07.jpg",
            "Tư vấn – Thiết kế – Xây dựng",
            "KIẾN TẠO KHÔNG GIAN",
            "KIẾN TẠO GIÁ TRỊ",
            "Công ty TNHH Tư vấn Thiết kế Xây dựng Trần Gia Phát – Đồng hành cùng khách hàng từ ý tưởng đến công trình hoàn thiện.",
            "Khám phá dự án", "/pages/du-an.html",
            "Nhận tư vấn", "/pages/lien-he.html",
        ),
    )
    logger.info("Seeded 1 default hero slide")


HOME_STRENGTHS = [
    ("Quy trình chuyên nghiệp", "Kiểm soát chặt chẽ từ khảo sát, thiết kế đến thi công và giám sát."),
    ("Chất lượng & tiến độ", "Cam kết đúng hồ sơ thiết kế, minh bạch khối lượng thi công."),
    ("Giải pháp tối ưu chi phí", "Tư vấn phương án thiết kế phù hợp ngân sách của khách hàng."),
]


def _seed_home_strengths(cur):
    cur.execute("SELECT COUNT(*) AS c FROM home_strengths")
    if cur.fetchone()["c"] > 0:
        return
    for i, (title, desc) in enumerate(HOME_STRENGTHS):
        cur.execute(
            """INSERT INTO home_strengths (image_url, title, description, sort_order)
               VALUES (NULL, ?, ?, ?)""",
            (title, desc, i),
        )
    logger.info("Seeded %d home strengths", len(HOME_STRENGTHS))


DEFAULT_SETTINGS = {
    "company_name": "CÔNG TY TNHH TƯ VẤN THIẾT KẾ XÂY DỰNG TRẦN GIA PHÁT",
    "brand_name": "TRẦN GIA PHÁT",
    "tagline": "Tư vấn – Thiết kế – Xây dựng",
    "hero_title_line1": "KIẾN TẠO KHÔNG GIAN",
    "hero_title_line2": "KIẾN TẠO GIÁ TRỊ",
    "hero_subtitle": "Công ty TNHH Tư vấn Thiết kế Xây dựng Trần Gia Phát – Đồng hành cùng khách hàng từ ý tưởng đến công trình hoàn thiện.",
    "phone": "0937114884",
    "hotline": "0937114884",
    "email": "trangiaphat988@gmail.com",
    "address": "89, Tô Vĩnh Diện, Phường Langbian, Đà Lạt",
    "tax_code": "[MÃ SỐ THUẾ]",
    "working_hours": "7h30 - 11h30, 13h30 - 17h00",
    "facebook_url": "[LINK FACEBOOK]",
    "zalo_url": "[LINK ZALO]",
    "youtube_url": "[LINK YOUTUBE]",
    "tiktok_url": "[LINK TIKTOK]",
    "map_embed_url": "",
    # Thanh thông báo/khuyến mãi ở đầu trang - tắt theo mặc định cho tới khi
    # công ty nhập nội dung thật qua trang quản trị.
    "announcement_enabled": "false",
    "announcement_text": "",
    "announcement_link": "",
    # Homepage counters - DEMO figures from the design brief, mark for review.
    "stat_years": "10",
    "stat_projects": "100",
    "stat_clients": "50",
    "stat_engineers": "20",
    "stats_is_demo_data": "true",
    "copyright_year": "2026",
}


def _seed_settings(cur):
    for key, value in DEFAULT_SETTINGS.items():
        cur.execute(
            "INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
