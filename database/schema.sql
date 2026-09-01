-- Tran Gia Phat - database schema (SQLite)
-- Applied automatically on backend startup by app/models/db.py:init_db()

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- users: admin / staff accounts for the management dashboard
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    password_salt   TEXT NOT NULL,
    full_name       TEXT,
    role            TEXT NOT NULL DEFAULT 'admin',   -- admin | editor
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at   TEXT
);

-- ---------------------------------------------------------------------
-- projects: portfolio / du an tieu bieu
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    category        TEXT NOT NULL,     -- nha_pho | biet_thu | van_phong | noi_that | thuong_mai | khac
    location        TEXT,
    area_m2         REAL,
    year            INTEGER,
    cost_display    TEXT,              -- optional, free text ("Lien he" | "2.4 ty" ...), never invented
    summary         TEXT,
    concept         TEXT,
    design_notes    TEXT,
    progress_notes  TEXT,
    result_notes    TEXT,
    cover_image     TEXT,
    status          TEXT NOT NULL DEFAULT 'published', -- draft | published
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS project_images (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    image_url       TEXT NOT NULL,
    caption         TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0
);

-- ---------------------------------------------------------------------
-- services: dich vu cong ty cung cap
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS services (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    icon            TEXT,
    short_description TEXT,
    description     TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- blog_posts: tin tuc / kien thuc
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS blog_posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    category        TEXT,
    author          TEXT,
    excerpt         TEXT,
    content         TEXT,
    thumbnail_url   TEXT,
    seo_title       TEXT,
    seo_description TEXT,
    status          TEXT NOT NULL DEFAULT 'published',
    published_at    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- contacts: yeu cau tu van tu form website
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contacts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name           TEXT NOT NULL,
    phone               TEXT NOT NULL,
    email               TEXT,
    location            TEXT,
    construction_type   TEXT,
    area_expected       TEXT,
    budget              TEXT,
    message             TEXT,
    status              TEXT NOT NULL DEFAULT 'new',  -- new | contacted | closed
    source              TEXT DEFAULT 'website',
    ip_address          TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- testimonials: danh gia khach hang
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS testimonials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name   TEXT NOT NULL,
    project_name    TEXT,
    content         TEXT NOT NULL,
    rating          INTEGER NOT NULL DEFAULT 5,
    avatar_url      TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- team_members: doi ngu
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS team_members (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT NOT NULL,
    position        TEXT NOT NULL,
    specialty       TEXT,
    photo_url       TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0
);

-- ---------------------------------------------------------------------
-- hero_slides: slide anh lon o dau trang chu (co the them/bot/sap xep)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hero_slides (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url       TEXT NOT NULL,
    eyebrow         TEXT,
    title_line1     TEXT NOT NULL,
    title_line2     TEXT,
    subtitle        TEXT,
    button1_text    TEXT,
    button1_link    TEXT,
    button2_text    TEXT,
    button2_link    TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- home_strengths: "vi sao chon chung toi" - the manh co anh minh hoa
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS home_strengths (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url       TEXT,
    title           TEXT NOT NULL,
    description     TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- estimates: log ket qua cong cu uoc tinh chi phi (C++ engine)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estimates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_name    TEXT,
    phone           TEXT,
    input_json      TEXT NOT NULL,
    result_json     TEXT NOT NULL,
    ip_address      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- site_settings: key/value cho thong tin cong ty, counters, banner...
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS site_settings (
    key             TEXT PRIMARY KEY,
    value           TEXT,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- page_views: simple real pageview log, powers "Luot truy cap" on the
-- admin dashboard (no fabricated analytics numbers).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS page_views (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path            TEXT,
    ip_address      TEXT,
    user_agent      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category);
CREATE INDEX IF NOT EXISTS idx_blog_status ON blog_posts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_created ON contacts(created_at);
CREATE INDEX IF NOT EXISTS idx_pageviews_created ON page_views(created_at);
