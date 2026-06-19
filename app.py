"""
FramesByMaddy — Full Stack Portfolio
Flask + SQLite backend
Run: python app.py
Visit: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3, os, hashlib, datetime, json

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
)
print("Template Folder:", app.template_folder)
print("Jinja Search Path:", app.jinja_loader.searchpath)

app.secret_key = "framesbymaddy_secret_2026_change_this"
print("Template Folder:",
      os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

print("Admin Login Exists:",
      os.path.exists(
          os.path.join(
              os.path.dirname(os.path.abspath(__file__)),
              "templates",
              "admin_login.html"
          )
      ))

DB_PATH = os.path.join(

    os.path.dirname(os.path.abspath(__file__)),

    "framesbymaddy.db"

)
print("Current Working Directory:", os.getcwd())
print("App File Directory:", os.path.dirname(os.path.abspath(__file__)))
print("Templates Folder Exists:", os.path.exists("templates"))

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    """Create all tables and seed initial data."""
    conn = get_db()
    c = conn.cursor()

    # ── INQUIRIES (Contact Form submissions) ──────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS inquiries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL,
            project_type TEXT   NOT NULL,
            message     TEXT    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'new',   -- new | read | replied
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── PROJECTS (Work section) ────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            thumbnail   TEXT,                  -- image URL or base64
            vimeo_id    TEXT,                  -- Vimeo video ID
            sort_order  INTEGER DEFAULT 0,
            visible     INTEGER DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── PHOTOS (Photography section) ──────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT,
            category    TEXT    NOT NULL,
            image_url   TEXT    NOT NULL,
            sort_order  INTEGER DEFAULT 0,
            visible     INTEGER DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── TESTIMONIALS ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS testimonials (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT    NOT NULL,
            client_role TEXT,
            initials    TEXT,
            review_text TEXT    NOT NULL,
            stars       INTEGER DEFAULT 5,
            visible     INTEGER DEFAULT 1,
            sort_order  INTEGER DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── SERVICES ──────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            description TEXT    NOT NULL,
            features    TEXT,                  -- JSON array of strings
            icon_type   TEXT    DEFAULT 'video',
            sort_order  INTEGER DEFAULT 0,
            visible     INTEGER DEFAULT 1
        )
    """)

    # ── SITE SETTINGS (key-value store) ───────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key         TEXT PRIMARY KEY,
            value       TEXT,
            updated_at  TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── ADMIN USERS ───────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── SEED DATA (only if tables are empty) ──────────────────

    # Default admin (username: admin, password: maddy2026)
    c.execute("SELECT COUNT(*) FROM admin_users")
    if c.fetchone()[0] == 0:
        pw_hash = hashlib.sha256("maddy2026".encode()).hexdigest()
        c.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
                  ("admin", pw_hash))

    # Default services
    c.execute("SELECT COUNT(*) FROM services")
    if c.fetchone()[0] == 0:
        services = [
            ("Reel Editing",
             "Instagram Reels, YouTube Shorts, and engaging social media content crafted to stop the scroll.",
             json.dumps(["Instagram & YouTube Reels","Motion graphics & transitions","Sound design & sync","Platform-optimised exports"]),
             "video", 1),
            ("Photography",
             "Portraits, events, lifestyle, and professional photography that tells your story with depth.",
             json.dumps(["Portrait & personal branding","Event & wedding coverage","Product & commercial shoots","Professional retouching"]),
             "camera", 2),
            ("Videography",
             "Cinematic videos, events, promotional content, and storytelling projects with a premium finish.",
             json.dumps(["Cinematic event films","Brand promotional videos","Documentary storytelling","Colour grading & DI"]),
             "film", 3),
        ]
        c.executemany(
            "INSERT INTO services (title, description, features, icon_type, sort_order) VALUES (?,?,?,?,?)",
            services)

    # Default testimonials
    c.execute("SELECT COUNT(*) FROM testimonials")
    if c.fetchone()[0] == 0:
        testimonials = [
            ("Aditya Reddy", "Content Creator, 150K followers", "AR",
             "Madhukar completely transformed my brand's visual identity. The reels he edited got 3× more engagement than anything I'd posted before. Absolutely cinematic quality.",
             5, 1),
            ("Priya Sharma", "Wedding Client", "PS",
             "The wedding film he created left us speechless. Every frame told our story perfectly. Friends and family couldn't believe the quality. Will recommend to everyone.",
             5, 2),
            ("Vikram Kulkarni", "Startup Founder", "VK",
             "Our product launch video got featured on two major tech blogs. FramesByMaddy understood exactly what our brand needed — premium, clean, cinematic.",
             5, 3),
            ("Neha Kapoor", "Brand Manager, Fashion Label", "NK",
             "Quick turnaround, incredible attention to detail, and the final edits always exceed expectations. My go-to editor for all content campaigns.",
             5, 4),
        ]
        c.executemany(
            "INSERT INTO testimonials (client_name, client_role, initials, review_text, stars, sort_order) VALUES (?,?,?,?,?,?)",
            testimonials)

    # Default projects
    c.execute("SELECT COUNT(*) FROM projects")
    if c.fetchone()[0] == 0:
        projects = [
            ("Instagram Reel — Brand Showcase", "reel", "", "1199859781", 1),
            ("Cinematic Short Film", "cinematic", "", "1199859781", 2),
            ("Product Commercial — Launch", "commercial", "", "", 3),
            ("Wedding Highlights Film", "event", "", "", 4),
            ("Creator Content Package", "lifestyle", "", "", 5),
            ("YouTube Shorts Series", "reel", "", "", 6),
        ]
        c.executemany(
            "INSERT INTO projects (title, category, thumbnail, vimeo_id, sort_order) VALUES (?,?,?,?,?)",
            projects)

    # Default site settings
    defaults = {
        "showreel_vimeo_id":    "1199859781",
        "hero_vimeo_id":        "1200231066",
        "ba_before_vimeo_id":   "1199859780",
        "ba_after_vimeo_id":    "1199859781",
        "whatsapp_number":      "917093474065",
        "instagram_url":        "https://www.instagram.com/frames.bymaddy",
        "email":                "framesbymaddy.49@gmail.com",
        "tagline":              "Capturing Stories Through Frames.",
        "stats_projects":       "50+",
        "stats_clients":        "30+",
        "stats_experience":     "3+",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()
    print("✅ Database initialised:", DB_PATH)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────────
@app.route("/")
def index():
    conn = get_db()
    settings     = get_settings()
    projects     = conn.execute("SELECT * FROM projects WHERE visible=1 ORDER BY sort_order").fetchall()
    photos       = conn.execute("SELECT * FROM photos   WHERE visible=1 ORDER BY sort_order").fetchall()
    testimonials = conn.execute("SELECT * FROM testimonials WHERE visible=1 ORDER BY sort_order").fetchall()
    services     = conn.execute("SELECT * FROM services WHERE visible=1 ORDER BY sort_order").fetchall()
    conn.close()

    # Parse features JSON for services
    services_parsed = []
    for s in services:
        d = dict(s)
        try:
            d["features_list"] = json.loads(d["features"] or "[]")
        except Exception:
            d["features_list"] = []
        services_parsed.append(d)

    return render_template("index.html",
        settings=settings,
        projects=projects,
        photos=photos,
        testimonials=testimonials,
        services=services_parsed,
    )


# ─────────────────────────────────────────────
# CONTACT FORM API
# ─────────────────────────────────────────────
@app.route("/api/inquiry", methods=["POST"])
def submit_inquiry():
    data = request.get_json()
    name         = (data.get("name") or "").strip()
    email        = (data.get("email") or "").strip()
    project_type = (data.get("project_type") or "").strip()
    message      = (data.get("message") or "").strip()

    if not all([name, email, project_type, message]):
        return jsonify({"ok": False, "error": "All fields are required."}), 400
    if "@" not in email or "." not in email:
        return jsonify({"ok": False, "error": "Invalid email address."}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO inquiries (name, email, project_type, message) VALUES (?,?,?,?)",
        (name, email, project_type, message)
    )
    conn.commit()
    conn.close()

    settings = get_settings()
    wa_num   = settings.get("whatsapp_number", "917093474065")
    wa_msg   = f"Hi Madhukar! I found you on FramesByMaddy.\n\n*Name:* {name}\n*Email:* {email}\n*Project:* {project_type}\n*Message:* {message}"
    import urllib.parse
    wa_url = f"https://wa.me/{wa_num}?text={urllib.parse.quote(wa_msg)}"

    return jsonify({"ok": True, "whatsapp_url": wa_url})


# ─────────────────────────────────────────────
# ADMIN — AUTH
# ─────────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        pw_hash  = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM admin_users WHERE username=? AND password_hash=?",
            (username, pw_hash)
        ).fetchone()
        conn.close()
        if user:
            session["admin_logged_in"] = True
            session["admin_username"]  = username
            return redirect(url_for("admin_dashboard"))
        flash("Invalid username or password.")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ─────────────────────────────────────────────
# ADMIN — DASHBOARD
# ─────────────────────────────────────────────
@app.route("/admin")
@require_admin
def admin_dashboard():
    conn = get_db()
    inquiry_count  = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
    new_count      = conn.execute("SELECT COUNT(*) FROM inquiries WHERE status='new'").fetchone()[0]
    project_count  = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    photo_count    = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    recent_inquiries = conn.execute(
        "SELECT * FROM inquiries ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return render_template("admin_dashboard.html",
        inquiry_count=inquiry_count, new_count=new_count,
        project_count=project_count, photo_count=photo_count,
        recent_inquiries=recent_inquiries)


# ─────────────────────────────────────────────
# ADMIN — INQUIRIES
# ─────────────────────────────────────────────
@app.route("/admin/inquiries")
@require_admin
def admin_inquiries():
    conn = get_db()
    inquiries = conn.execute(
        "SELECT * FROM inquiries ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("admin_inquiries.html", inquiries=inquiries)

@app.route("/admin/inquiries/<int:inquiry_id>/status", methods=["POST"])
@require_admin
def update_inquiry_status(inquiry_id):
    status = request.form.get("status")
    if status in ("new", "read", "replied"):
        conn = get_db()
        conn.execute("UPDATE inquiries SET status=? WHERE id=?", (status, inquiry_id))
        conn.commit()
        conn.close()
    return redirect(url_for("admin_inquiries"))

@app.route("/admin/inquiries/<int:inquiry_id>/delete", methods=["POST"])
@require_admin
def delete_inquiry(inquiry_id):
    conn = get_db()
    conn.execute("DELETE FROM inquiries WHERE id=?", (inquiry_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_inquiries"))


# ─────────────────────────────────────────────
# ADMIN — PROJECTS
# ─────────────────────────────────────────────
@app.route("/admin/projects")
@require_admin
def admin_projects():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY sort_order").fetchall()
    conn.close()
    return render_template("admin_projects.html", projects=projects)

@app.route("/admin/projects/add", methods=["GET", "POST"])
@require_admin
def admin_add_project():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO projects (title, category, thumbnail, vimeo_id, sort_order, visible) VALUES (?,?,?,?,?,?)",
            (request.form["title"], request.form["category"],
             request.form["thumbnail"], request.form["vimeo_id"],
             request.form.get("sort_order", 99), 1)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_projects"))
    return render_template("admin_project_form.html", project=None)

@app.route("/admin/projects/<int:pid>/edit", methods=["GET", "POST"])
@require_admin
def admin_edit_project(pid):
    conn = get_db()
    project = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if request.method == "POST":
        conn.execute(
            "UPDATE projects SET title=?, category=?, thumbnail=?, vimeo_id=?, sort_order=?, visible=? WHERE id=?",
            (request.form["title"], request.form["category"],
             request.form["thumbnail"], request.form["vimeo_id"],
             request.form.get("sort_order", 99),
             1 if request.form.get("visible") else 0, pid)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_projects"))
    conn.close()
    return render_template("admin_project_form.html", project=project)

@app.route("/admin/projects/<int:pid>/delete", methods=["POST"])
@require_admin
def admin_delete_project(pid):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_projects"))


# ─────────────────────────────────────────────
# ADMIN — PHOTOS
# ─────────────────────────────────────────────
@app.route("/admin/photos")
@require_admin
def admin_photos():
    conn = get_db()
    photos = conn.execute("SELECT * FROM photos ORDER BY sort_order").fetchall()
    conn.close()
    return render_template("admin_photos.html", photos=photos)

@app.route("/admin/photos/add", methods=["GET", "POST"])
@require_admin
def admin_add_photo():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO photos (title, category, image_url, sort_order, visible) VALUES (?,?,?,?,?)",
            (request.form["title"], request.form["category"],
             request.form["image_url"], request.form.get("sort_order", 99), 1)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_photos"))
    return render_template("admin_photo_form.html", photo=None)

@app.route("/admin/photos/<int:pid>/edit", methods=["GET", "POST"])
@require_admin
def admin_edit_photo(pid):
    conn = get_db()
    photo = conn.execute("SELECT * FROM photos WHERE id=?", (pid,)).fetchone()
    if request.method == "POST":
        conn.execute(
            "UPDATE photos SET title=?, category=?, image_url=?, sort_order=?, visible=? WHERE id=?",
            (request.form["title"], request.form["category"],
             request.form["image_url"], request.form.get("sort_order", 99),
             1 if request.form.get("visible") else 0, pid)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_photos"))
    conn.close()
    return render_template("admin_photo_form.html", photo=photo)

@app.route("/admin/photos/<int:pid>/delete", methods=["POST"])
@require_admin
def admin_delete_photo(pid):
    conn = get_db()
    conn.execute("DELETE FROM photos WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_photos"))


# ─────────────────────────────────────────────
# ADMIN — TESTIMONIALS
# ─────────────────────────────────────────────
@app.route("/admin/testimonials")
@require_admin
def admin_testimonials():
    conn = get_db()
    testimonials = conn.execute("SELECT * FROM testimonials ORDER BY sort_order").fetchall()
    conn.close()
    return render_template("admin_testimonials.html", testimonials=testimonials)

@app.route("/admin/testimonials/add", methods=["GET", "POST"])
@require_admin
def admin_add_testimonial():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO testimonials (client_name, client_role, initials, review_text, stars, sort_order, visible) VALUES (?,?,?,?,?,?,?)",
            (request.form["client_name"], request.form["client_role"],
             request.form["initials"], request.form["review_text"],
             int(request.form.get("stars", 5)), request.form.get("sort_order", 99), 1)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_testimonials"))
    return render_template("admin_testimonial_form.html", t=None)

@app.route("/admin/testimonials/<int:tid>/edit", methods=["GET", "POST"])
@require_admin
def admin_edit_testimonial(tid):
    conn = get_db()
    t = conn.execute("SELECT * FROM testimonials WHERE id=?", (tid,)).fetchone()
    if request.method == "POST":
        conn.execute(
            "UPDATE testimonials SET client_name=?, client_role=?, initials=?, review_text=?, stars=?, sort_order=?, visible=? WHERE id=?",
            (request.form["client_name"], request.form["client_role"],
             request.form["initials"], request.form["review_text"],
             int(request.form.get("stars", 5)), request.form.get("sort_order", 99),
             1 if request.form.get("visible") else 0, tid)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_testimonials"))
    conn.close()
    return render_template("admin_testimonial_form.html", t=t)

@app.route("/admin/testimonials/<int:tid>/delete", methods=["POST"])
@require_admin
def admin_delete_testimonial(tid):
    conn = get_db()
    conn.execute("DELETE FROM testimonials WHERE id=?", (tid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_testimonials"))


# ─────────────────────────────────────────────
# ADMIN — SETTINGS
# ─────────────────────────────────────────────
@app.route("/admin/settings", methods=["GET", "POST"])
@require_admin
def admin_settings():
    conn = get_db()
    if request.method == "POST":
        keys = ["showreel_vimeo_id","showreel_thumbnail","hero_vimeo_id","ba_before_vimeo_id","ba_after_vimeo_id",
                "whatsapp_number","instagram_url","email","tagline",
                "stats_projects","stats_clients","stats_experience"]
        for k in keys:
            v = request.form.get(k, "").strip()
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now','localtime'))",
                (k, v))
        conn.commit()
        flash("Settings saved successfully!")
    settings = {r["key"]: r["value"] for r in conn.execute("SELECT key,value FROM settings").fetchall()}
    conn.close()
    return render_template("admin_settings.html", settings=settings)

# Initialize database for Render/Gunicorn
init_db()

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("🎬 FramesByMaddy running at http://localhost:5000")
    print("🔐 Admin panel at http://localhost:5000/admin")
    print("   Username: admin | Password: maddy2026")
    app.run(debug=True, port=5000)
