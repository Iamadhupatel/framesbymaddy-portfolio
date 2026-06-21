-- ============================================================
--  FramesByMaddy — SQLite Database Schema
--  File: schema.sql
--  Engine: SQLite 3 (via Python's built-in sqlite3 module)
--  Run standalone: sqlite3 framesbymaddy.db < schema.sql
--  (app.py runs init_db() automatically on startup)
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────
-- TABLE: inquiries
-- Stores every contact form submission from the portfolio
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inquiries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    email        TEXT    NOT NULL,
    project_type TEXT    NOT NULL,   -- "Reel Editing" | "Photography" | "Videography" | etc.
    message      TEXT    NOT NULL,
    status       TEXT    NOT NULL
                         DEFAULT 'new'
                         CHECK (status IN ('new','read','replied')),
    created_at   TEXT    NOT NULL
                         DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- TABLE: photos
-- Photography portfolio gallery (masonry grid)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS photos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT,               -- Optional caption
    category    TEXT    NOT NULL
                        CHECK (category IN ('portrait','event','street','lifestyle','product')),
    image_url   TEXT    NOT NULL,   -- Direct image URL
    sort_order  INTEGER DEFAULT 0,
    visible     INTEGER DEFAULT 1
                        CHECK (visible IN (0,1)),
    created_at  TEXT    NOT NULL
                        DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- TABLE: testimonials
-- Client reviews displayed in testimonials slider
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS testimonials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT    NOT NULL,
    client_role TEXT,               -- e.g. "Content Creator, 150K followers"
    initials    TEXT,               -- 2-3 char avatar fallback, e.g. "AR"
    review_text TEXT    NOT NULL,
    stars       INTEGER DEFAULT 5
                        CHECK (stars BETWEEN 1 AND 5),
    visible     INTEGER DEFAULT 1
                        CHECK (visible IN (0,1)),
    sort_order  INTEGER DEFAULT 0,
    created_at  TEXT    NOT NULL
                        DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- TABLE: services
-- Services cards (Reel Editing, Photography, Videography)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS services (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL,
    features    TEXT,               -- JSON array: '["Feature 1","Feature 2"]'
    icon_type   TEXT    DEFAULT 'video'
                        CHECK (icon_type IN ('video','camera','film')),
    sort_order  INTEGER DEFAULT 0,
    visible     INTEGER DEFAULT 1
                        CHECK (visible IN (0,1))
);

-- ─────────────────────────────────────────────
-- TABLE: settings
-- Key-value store for all site configuration
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- TABLE: admin_users
-- Admin panel login accounts
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admin_users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,   -- SHA-256 hex digest
    created_at    TEXT    NOT NULL
                          DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- INDEXES for performance
-- ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_inquiries_status     ON inquiries   (status);
CREATE INDEX IF NOT EXISTS idx_inquiries_created    ON inquiries   (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_photos_category      ON photos      (category);
CREATE INDEX IF NOT EXISTS idx_photos_visible       ON photos      (visible, sort_order);
CREATE INDEX IF NOT EXISTS idx_testimonials_visible ON testimonials(visible, sort_order);

-- ─────────────────────────────────────────────
-- SEED DATA — Default content
-- (app.py inserts these automatically via init_db())
-- ─────────────────────────────────────────────

-- Default site settings
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('showreel_vimeo_id',  '1199859781'),
    ('hero_vimeo_id',      '1200231066'),
    ('ba_before_vimeo_id', '1199859780'),
    ('ba_after_vimeo_id',  '1199859781'),
    ('whatsapp_number',    '917093474065'),
    ('instagram_url',      'https://www.instagram.com/frames.bymaddy'),
    ('email',              'framesbymaddy.49@gmail.com'),
    ('tagline',            'Capturing Stories Through Frames.'),
    ('stats_projects',     '50+'),
    ('stats_clients',      '30+'),
    ('stats_experience',   '3+');

-- Default services
INSERT OR IGNORE INTO services (id, title, description, features, icon_type, sort_order) VALUES
    (1, 'Reel Editing',
        'Instagram Reels, YouTube Shorts, and engaging social media content crafted to stop the scroll.',
        '["Instagram & YouTube Reels","Motion graphics & transitions","Sound design & sync","Platform-optimised exports"]',
        'video', 1),
    (2, 'Photography',
        'Portraits, events, lifestyle, and professional photography that tells your story with depth.',
        '["Portrait & personal branding","Event & wedding coverage","Product & commercial shoots","Professional retouching"]',
        'camera', 2),
    (3, 'Videography',
        'Cinematic videos, events, promotional content, and storytelling projects with a premium finish.',
        '["Cinematic event films","Brand promotional videos","Documentary storytelling","Colour grading & DI"]',
        'film', 3);

-- Default admin (username: admin | password: maddy2026)
-- SHA-256 of "maddy2026" = 97b5c793d0a27de97e5a66a0e90eccc7eb5d58c4b28b2ab62168ab3dbcae36a9
INSERT OR IGNORE INTO admin_users (username, password_hash) VALUES
    ('admin', '97b5c793d0a27de97e5a66a0e90eccc7eb5d58c4b28b2ab62168ab3dbcae36a9');
