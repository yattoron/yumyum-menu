#!/usr/bin/env python3
"""
溱溱有味 · 美食手帳作品集
"""

import os
import json
import uuid
import cgi
import html
import secrets
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote, parse_qs
from http.cookies import SimpleCookie

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DATA_FILE = os.path.join(BASE_DIR, "data", "works.json")
MEMORIES_FILE = os.path.join(BASE_DIR, "data", "memories.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

ADMIN_PASSWORD = "66798961"
SESSIONS = {}

CATEGORIES = ["前菜", "伴菜", "主食", "湯類", "小菜", "甜品", "小食"]
COUNTRIES = ["日本", "韓國", "法國", "中國", "台灣", "香港", "意大利", "美國", "泰國", "西班牙", "威爾士", "印度", "Fusion"]

FLAG_EMOJI = {
    "日本": "🇯🇵", "韓國": "🇰🇷", "法國": "🇫🇷", "中國": "🇨🇳",
    "台灣": "🇹🇼", "香港": "🇭🇰", "意大利": "🇮🇹", "美國": "🇺🇸",
    "泰國": "🇹🇭", "西班牙": "🇪🇸", "威爾士": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "印度": "🇮🇳",
    "Fusion": "🔀"
}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

def load_works():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            works = json.load(f)
            for w in works:
                w.setdefault("steps", "")
                w.setdefault("likes", 0)
                w.setdefault("comments", [])
                w.setdefault("category", "主食")
                w.setdefault("tags", [])
                w.setdefault("country", "")
                w.setdefault("season", "")
                w.setdefault("description", "")
            return works
    except:
        return []

def save_works(works):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(works, f, ensure_ascii=False, indent=2)

def load_memories():
    if not os.path.exists(MEMORIES_FILE):
        return []
    try:
        with open(MEMORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_memories(memories):
    with open(MEMORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

def get_session_id(handler):
    cookie = SimpleCookie(handler.headers.get("Cookie", ""))
    if "sid" in cookie:
        sid = cookie["sid"].value
        if sid in SESSIONS:
            return sid
    return None

def create_session():
    sid = secrets.token_hex(16)
    SESSIONS[sid] = {"logged_in": True}
    return sid

def is_logged_in(handler):
    sid = get_session_id(handler)
    return sid is not None and SESSIONS.get(sid, {}).get("logged_in")

def render_index(works):
    with open(os.path.join(TEMPLATES_DIR, "index.html"), "r", encoding="utf-8") as f:
        tpl = f.read()
    cat_buttons = '<button class="filter-btn active" data-filter="all">全部</button>\n'
    for cat in CATEGORIES:
        cat_buttons += f'        <button class="filter-btn" data-filter="{html.escape(cat)}">{html.escape(cat)}</button>\n'
    if works:
        cards = []
        for w in works:
            steps = w.get("steps", "") or ""
            steps_attr = html.escape(steps).replace("\n", "&#10;")
            desc = w.get("description", "") or ""
            desc_attr = html.escape(desc).replace("\n", "&#10;")
            likes = w.get("likes", 0)
            category = w.get("category", "主食")
            tags = w.get("tags", [])
            tags_str = ",".join(tags)
            country = w.get("country", "")
            flag = FLAG_EMOJI.get(country, "")
            season = w.get("season", "") or ""
            season_list = [s.strip() for s in season.split(",") if s.strip()]
            season_emoji_map = {"春": "🌸", "夏": "☀️", "秋": "🍂", "冬": "❄️"}
            season_html = "".join(
                f'<div class="season-flag" style="position:absolute;top:{10+i*26}px;left:10px;width:22px;height:22px;font-size:0.7rem;border-radius:50%;background:rgba(255,254,249,0.92);display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(74,63,53,0.12);z-index:4;" title="{html.escape(s)}">{season_emoji_map.get(s,"")}</div>'
                for i, s in enumerate(season_list) if season_emoji_map.get(s)
            )
            card = f'''      <article class="work-card" data-id="{html.escape(w['id'])}" data-title="{html.escape(w['title'])}" data-src="/uploads/{html.escape(w['filename'])}" data-steps="{steps_attr}" data-description="{desc_attr}" data-category="{html.escape(category)}" data-tags="{html.escape(tags_str)}" data-country="{html.escape(country)}" data-season="{html.escape(season)}">
        <div class="work-image-wrap">
          <img src="/uploads/{html.escape(w['filename'])}" alt="{html.escape(w['title'])}" loading="lazy">
          <div class="country-flag" title="{html.escape(country)}">{flag}</div>
          {season_html}
        </div>
        <div class="work-info">
          <h2 class="work-title">{html.escape(w['title'])}</h2>
        </div>
        <div class="like-area">
          <button class="like-btn" data-id="{html.escape(w['id'])}" aria-label="喜歡">♡</button>
          <span class="like-count">{likes}</span>
        </div>
        <div class="comment-area" data-id="{html.escape(w['id'])}">
          <span class="comment-icon">💬</span>
          <span class="comment-count">{len(w.get('comments', []))}</span>
        </div>
      </article>'''
            cards.append(card)
        works_html = "\n".join(cards)
    else:
        works_html = '<div class="empty-state" style="grid-column: 1 / -1;"><p>還沒有菜色</p></div>'
    tpl = tpl.replace("<!-- FILTER_PLACEHOLDER -->", cat_buttons)
    return tpl.replace("<!-- WORKS_PLACEHOLDER -->", works_html)
def render_admin(works):
    return '''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>後台管理 · 溱溱有味</title>
  <link rel="stylesheet" href="/static/css/style.css">
  <style>
    .admin-menu { display: flex; gap: 1.5rem; justify-content: center; margin-top: 3rem; }
    .admin-menu a { display: block; padding: 2rem 3rem; background: #fffef9; border: 1px solid rgba(212,165,116,0.4); border-radius: 12px; text-decoration: none; color: #4a3f35; font-size: 1.2rem; box-shadow: 0 4px 12px rgba(74,63,53,0.08); }
    .admin-menu a:hover { transform: translateY(-2px); }
  </style>
</head>
<body>
  <div class="admin-dashboard">
    <div class="admin-header">
      <h1>後台管理</h1>
      <div class="admin-actions">
        <a href="/" target="_blank">查看前台</a>
        <a href="/admin/logout">登出</a>
      </div>
    </div>
    <div class="admin-menu">
      <a href="/admin/dishes">上傳菜色</a>
      <a href="/admin/memories">上傳 Memories</a>
    </div>
  </div>
</body>
</html>'''

def render_admin_login(error=None):
    with open(os.path.join(TEMPLATES_DIR, "admin_login.html"), "r", encoding="utf-8") as f:
        tpl = f.read()
    error_html = f'<div class="error-msg">{html.escape(error)}</div>' if error else ""
    return tpl.replace("<!-- ERROR_PLACEHOLDER -->", error_html)

def render_dishes_admin(works):
    count = str(len(works))
    if works:
        items = []
        for w in works:
            cat = w.get("category", "主食")
            country = w.get("country", "")
            item = f'''        <div class="work-item">
          <img src="/uploads/{html.escape(w['filename'])}" alt="{html.escape(w['title'])}">
          <div class="work-item-info">
            <div class="title">{html.escape(w['title'])} <span style="font-size:0.8rem;color:#999;">[{html.escape(cat)}]</span></div>
            <div class="date">{html.escape(w.get('created_at', ''))}</div>
          </div>
          <div style="display:flex;gap:0.5rem;">
            <a href="/admin/edit/{html.escape(w['id'])}" class="btn-delete" style="text-decoration:none;">編輯</a>
            <form method="POST" action="/admin/delete/{html.escape(w['id'])}" onsubmit="return confirm('確定刪除？');" style="margin:0;">
              <button type="submit" class="btn-delete">刪除</button>
            </form>
          </div>
        </div>'''
            items.append(item)
        list_html = '<div class="works-list">\n' + "\n".join(items) + '\n      </div>'
    else:
        list_html = '<div class="empty-state"><p>目前沒有菜色</p></div>'
    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <title>上傳菜色 · 後台</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <div class="admin-dashboard">
    <div class="admin-header">
      <h1>上傳菜色</h1>
      <div class="admin-actions">
        <a href="/admin/dashboard">← 返回</a>
        <a href="/admin/logout">登出</a>
      </div>
    </div>
    <section class="upload-section">
      <h2>上傳新菜色</h2>
      <form method="POST" action="/admin/upload" enctype="multipart/form-data">
        <div class="form-group">
          <label for="title">菜色名稱</label>
          <input type="text" id="title" name="title" required>
        </div>
        <div class="form-group">
          <label for="category">主分類</label>
          <select id="category" name="category" style="width:100%;padding:0.7rem;border:1px solid rgba(212,165,116,0.45);border-radius:4px;">
            {''.join(f'<option value="{c}">{c}</option>' for c in CATEGORIES)}
          </select>
        </div>
        <div class="form-group">
          <label for="country">國家</label>
          <select id="country" name="country" style="width:100%;padding:0.7rem;border:1px solid rgba(212,165,116,0.45);border-radius:4px;">
            {''.join(f'<option value="{c}">{c}</option>' for c in COUNTRIES)}
          </select>
        </div>
        <div class="form-group">
          <label>季節（可多選）</label>
          <div style="display:flex;gap:0.8rem;margin-top:0.4rem;">
            <label style="cursor:pointer;"><input type="checkbox" name="season" value="春" style="display:none;"><span style="font-size:1.5rem;" onclick="this.previousElementSibling.checked=!this.previousElementSibling.checked;this.style.opacity=this.previousElementSibling.checked?1:0.5;">🌸</span></label>
            <label style="cursor:pointer;"><input type="checkbox" name="season" value="夏" style="display:none;"><span style="font-size:1.5rem;" onclick="this.previousElementSibling.checked=!this.previousElementSibling.checked;this.style.opacity=this.previousElementSibling.checked?1:0.5;">☀️</span></label>
            <label style="cursor:pointer;"><input type="checkbox" name="season" value="秋" style="display:none;"><span style="font-size:1.5rem;" onclick="this.previousElementSibling.checked=!this.previousElementSibling.checked;this.style.opacity=this.previousElementSibling.checked?1:0.5;">🍂</span></label>
            <label style="cursor:pointer;"><input type="checkbox" name="season" value="冬" style="display:none;"><span style="font-size:1.5rem;" onclick="this.previousElementSibling.checked=!this.previousElementSibling.checked;this.style.opacity=this.previousElementSibling.checked?1:0.5;">❄️</span></label>
          </div>
        </div>
        <div class="form-group">
          <label for="description">菜色簡介</label>
          <textarea id="description" name="description" rows="3" style="width:100%;padding:0.7rem;border:1px solid rgba(212,165,116,0.45);border-radius:4px;"></textarea>
        </div>
        <div class="form-group">
          <label for="steps">煮食步驟</label>
          <textarea id="steps" name="steps" rows="6" style="width:100%;padding:0.7rem;border:1px solid rgba(212,165,116,0.45);border-radius:4px;"></textarea>
        </div>
        <div class="form-group">
          <label for="image">選擇圖片</label>
          <input type="file" id="image" name="image" accept="image/*" required>
        </div>
        <button type="submit" class="btn">上傳</button>
      </form>
    </section>
    <section style="margin-top:2rem;">
      <h2>已上傳菜色（{count}）</h2>
      {list_html}
    </section>
  </div>
</body>
</html>'''

def render_memories_admin(memories):
    count = str(len(memories))
    if memories:
        items = []
        for m in memories:
            item = f'''        <div class="work-item">
          <img src="/uploads/{html.escape(m['filename'])}" alt="" style="width:60px;height:60px;object-fit:cover;">
          <div class="work-item-info">
            <div class="title">{html.escape(m.get('created_at', ''))}</div>
            <div class="date">{html.escape(m.get('note', ''))}</div>
          </div>
          <div style="display:flex;gap:0.5rem;">
            <a href="/admin/edit-memory/{html.escape(m['id'])}" class="btn-delete" style="text-decoration:none;">編輯</a>
            <form method="POST" action="/admin/delete-memory/{html.escape(m['id'])}" onsubmit="return confirm('確定刪除？');" style="margin:0;">
              <button type="submit" class="btn-delete">刪除</button>
            </form>
          </div>
        </div>'''
            items.append(item)
        list_html = '<div class="works-list">\n' + "\n".join(items) + '\n      </div>'
    else:
        list_html = '<div class="empty-state"><p>目前沒有 Memories</p></div>'
    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <title>上傳 Memories · 後台</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <div class="admin-dashboard">
    <div class="admin-header">
      <h1>上傳 Memories</h1>
      <div class="admin-actions">
        <a href="/admin/dashboard">← 返回</a>
        <a href="/admin/logout">登出</a>
      </div>
    </div>
    <section class="upload-section">
      <h2>上傳新照片</h2>
      <form method="POST" action="/admin/upload-memory" enctype="multipart/form-data">
        <div class="form-group">
          <label for="memory-date">日期</label>
          <input type="text" id="memory-date" name="date" placeholder="例如：2026-11-20" style="width:100%;padding:0.7rem;border:1px solid rgba(212,165,116,0.45);border-radius:4px;">
        </div>
        <div class="form-group">
          <label for="memory-note">照片資訊</label>
          <input type="text" id="memory-note" name="note" placeholder="一句話描述" style="width:100%;padding:0.7rem;border:1px solid rgba(212,165,116,0.45);border-radius:4px;">
        </div>
        <div class="form-group">
          <label for="memory-image">選擇照片</label>
          <input type="file" id="memory-image" name="image" accept="image/*" required>
        </div>
        <button type="submit" class="btn">上傳</button>
      </form>
    </section>
    <section style="margin-top:2rem;">
      <h2>已上傳 Memories（{count}）</h2>
      {list_html}
    </section>
  </div>
</body>
</html>'''

class PortfolioHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def send_html(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_redirect(self, location, set_cookie=None):
        self.send_response(302)
        self.send_header("Location", location)
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()

    def send_file(self, path, content_type=None):
        if not os.path.exists(path):
            self.send_error(404)
            return
        with open(path, "rb") as f:
            data = f.read()
        if not content_type:
            ext = os.path.splitext(path)[1].lower()
            types = {".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
            content_type = types.get(ext, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/" or path == "/index.html":
            with open(os.path.join(TEMPLATES_DIR, "home.html"), "r", encoding="utf-8") as f:
                self.send_html(f.read())
            return

        if path == "/menu":
            works = load_works()
            works = sorted(works, key=lambda x: x.get("likes", 0), reverse=True)
            self.send_html(render_index(works))
            return

        if path == "/about":
            with open(os.path.join(TEMPLATES_DIR, "about.html"), "r", encoding="utf-8") as f:
                self.send_html(f.read())
            return

        if path == "/memories":
            memories = load_memories()
            memories = sorted(memories, key=lambda x: x.get("created_at", ""))
            with open(os.path.join(TEMPLATES_DIR, "memories.html"), "r", encoding="utf-8") as f:
                tpl = f.read()
            if memories:
                photos = []
                for i, m in enumerate(memories):
                    rot = (i % 5 - 2) * 2
                    photo = f'<div class="polaroid" style="--rot:{rot}deg;" data-src="/uploads/{html.escape(m["filename"])}" data-date="{html.escape(m.get("created_at", ""))}" data-note="{html.escape(m.get("note", ""))}"><div class="clip"></div><img src="/uploads/{html.escape(m["filename"])}" alt=""></div>'
                    photos.append(photo)
                photos_html = "\n".join(photos)
            else:
                photos_html = '<div class="empty-msg">還沒有回憶</div>'
            self.send_html(tpl.replace("<!-- PHOTOS_PLACEHOLDER -->", photos_html))
            return

        if path == "/admin":
            if is_logged_in(self):
                self.send_redirect("/admin/dashboard")
            else:
                self.send_html(render_admin_login())
            return

        if path == "/admin/dashboard":
            if not is_logged_in(self):
                self.send_redirect("/admin")
                return
            works = load_works()
            works = sorted(works, key=lambda x: x.get("created_at", ""), reverse=True)
            self.send_html(render_admin(works))
            return        
        if path == "/admin/dishes":
            if not is_logged_in(self):
                self.send_redirect("/admin")
                return
            works = load_works()
            works = sorted(works, key=lambda x: x.get("created_at", ""), reverse=True)
            self.send_html(render_dishes_admin(works))
            return

        if path == "/admin/memories":
            if not is_logged_in(self):
                self.send_redirect("/admin")
                return
            memories = load_memories()
            memories = sorted(memories, key=lambda x: x.get("created_at", ""), reverse=True)
            self.send_html(render_memories_admin(memories))
            return


        if path.startswith("/admin/edit-memory/"):
            if not is_logged_in(self):
                self.send_redirect("/admin")
                return
            mem_id = path.split("/")[-1]
            memories = load_memories()
            mem = None
            for m in memories:
                if m.get("id") == mem_id:
                    mem = m
                    break
            if not mem:
                self.send_redirect("/admin/dashboard")
                return
            html_content = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <title>編輯 Memories</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <div class="admin-dashboard">
    <div class="admin-header">
      <h1>編輯 Memories</h1>
      <a href="/admin/dashboard">← 返回</a>
    </div>
    <section class="upload-section">
      <form method="POST" action="/admin/edit-memory/{html.escape(mem['id'])}">
        <div class="form-group">
          <img src="/uploads/{html.escape(mem['filename'])}" style="max-width:200px;">
        </div>
        <div class="form-group">
          <label>日期</label>
          <input type="text" name="date" value="{html.escape(mem.get('created_at', ''))}" style="width:100%;padding:0.7rem;border:1px solid #ccc;border-radius:4px;">
        </div>
        <div class="form-group">
          <label>照片資訊</label>
          <input type="text" name="note" value="{html.escape(mem.get('note', ''))}" style="width:100%;padding:0.7rem;border:1px solid #ccc;border-radius:4px;">
        </div>
        <button type="submit" class="btn">儲存</button>
      </form>
    </section>
  </div>
</body>
</html>'''
            self.send_html(html_content)
            return

        if path.startswith("/admin/edit/"):
            if not is_logged_in(self):
                self.send_redirect("/admin")
                return
            work_id = path.split("/")[-1]
            works = load_works()
            work = None
            for w in works:
                if w.get("id") == work_id:
                    work = w
                    break
            if not work:
                self.send_redirect("/admin/dashboard")
                return
            self.send_html("<h1>編輯菜色</h1><p>功能開發中</p><a href='/admin/dashboard'>返回</a>")
            return

        if path == "/admin/logout":
            sid = get_session_id(self)
            if sid and sid in SESSIONS:
                del SESSIONS[sid]
            self.send_redirect("/admin", set_cookie="sid=; Path=/; Max-Age=0")
            return

        if path.startswith("/uploads/"):
            filename = os.path.basename(path)
            filepath = os.path.join(UPLOAD_DIR, filename)
            self.send_file(filepath)
            return

        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            filepath = os.path.join(STATIC_DIR, rel)
            self.send_file(filepath)
            return

        if path.startswith("/like/"):
            work_id = path.split("/")[-1]
            works = load_works()
            for w in works:
                if w.get("id") == work_id:
                    self.send_json({"likes": w.get("likes", 0)})
                    return
            self.send_json({"likes": 0}, 404)
            return

        if path.startswith("/comments/"):
            work_id = path.split("/")[-1]
            works = load_works()
            for w in works:
                if w.get("id") == work_id:
                    self.send_json({"comments": w.get("comments", [])})
                    return
            self.send_json({"comments": []}, 404)
            return

        self.send_error(404)

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = unquote(parsed.path)

            if path == "/admin":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                params = parse_qs(body)
                password = params.get("password", [""])[0]
                if password == ADMIN_PASSWORD:
                    sid = create_session()
                    self.send_redirect("/admin/dashboard", set_cookie=f"sid={sid}; Path=/; HttpOnly")
                else:
                    self.send_html(render_admin_login("密碼錯誤"))
                return

            if path == "/admin/upload-memory":
                if not is_logged_in(self):
                    self.send_redirect("/admin")
                    return
                content_type = self.headers.get("Content-Type", "")
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type})
                if "image" not in form:
                    self.send_redirect("/admin/dashboard")
                    return
                file_item = form["image"]
                filename = getattr(file_item, "filename", None)
                if not filename:
                    self.send_redirect("/admin/dashboard")
                    return
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_EXT:
                    self.send_redirect("/admin/dashboard")
                    return
                new_filename = f"mem_{uuid.uuid4().hex[:8]}{ext}"
                filepath = os.path.join(UPLOAD_DIR, new_filename)
                with open(filepath, "wb") as f:
                    f.write(file_item.file.read())
                memories = load_memories()
                mem_date = (form.getvalue("date") or "").strip() if "date" in form else datetime.now().strftime("%Y-%m-%d")
                mem_note = (form.getvalue("note") or "").strip() if "note" in form else ""
                memories.append({"id": str(uuid.uuid4())[:8], "filename": new_filename, "created_at": mem_date, "note": mem_note})
                save_memories(memories)
                print(f"上傳 Memories：{new_filename}")
                self.send_redirect("/admin/dashboard")
                return

            if path.startswith("/admin/edit-memory/"):
                if not is_logged_in(self):
                    self.send_redirect("/admin")
                    return
                mem_id = path.split("/")[-1]
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                params = parse_qs(body)
                new_date = params.get("date", [""])[0].strip()
                new_note = params.get("note", [""])[0].strip()
                memories = load_memories()
                for m in memories:
                    if m.get("id") == mem_id:
                        if new_date:
                            m["created_at"] = new_date
                        m["note"] = new_note
                        break
                save_memories(memories)
                self.send_redirect("/admin/dashboard")
                return

            if path.startswith("/admin/delete-memory/"):
                if not is_logged_in(self):
                    self.send_redirect("/admin")
                    return
                mem_id = path.split("/")[-1]
                memories = load_memories()
                new_memories = []
                for m in memories:
                    if m.get("id") == mem_id:
                        fp = os.path.join(UPLOAD_DIR, m.get("filename", ""))
                        if os.path.exists(fp):
                            os.remove(fp)
                    else:
                        new_memories.append(m)
                save_memories(new_memories)
                self.send_redirect("/admin/dashboard")
                return

            if path == "/admin/upload":
                if not is_logged_in(self):
                    self.send_redirect("/admin")
                    return
                content_type = self.headers.get("Content-Type", "")
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type})
                title = (form.getvalue("title") or "").strip() if "title" in form else ""
                if not title or "image" not in form:
                    self.send_redirect("/admin/dashboard")
                    return
                file_item = form["image"]
                filename = getattr(file_item, "filename", None)
                if not filename:
                    self.send_redirect("/admin/dashboard")
                    return
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_EXT:
                    self.send_redirect("/admin/dashboard")
                    return
                new_filename = f"{uuid.uuid4().hex[:8]}{ext}"
                filepath = os.path.join(UPLOAD_DIR, new_filename)
                with open(filepath, "wb") as f:
                    f.write(file_item.file.read())
                steps = (form.getvalue("steps") or "").strip() if "steps" in form else ""
                description = (form.getvalue("description") or "").strip() if "description" in form else ""
                category = (form.getvalue("category") or "主食").strip() if "category" in form else "主食"
                country = (form.getvalue("country") or "").strip() if "country" in form else ""
                seasons = form.getlist("season") if hasattr(form, "getlist") else []
                season = ",".join(seasons) if isinstance(seasons, list) else ""
                works = load_works()
                works.append({"id": str(uuid.uuid4())[:8], "title": title, "filename": new_filename, "created_at": datetime.now().strftime("%Y-%m-%d"), "steps": steps, "likes": 0, "comments": [], "category": category, "tags": [], "country": country, "season": season, "description": description})
                save_works(works)
                print(f"上傳菜色：{title}")
                self.send_redirect("/admin/dashboard")
                return

            if path.startswith("/admin/delete/"):
                if not is_logged_in(self):
                    self.send_redirect("/admin")
                    return
                work_id = path.split("/")[-1]
                works = load_works()
                new_works = []
                for w in works:
                    if w.get("id") == work_id:
                        fp = os.path.join(UPLOAD_DIR, w.get("filename", ""))
                        if os.path.exists(fp):
                            os.remove(fp)
                    else:
                        new_works.append(w)
                save_works(new_works)
                self.send_redirect("/admin/dashboard")
                return

            if path.startswith("/like/"):
                work_id = path.split("/")[-1]
                works = load_works()
                for w in works:
                    if w.get("id") == work_id:
                        w["likes"] = w.get("likes", 0) + 1
                        save_works(works)
                        self.send_json({"success": True, "likes": w["likes"]})
                        return
                self.send_json({"success": False}, 404)
                return

            if path.startswith("/comment/"):
                work_id = path.split("/")[-1]
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                params = parse_qs(body)
                name = params.get("name", [""])[0].strip() or "匿名"
                text = params.get("text", [""])[0].strip()
                if not text:
                    self.send_json({"success": False}, 400)
                    return
                works = load_works()
                for w in works:
                    if w.get("id") == work_id:
                        comment = {"id": str(uuid.uuid4())[:8], "name": name, "text": text, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
                        w.setdefault("comments", []).append(comment)
                        save_works(works)
                        self.send_json({"success": True, "comments": w["comments"]})
                        return
                self.send_json({"success": False}, 404)
                return

            self.send_error(404)
        except Exception as e:
            print(f"POST Error: {e}")
            self.send_error(500)

def main():
    print("=" * 40)
    print("  溱溱有味 · 美食手帳")
    print("=" * 40)
    print(f"前台： http://127.0.0.1:{PORT}/")
    print(f"後台： http://127.0.0.1:{PORT}/admin")
    print(f"密碼： {ADMIN_PASSWORD}")
    print("按 Ctrl+C 停止")
    print("=" * 40)
    server = HTTPServer(("0.0.0.0", PORT), PortfolioHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止")
        server.server_close()

if __name__ == "__main__":
    main()

