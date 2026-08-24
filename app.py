#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COLDWELL BANKER VIP - CLOUD MEDIA STREAMING SYSTEM (FOLDER 3)
Zero permission walls, zero Google login prompts, HTTP 206 fast video streaming
Folder: c:/Users/USER/Desktop/3
"""

import json
import os
import re
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from flask import Flask, send_file, send_from_directory, request, jsonify, Response, redirect

try:
    import requests as _requests
except ImportError:
    _requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# ─── CONFIG (P15: config.json ile taşınabilirlik, ENV override) ───
BASE_DIR = Path(__file__).parent

_CONFIG_DEFAULTS = {
    "host": "0.0.0.0",
    "port": 5002,
    "projeler_dir": str(BASE_DIR / "projeler"),
    "cb_listings_url": "https://www.cb.com.tr/ilanlar?officeid=470&officeuserid=17983",
    "log_dir": "logs",
    "telemetry_file": "logs/telemetry.jsonl",
    "chat_rate_limit_per_min": 12,
}
CONFIG_FILE = BASE_DIR / "config.json"


def _load_config():
    cfg = dict(_CONFIG_DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    for env_key, cfg_key in (("PORT", "port"), ("NEXA_PORT", "port"), ("NEXA_PROJELER_DIR", "projeler_dir"),
                             ("NEXA_HOST", "host"), ("NEXA_CB_URL", "cb_listings_url")):
        val = os.getenv(env_key)
        if val:
            if cfg_key == "port":
                val = int(val)
            cfg[cfg_key] = val
    if not CONFIG_FILE.exists():
        try:
            CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    return cfg


CFG = _load_config()

# ─── LOGGING (P16: döngüsel dosya logu) ───
LOG_DIR = BASE_DIR / CFG["log_dir"]
LOG_DIR.mkdir(exist_ok=True)
_log_handler = RotatingFileHandler(LOG_DIR / "app.log", maxBytes=5 * 1024 * 1024,
                                   backupCount=3, encoding="utf-8")
_log_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s [%(name)s] %(message)s"))
logging.basicConfig(level=logging.INFO,
                    handlers=[_log_handler, logging.StreamHandler()])
logger = logging.getLogger("nexa.app")

# ─── TELEMETRİ (E6: JSONL kaydı) ───
_telemetry_lock = threading.Lock()


_TELEMETRY_MAX_BYTES = 10 * 1024 * 1024


def telemetry(event: dict):
    try:
        line = json.dumps({"ts": datetime.now().isoformat(), **event}, ensure_ascii=False)
        with _telemetry_lock:
            tele_file = BASE_DIR / CFG["telemetry_file"]
            # O3: 10 MB üzeri JSONL'i .1'e rotate et, yenisini başlat
            if tele_file.exists() and tele_file.stat().st_size > _TELEMETRY_MAX_BYTES:
                try:
                    tele_file.replace(tele_file.with_suffix(".jsonl.1"))
                except OSError:
                    pass
            with open(tele_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass

from nexa_ai_engine import process_nexa_query, extract_keywords_and_projects
from nexa_rag import (cognitive_chat, _find_project_by_name, DOCS_DIR as NEXA_DOCS_DIR,
                      DB_PATH as NEXA_DB_PATH, generate_all_project_summaries,
                      get_project_summary)

# After db connection setup, add safe migration:
def _migrate_db(db_path):
    """Add missing tables, columns, and indexes safely with WAL mode."""
    import sqlite3
    import logging
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.execute("PRAGMA foreign_keys=ON;")
        cur = conn.cursor()
        
        # Ensure core tables exist before migrating
        cur.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255), title TEXT)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                name VARCHAR(255),
                phone VARCHAR(20),
                email VARCHAR(255),
                interested_units TEXT,
                notes TEXT,
                created_at TIMESTAMP,
                last_contact TIMESTAMP,
                stage VARCHAR(50) DEFAULT 'lead',
                budget VARCHAR(100),
                assigned_agent VARCHAR(100),
                firebase_synced INTEGER DEFAULT 0,
                UNIQUE(project_id, phone)
            )
        """)
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_proj_phone ON customers(project_id, phone)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                doc_type VARCHAR(50),
                title VARCHAR(255),
                content TEXT,
                file_url VARCHAR(500),
                category VARCHAR(100),
                created_at TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50),
                entity_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                user_or_agent VARCHAR(100),
                details TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                chunk_text TEXT,
                embedding TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                unit_type VARCHAR(50),
                area_m2 FLOAT,
                price FLOAT,
                available_count INTEGER,
                plan_url VARCHAR(500),
                images TEXT,
                delivery_date VARCHAR(100)
            )
        """)
        
        existing = {r[1] for r in cur.execute("PRAGMA table_info(projects)").fetchall()}
        migrations = [
            ("name", "ALTER TABLE projects ADD COLUMN name VARCHAR(255)"),
            ("location", "ALTER TABLE projects ADD COLUMN location VARCHAR(255)"),
            ("description", "ALTER TABLE projects ADD COLUMN description TEXT"),
            ("cover_image_url", "ALTER TABLE projects ADD COLUMN cover_image_url VARCHAR(500)"),
            ("lat", "ALTER TABLE projects ADD COLUMN lat FLOAT"),
            ("lng", "ALTER TABLE projects ADD COLUMN lng FLOAT"),
            ("ada_no", "ALTER TABLE projects ADD COLUMN ada_no VARCHAR(50)"),
            ("parsel_no", "ALTER TABLE projects ADD COLUMN parsel_no VARCHAR(50)"),
            ("tkgm_verified", "ALTER TABLE projects ADD COLUMN tkgm_verified INTEGER DEFAULT 0"),
            ("created_at", "ALTER TABLE projects ADD COLUMN created_at TIMESTAMP"),
            ("il", "ALTER TABLE projects ADD COLUMN il VARCHAR(100)"),
            ("ilce", "ALTER TABLE projects ADD COLUMN ilce VARCHAR(100)"),
            ("mahalle", "ALTER TABLE projects ADD COLUMN mahalle VARCHAR(100)"),
            ("location_accuracy_score", "ALTER TABLE projects ADD COLUMN location_accuracy_score INTEGER DEFAULT 0"),
            ("location_status", "ALTER TABLE projects ADD COLUMN location_status VARCHAR(50)"),
            ("location_source", "ALTER TABLE projects ADD COLUMN location_source VARCHAR(255)"),
            ("reverse_geocoded_address", "ALTER TABLE projects ADD COLUMN reverse_geocoded_address TEXT"),
            ("is_portfolio", "ALTER TABLE projects ADD COLUMN is_portfolio INTEGER DEFAULT 0"),
            ("listing_type", "ALTER TABLE projects ADD COLUMN listing_type VARCHAR(50)"),
            ("property_category", "ALTER TABLE projects ADD COLUMN property_category VARCHAR(100)"),
            ("price_display", "ALTER TABLE projects ADD COLUMN price_display VARCHAR(100)"),
            ("room_info", "ALTER TABLE projects ADD COLUMN room_info VARCHAR(50)"),
            ("net_gross_area", "ALTER TABLE projects ADD COLUMN net_gross_area VARCHAR(100)"),
            ("cb_ilan_no", "ALTER TABLE projects ADD COLUMN cb_ilan_no VARCHAR(50)"),
            ("cb_url", "ALTER TABLE projects ADD COLUMN cb_url VARCHAR(500)"),
            ("cb_last_synced", "ALTER TABLE projects ADD COLUMN cb_last_synced TIMESTAMP"),
            ("featured", "ALTER TABLE projects ADD COLUMN featured INTEGER DEFAULT 0"),
            ("display_order", "ALTER TABLE projects ADD COLUMN display_order INTEGER DEFAULT 0"),
            ("price_numeric", "ALTER TABLE projects ADD COLUMN price_numeric INTEGER"),
            ("price_min", "ALTER TABLE projects ADD COLUMN price_min INTEGER"),
            ("price_max", "ALTER TABLE projects ADD COLUMN price_max INTEGER"),
            ("down_payment", "ALTER TABLE projects ADD COLUMN down_payment VARCHAR(100)"),
            ("installment_terms", "ALTER TABLE projects ADD COLUMN installment_terms VARCHAR(255)"),
            ("monthly_installment", "ALTER TABLE projects ADD COLUMN monthly_installment INTEGER"),
            ("delivery_months", "ALTER TABLE projects ADD COLUMN delivery_months INTEGER"),
        ]
        for col, sql in migrations:
            if col not in existing:
                try:
                    cur.execute(sql)
                    logging.getLogger('nexa.app').info(f"Migration: added column '{col}' to projects")
                except Exception as e:
                    logging.getLogger('nexa.app').warning(f"Migration skip: {col}: {e}")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_projects_is_portfolio ON projects(is_portfolio)",
            "CREATE INDEX IF NOT EXISTS idx_projects_name_nocase ON projects(name COLLATE NOCASE)",
            "CREATE INDEX IF NOT EXISTS idx_projects_location ON projects(location)",
            "CREATE INDEX IF NOT EXISTS idx_projects_price_num ON projects(price_numeric)",
            "CREATE INDEX IF NOT EXISTS idx_projects_cb_url ON projects(cb_url)",
            "CREATE INDEX IF NOT EXISTS idx_projects_cb_ilan_no ON projects(cb_ilan_no)",
            "CREATE INDEX IF NOT EXISTS idx_customers_project_id ON customers(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_stage ON customers(stage)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_event ON audit_logs(event_type)",
        ]
        for idx_sql in indexes:
            try:
                cur.execute(idx_sql)
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception as e:
        logging.getLogger('nexa.app').warning(f"Migration error: {e}")

_migrate_db(NEXA_DB_PATH)

# ─── SETUP ───
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
_chat_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="nexa_chat")
PROJELER_DIR = Path(CFG["projeler_dir"])
STATIC_DIR = BASE_DIR / "static"
JSON_FILE = BASE_DIR / "projects_map.json"

try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

STATIC_DIR.mkdir(exist_ok=True)

# ─── ORIGIN VALIDATION (CSRF Protection for POST/PUT) ───
@app.before_request
def _validate_origin():
    if request.method in ("POST", "PUT", "DELETE") and request.path.startswith("/api/"):
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        host = request.headers.get("Host")
        # Allow requests if origin matches host, localhost, or is absent in non-browser API callers
        if origin and host:
            clean_host = host.split(":")[0].lower()
            import urllib.parse
            origin_host = urllib.parse.urlparse(origin).hostname or ""
            if origin_host not in (clean_host, "localhost", "127.0.0.1", "0.0.0.0"):
                logger.warning("CSRF/Origin reject: origin=%s != host=%s", origin, host)
                return jsonify({"success": False, "message": "Cross-origin request rejected"}), 403

# ─── CHAT RATE LIMIT (production koruması) ───
_rate_lock = threading.Lock()
_rate_hits = {}
_last_rate_cleanup = 0.0


def _get_client_ip():
    """Proxy ve CDN (Render, Cloudflare) arkasında doğru istemci IP adresini döner."""
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip.strip()
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
        return ips[-1] if ips else (request.remote_addr or "0.0.0.0")
    return request.remote_addr or "0.0.0.0"


def _check_rate_limit(ip=None):
    global _last_rate_cleanup
    if ip is None:
        ip = _get_client_ip()
    now = time.time()
    with _rate_lock:
        # Amortized periodic cleanup every 60s
        if now - _last_rate_cleanup > 60:
            for old_ip in [k for k, ts_list in list(_rate_hits.items())
                           if not ts_list or now - ts_list[-1] >= 60]:
                _rate_hits.pop(old_ip, None)
            _last_rate_cleanup = now
        hits = [t for t in _rate_hits.get(ip, []) if now - t < 60]
        if len(hits) >= int(CFG.get("chat_rate_limit_per_min", 12)):
            return False
        hits.append(now)
        _rate_hits[ip] = hits
    return True


# ─── CB LISTINGS SCRAPER ───
CB_LISTINGS_URL = CFG["cb_listings_url"]
CB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_listings_cache = {"data": [], "ts": 0.0}
_listings_lock = threading.Lock()

def fetch_cb_listings() -> list:
    """CB ilanları — Susanne Tenekecioğlu (config'deki cb_listings_url).

    Önce JSON-LD (schema.org ItemList) ayrıştırılır; sonuç yoksa HTML kart
    seçicileri denenir (eski yapı). Sonuç yine yoksa boş liste döner.
    """
    if _requests is None:
        return []
    try:
        response = _requests.get(CB_LISTINGS_URL, headers=CB_HEADERS, timeout=15)
        if response.status_code != 200:
            return []
        text = response.text
        listings = []

        # 1) JSON-LD ItemList
        for script in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            try:
                data = json.loads(script)
                items = data if isinstance(data, list) else data.get("@graph", [data])
                for it in items:
                    if not (isinstance(it, dict) and it.get("@type") == "ItemList"):
                        continue
                    for el in it.get("itemListElement", []):
                        p = el.get("item", {}) if isinstance(el, dict) else {}
                        if not isinstance(p, dict):
                            continue
                        link = (p.get("@id") or "").strip()
                        if not link:
                            continue
                        offers = p.get("offers") or {}
                        listings.append({
                            "title": re.sub(r"\s+", " ", (p.get("name") or "")).strip(),
                            "price": (offers.get("price") or "") if isinstance(offers, dict) else "",
                            "img": "https://via.placeholder.com/400x300",
                            "link": link,
                        })
            except Exception:
                continue
        if listings:
            return listings

        # 2) HTML kart fallback (eski yapı)
        if BeautifulSoup is not None:
            soup = BeautifulSoup(text, "html.parser")
            cards = soup.select(".card.locationDiv") or soup.select(".cb-list-item")
            for card in cards:
                try:
                    title_el = card.select_one(".cb-list-item-info h2") or card.select_one(".card-title")
                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title:
                        continue
                    price_el = card.select_one(".feature-item .text-primary") or card.select_one("span.h5.text-primary")
                    price = price_el.get_text(strip=True) if price_el else ""
                    link_el = card.select_one(".cb-list-img-container a") or card.select_one("a.title")
                    link = link_el["href"] if link_el else "#"
                    if link and not link.startswith("http"):
                        link = "https://www.cb.com.tr" + link
                    img_el = card.select_one(".cb-list-img-container img") or card.select_one("img.card-img-top")
                    img_url = img_el.get("src") if img_el else "https://via.placeholder.com/400x300"
                    listings.append({"title": title, "price": price, "img": img_url, "link": link})
                except Exception:
                    continue
        return listings
    except Exception:
        return []


def _db_portfolio_listings() -> list:
    """NEXA PRIME DB'deki canlı portföy ilanları (is_portfolio=1).

    Susanne'in CB sync'i (NEXA PRIME tarafında her 15 dk'da bir) bu tabloyu
    günceller; site buradan güncel envanteri otonom okur.
    """
    try:
        import sqlite3
        db_uri = f"file:{Path(NEXA_DB_PATH).resolve().as_posix()}?mode=ro"
        db = sqlite3.connect(db_uri, uri=True)
        try:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT * FROM projects WHERE COALESCE(is_portfolio,0)=1 ORDER BY id DESC"
            ).fetchall()
        finally:
            db.close()
        out = []
        for r in rows:
            p = dict(r)
            img = p.get("cover_image_url") or "/static/img/placeholder.jpg"
            loc = " / ".join(x for x in [p.get("il"), p.get("ilce"), p.get("mahalle")] if x)
            out.append({
                "id": p.get("id"),
                "title": p.get("name"),
                "price": p.get("price_display") or "",
                "price_display": p.get("price_display") or "",
                "img": img,
                "link": p.get("cb_url") or "#",
                "type": p.get("listing_type") or "Satılık",
                "loc": loc,
                "rooms": p.get("room_info") or "",
                "area": p.get("net_gross_area") or "",
                "cb_url": p.get("cb_url") or "",
                "source": "nexa_db",
            })
        return out
    except Exception:
        return []

_listings_refresh_lock = threading.Lock()

def _refresh_cb_listings_bg():
    def _run():
        with _listings_refresh_lock:
            if time.time() - _listings_cache["ts"] < 300:
                return
            try:
                data = fetch_cb_listings()
                with _listings_lock:
                    _listings_cache["data"] = data
                    _listings_cache["ts"] = time.time()
            except Exception:
                pass
    threading.Thread(target=_run, daemon=True).start()

@app.route("/api/listings", methods=["GET"])
def api_listings():
    now = time.time()
    if now - _listings_cache["ts"] >= 300:
        _refresh_cb_listings_bg()

    # 1) NEXA PRIME DB'deki canlı portföy ilanları (Susanne sync'i dahil)
    db_data = _db_portfolio_listings()
    if db_data:
        return jsonify({"success": True, "data": db_data, "source": "nexa_db"})

    # 2) CB canlı scrape cache
    data = _listings_cache["data"]
    if data:
        return jsonify({"success": True, "data": data, "source": "cb_live"})

    # 3) Yerel portföy ilan envanteri (son çare)
    try:
        pf = BASE_DIR / "nexa_portfolio_data.json"
        if pf.exists():
            pool = json.loads(pf.read_text(encoding="utf-8"))
            pool = pool if isinstance(pool, list) else pool.get("projects", [])
            data = [{
                "id": it.get("id"),
                "title": it.get("title"),
                "price": it.get("price_display") or "",
                "price_display": it.get("price_display") or "",
                "img": "/static/img/placeholder.jpg",
                "link": "#",
                "type": it.get("listing_type") or "Satılık",
                "loc": (it.get("mahalle") or it.get("ilce") or ""),
                "rooms": it.get("room_info") or "",
                "area": it.get("net_gross_area") or "",
            } for it in pool if it.get("type") == "portfolio"]
    except Exception:
        data = []
    return jsonify({"success": True, "data": data, "source": "local_json"})

@app.route("/api/projects", methods=["GET"])
def api_projects():
    projects = get_all_projects_ordered(include_hidden=False)
    resp = jsonify({"success": True, "data": projects})
    resp.headers["Cache-Control"] = "public, max-age=300"
    return resp

@app.route("/api/nexa-ai-chat", methods=["POST"])
@app.route("/api/chat", methods=["POST"])
def api_nexa_ai_chat():
    client_ip = _get_client_ip()
    if not _check_rate_limit(client_ip):
        telemetry({"event": "rate_limited", "ip": client_ip})
        return jsonify({"success": False,
                        "response": "Çok hızlı soru gönderiyorsunuz. Lütfen birkaç saniye bekleyip tekrar deneyin."}), 429

    data = request.get_json(silent=True) or {}
    raw_msg = data.get("message")
    message = raw_msg.strip() if isinstance(raw_msg, str) else ""
    if not message:
        return jsonify({"success": False, "response": "Lütfen bir soru yazın."}), 400
    if len(message) > 2000:
        message = message[:2000]
    
    history = data.get("history") or []
    if not isinstance(history, list):
        history = []
    elif len(history) > 20:
        history = history[-20:]

    t0 = time.time()
    try:
        result = process_nexa_query(message)
    except Exception as e:
        logger.exception("process_nexa_query hatasi")
        telemetry({"event": "engine_error", "ip": client_ip, "err": str(e)[:200]})
        return jsonify({"success": False,
                        "response": "Sistem kısa süreliğine meşgul. Lütfen bir dakika sonra tekrar deneyin."}), 500
    cards = result.get("projects", [])
    mode = "heuristic"

    # Randevu talebi veya saf selamlama ise anında doğrulanmış yanıtı dön
    ql = message.lower()
    if any(w in ql for w in ["randevu", "arama", "görüşme", "gorusme", "ulas", "ulaş", "telefon", "numara", "gsm"]) and result.get("lead_score", 0) >= 8:
        payload = {
            "success": True,
            "response": result.get("response"),
            "projects": [],
            "lead_score": 9,
            "mode": "appointment-direct",
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
        return jsonify(payload)

    project = None
    try:
        named = extract_keywords_and_projects(message)
        if len(named) == 1:
            project = _find_project_by_name(named[0])
    except Exception:
        project = None

    try:
        rag_reply = None
        try:
            future = _chat_executor.submit(cognitive_chat, message, project=project, history=history)
            rag_reply = future.result(timeout=25.0)
        except Exception:
            rag_reply = None
        if rag_reply:
            mode = "cognitive-rag"
            payload = {
                "success": True,
                "response": rag_reply,
                "projects": cards,
                "lead_score": result.get("lead_score", 3),
                "mode": mode,
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
            telemetry({"event": "chat", "ip": client_ip, "mode": mode,
                       "msg": message[:120], "projects": [c.get("title") for c in cards],
                       "elapsed_ms": payload["elapsed_ms"]})
            return jsonify(payload)
    except Exception as e:
        logger.warning("cognitive_chat zaman aşımı veya hata (%s) — anında nexa engine yanıtına düşülüyor", e)

    payload = {
        "success": True,
        "response": result.get("response", "Nexa AI Analizi tamamlandı."),
        "projects": cards,
        "lead_score": result.get("lead_score", 3),
        "mode": mode,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }
    telemetry({"event": "chat", "ip": client_ip, "mode": mode,
               "msg": message[:120], "projects": [c.get("title") for c in cards],
               "elapsed_ms": payload["elapsed_ms"]})
    return jsonify(payload)


@app.route("/api/track", methods=["POST"])
def api_track():
    """Frontend olay telemetrisi: proje kartı tıklama, WhatsApp tıklama, lead formu."""
    data = request.get_json(silent=True) or {}
    ev = data.get("event") or "click"
    telemetry({"event": f"ui_{ev}", "ip": request.remote_addr or "?",
               "project": data.get("project") or "",
               "target": data.get("target") or "",
               "extra": (data.get("extra") or {}) if isinstance(data.get("extra"), dict) else {}})
    return jsonify({"success": True})


@app.route("/api/appointments", methods=["GET", "POST"])
def api_appointments():
    """Online randevu ve lead kayıt endpointi."""
    if request.method == "GET":
        return jsonify({"success": True, "message": "Randevu kayıt servisi aktif (POST ile kayıt yapabilirsiniz)."})
    if not _check_rate_limit():
        return jsonify({"success": False, "message": "Çok fazla istek. Lütfen biraz bekleyin."}), 429
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()
    phone = str(data.get("phone") or "").strip()
    email = str(data.get("email") or "").strip()
    preferred_dt = str(data.get("preferred_datetime") or "").strip()
    project_id = data.get("project_id") or ""
    project_name = str(data.get("project_name") or "").strip()
    notes = str(data.get("notes") or "").strip()
    agent = str(data.get("agent") or "Suzanne Tenekecioğlu").strip()

    if not name or not phone:
        return jsonify({"success": False, "message": "Ad ve telefon alanları zorunludur."}), 400

    full_notes = f"Proje: {project_name} (ID: {project_id}) | Tercih: {preferred_dt} | Danışman: {agent} | Not: {notes}".strip()
    try:
        import sqlite3
        conn = sqlite3.connect(str(NEXA_DB_PATH), timeout=15.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO customers (project_id, name, phone, email, notes, stage, assigned_agent, created_at)
                VALUES (?, ?, ?, ?, ?, 'appointment', ?, datetime('now'))
                ON CONFLICT(project_id, phone) DO UPDATE SET
                    notes = excluded.notes,
                    email = coalesce(excluded.email, customers.email),
                    assigned_agent = coalesce(excluded.assigned_agent, customers.assigned_agent),
                    stage = 'appointment'
            """, (str(project_id) if project_id else None, name, phone, email or None, full_notes, agent))
            conn.commit()
            lead_id = cur.lastrowid
        finally:
            conn.close()

        telemetry({
            "event": "appointment_created",
            "lead_id": lead_id,
            "name": name[:2] + "***" if name else "",
            "phone": phone[:3] + "***" + phone[-2:] if len(phone) > 5 else "***",
            "project": project_name,
            "agent": agent
        })
        return jsonify({
            "success": True,
            "lead_id": lead_id,
            "message": "Randevu talebiniz başarıyla alındı. Danışmanımız en kısa sürede sizinle iletişime geçecektir."
        })
    except Exception as e:
        logger.exception("Randevu kaydetme hatasi")
        return jsonify({"success": False, "message": "Kayıt sırasında bir hata oluştu."}), 500


@app.route("/api/config", methods=["GET"])
def api_config():
    """Genel sistem konfigürasyonu."""
    return jsonify({
        "success": True,
        "assistant_name": CFG.get("assistant_display_name", "Mira"),
        "default_agent": {
            "name": "Suzanne Tenekecioğlu",
            "title": "Lüks Konut ve Prestijli Proje Danışmanı",
            "phone": "+905354895656",
            "phone_display": "0535 489 56 56",
            "whatsapp": "https://wa.me/905354895656"
        }
    })


@app.route("/healthz")
@app.route("/health")
@app.route("/api/health")
@app.route("/api/system-status")
def healthz():
    return jsonify({"status": "ok", "service": "nexa-cb-vip",
                    "assistant": CFG.get("assistant_display_name", "Mira"),
                    "time": datetime.now().isoformat(),
                    "port": CFG["port"]})

@app.route("/api/cognitive/status", methods=["GET"])
@app.route("/api/cognitive/reasoning", methods=["GET"])
def api_cognitive_status():
    """NEXA PRIME v2 Autonomous Cognitive System real-time monitoring endpoint."""
    try:
        from nexa_autonomous_system import CognitiveMonitoringDashboard, cognitive_nucleus
        data = CognitiveMonitoringDashboard.get_dashboard_data()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.warning("Cognitive status error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/nexa-documents", methods=["GET"])
def api_nexa_documents():
    project_id = request.args.get("project_id", type=int)
    folder = request.args.get("folder", type=str)  # D1: kategori adı (string)
    try:
        import sqlite3
        db_uri = f"file:{Path(NEXA_DB_PATH).resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        try:
            conn.row_factory = sqlite3.Row
            if project_id:
                rows = conn.execute(
                    "SELECT id, project_id, doc_type, title, file_url, category FROM documents WHERE project_id = ? ORDER BY id",
                    (project_id,)).fetchall()
            elif folder:
                rows = conn.execute(
                    "SELECT id, project_id, doc_type, title, file_url, category FROM documents WHERE (doc_type='doc' OR doc_type='html') AND file_url LIKE '/static/documents/%' AND category LIKE ? ORDER BY project_id, id",
                    (f"%{folder}%",)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, project_id, doc_type, title, file_url, category FROM documents ORDER BY project_id, id").fetchall()
        finally:
            conn.close()
        out = []
        for r in rows:
            d = dict(r)
            url = d.get("file_url") or "#"
            # O8: dış URL'li test/örnek kayıtlar gösterilmez (yerel belge envanteri yalnız)
            if url.startswith("http"):
                continue
            if url.startswith("/static/documents/"):
                url = url.replace("/static/documents/", "/nexa-docs/", 1)
            d["download_url"] = url
            out.append(d)
        return jsonify({"success": True, "count": len(out), "documents": out})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/nexa-summaries", methods=["GET"])
def api_nexa_summaries():
    try:
        from nexa_rag import _load_summaries
        data = _load_summaries()
        items = [{"project_id": v.get("project_id"), "title": k, "summary": v.get("summary", "")}
                 for k, v in data.items()]
        resp = jsonify({"success": True, "count": len(items), "summaries": items})
        resp.headers["Cache-Control"] = "public, max-age=300"
        return resp
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/filter-facets", methods=["GET"])
def api_filter_facets():
    """RAG & Drive senkronizasyonundan anlık beslenen otonom arama filtre faceti."""
    try:
        import re
        import sqlite3
        
        # 1. Load active projects
        projects = get_all_projects_ordered(include_hidden=False)
        
        # 2. Load active portfolio listings
        listings = []
        try:
            db_uri = f"file:{Path(NEXA_DB_PATH).resolve().as_posix()}?mode=ro"
            conn = sqlite3.connect(db_uri, uri=True)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM portfolio_listings ORDER BY id DESC").fetchall()
            listings = [dict(r) for r in rows]
            conn.close()
        except Exception:
            p_file = BASE_DIR / "nexa_portfolio_data.json"
            if p_file.exists():
                try:
                    listings = json.loads(p_file.read_text(encoding="utf-8"))
                except Exception:
                    listings = []

        all_items = projects + listings

        # 3. Dynamic Room Facets
        room_counts = {}
        room_canonical_order = ["1+0", "1+1", "2+1", "3+1", "4+1", "5+1", "6+1", "Villa", "Ofis / Ticari"]
        room_labels = {
            "1+0": "1+0 Stüdyo",
            "1+1": "1+1 Yatırımlık",
            "2+1": "2+1 Konut",
            "3+1": "3+1 Aile",
            "4+1": "4+1 Geniş",
            "5+1": "5+1 / Dubleks",
            "6+1": "6+1 ve Üzeri",
            "Villa": "Müstakil Villa",
            "Ofis / Ticari": "Ticari / Ofis"
        }

        for item in all_items:
            item_rooms = set()
            r_info = str(item.get("room_info") or item.get("rooms") or "")
            cat = str(item.get("category") or "")
            title = str(item.get("title") or item.get("name") or "")
            combined_txt = f"{r_info} {cat} {title}"

            found_patterns = re.findall(r"\b([1-6]\s*\+\s*[0-2])\b", combined_txt)
            for pat in found_patterns:
                clean_r = pat.replace(" ", "")
                item_rooms.add(clean_r)

            if "villa" in combined_txt.lower():
                item_rooms.add("Villa")
            if "ofis" in combined_txt.lower() or "dükkan" in combined_txt.lower() or "ticari" in combined_txt.lower():
                item_rooms.add("Ofis / Ticari")

            for r in item_rooms:
                room_counts[r] = room_counts.get(r, 0) + 1

        room_facets = []
        for r_name in room_canonical_order:
            if room_counts.get(r_name, 0) > 0:
                room_facets.append({
                    "room": r_name,
                    "label": room_labels.get(r_name, r_name),
                    "count": room_counts[r_name]
                })
        for r_name, count in sorted(room_counts.items(), key=lambda x: -x[1]):
            if r_name not in room_canonical_order and count > 0:
                room_facets.append({
                    "room": r_name,
                    "label": room_labels.get(r_name, r_name),
                    "count": count
                })

        # 4. Dynamic Price Tier Facets
        price_tier_defs = [
            {"min": 0, "max": 3000000, "label": "1 - 3 Milyon TL", "icon": "fa-solid fa-tag"},
            {"min": 3000000, "max": 5000000, "label": "3 - 5 Milyon TL", "icon": "fa-solid fa-tag"},
            {"min": 5000000, "max": 10000000, "label": "5 - 10 Milyon TL", "icon": "fa-solid fa-tag"},
            {"min": 10000000, "max": 999999999, "label": "10 Milyon TL ve Üzeri (Lüks)", "icon": "fa-solid fa-gem"}
        ]
        price_facets = []
        for tier in price_tier_defs:
            t_count = 0
            for item in all_items:
                p_min = item.get("price_min") or item.get("price_numeric") or 0
                p_max = item.get("price_max") or item.get("price_numeric") or p_min
                if p_min > 0 and (p_min <= tier["max"] and p_max >= tier["min"]):
                    t_count += 1
            if t_count > 0:
                price_facets.append({
                    "min": tier["min"],
                    "max": tier["max"],
                    "label": tier["label"],
                    "icon": tier["icon"],
                    "count": t_count
                })

        # 5. Dynamic Location Facets
        il_counts = {}
        ilce_counts = {}
        for item in all_items:
            il = (item.get("il") or "Ankara").strip()
            ilce = (item.get("ilce") or "").strip()
            if il:
                il_counts[il] = il_counts.get(il, 0) + 1
            if ilce:
                ilce_counts[ilce] = ilce_counts.get(ilce, 0) + 1

        location_facets = []
        for il, count in sorted(il_counts.items(), key=lambda x: -x[1]):
            location_facets.append({"type": "il", "name": il, "count": count, "icon": "fa-solid fa-city"})
        for ilce, count in sorted(ilce_counts.items(), key=lambda x: -x[1]):
            location_facets.append({"type": "ilce", "name": ilce, "count": count, "icon": "fa-solid fa-location-dot"})

        # 6. Dynamic Delivery Facets
        delivery_counts = {"hemen": 0, "12ay": 0, "24ay": 0, "36ay_plus": 0}
        for item in all_items:
            sum_text = f"{item.get('description','')} {item.get('sales_highlights','')} {item.get('title','')} {item.get('name','')}".lower()
            if any(w in sum_text for w in ['anahtar teslim', 'teslim edil', 'hemen teslim', 'hazır konut', 'iskanı alınmış', 'oturuma hazır']) or item.get("is_portfolio"):
                delivery_counts["hemen"] += 1
            elif any(w in sum_text for w in ['12 ay', '1 yıl', '2025']):
                delivery_counts["12ay"] += 1
            elif any(w in sum_text for w in ['18 ay', '24 ay', '2 yıl', '2026', '18-24 ay']):
                delivery_counts["24ay"] += 1
            elif any(w in sum_text for w in ['36 ay', '48 ay', 'lansman', 'proje aşamasında', '3 yıl', '4 yıl']):
                delivery_counts["36ay_plus"] += 1

        delivery_defs = [
            {"key": "hemen", "label": "Hemen Teslim / Hazır", "icon": "fa-solid fa-bolt", "color": "#34C759"},
            {"key": "12ay", "label": "12 Ay İçinde Teslim", "icon": "fa-solid fa-clock", "color": "#0071E3"},
            {"key": "24ay", "label": "18 - 24 Ay Teslim", "icon": "fa-solid fa-helmet-safety", "color": "#FF9500"},
            {"key": "36ay_plus", "label": "36+ Ay / Lansman", "icon": "fa-solid fa-gem", "color": "#5E5CE6"}
        ]
        delivery_facets = []
        for d_def in delivery_defs:
            cnt = delivery_counts.get(d_def["key"], 0)
            if cnt > 0:
                delivery_facets.append({
                    "key": d_def["key"],
                    "label": d_def["label"],
                    "icon": d_def["icon"],
                    "color": d_def["color"],
                    "count": cnt
                })

        # 7. Dynamic AI Criteria Facets
        ai_high_score_count = len([x for x in all_items if x.get("tkgm_verified") or x.get("is_portfolio") or float(x.get("confidence_score") or 0.9) >= 0.85])
        ai_ready_count = delivery_counts["hemen"]
        ai_verified_count = len([x for x in projects if x.get("tkgm_verified")])

        ai_facets = [
            {"key": "all", "label": "Tüm Seçenekler", "icon": "fa-solid fa-layer-group", "count": len(all_items)},
            {"key": "high_score", "label": "9.0+ Üstün AI Skorlu", "icon": "fa-solid fa-star", "color": "#FFD700", "count": ai_high_score_count},
            {"key": "ready", "label": "Hemen Teslim / Hazır", "icon": "fa-solid fa-key", "color": "#34C759", "count": ai_ready_count},
            {"key": "verified", "label": "TKGM Parsel Onaylı", "icon": "fa-solid fa-circle-check", "color": "#0071E3", "count": ai_verified_count}
        ]

        resp = jsonify({
            "success": True,
            "total_items": len(all_items),
            "data": {
                "rooms": room_facets,
                "price_tiers": price_facets,
                "locations": location_facets,
                "deliveries": delivery_facets,
                "ai": ai_facets
            }
        })
        resp.headers["Cache-Control"] = "public, max-age=180"
        return resp
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/nexa-regions", methods=["GET"])
def api_nexa_regions():
    """Bölge/Konum Seçimi + zihin haritası paneli için RAG kaynaklı güncel proje verisi."""
    try:
        from nexa_rag import _load_summaries
        summaries = _load_summaries()
        import sqlite3
        db_uri = f"file:{Path(NEXA_DB_PATH).resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT id, name, il, ilce, mahalle, location, description, ada_no, parsel_no,
                       price_display, room_info, tkgm_verified
                FROM projects WHERE COALESCE(is_portfolio,0) = 0 ORDER BY name
            """).fetchall()
        finally:
            conn.close()
        out = []
        for r in rows:
            p = dict(r)
            loc = p.get("location") or f"{p.get('mahalle') or ''} {p.get('ilce') or ''} {p.get('il') or ''}".strip()
            sum_text = summaries.get(p["name"], {}).get("summary", "")
            out.append({
                "name": p["name"],
                "il": p.get("il") or "",
                "ilce": p.get("ilce") or "",
                "mahalle": p.get("mahalle") or "",
                "location": loc,
                "ada_no": p.get("ada_no") or "",
                "parsel_no": p.get("parsel_no") or "",
                "price_display": p.get("price_display") or "",
                "room_info": p.get("room_info") or "",
                "tkgm_verified": bool(p.get("tkgm_verified")),
                "summary": sum_text,
            })
        resp = jsonify({"success": True, "count": len(out), "data": out})
        resp.headers["Cache-Control"] = "public, max-age=300"
        return resp
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/nexa-docs/<path:filename>")
def nexa_docs_file(filename):
    base = NEXA_DOCS_DIR.resolve()
    target = (base / filename).resolve()
    if base not in target.parents and target != base:
        return "Erişim engellendi", 403
    if not target.exists() or not target.is_file():
        return "Dosya bulunamadı", 404
    resp = send_file(str(target))
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp

@app.route("/site")
def site():
    site_file = BASE_DIR / "site.html"
    if not site_file.exists():
        return "site.html bulunamadı", 404
    resp = Response(site_file.read_text(encoding="utf-8"), mimetype="text/html; charset=utf-8")
    resp.headers['Cache-Control'] = 'public, max-age=3600, must-revalidate'
    return resp

@app.route("/favicon.ico")
def favicon():
    fav = BASE_DIR / "favicon.ico"
    if not fav.exists():
        fav = STATIC_DIR / "favicon.ico"
    if not fav.exists():
        fav = STATIC_DIR / "img" / "suzanne_icon_circle_32.png"
    resp = send_file(fav, mimetype="image/x-icon")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp

@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
@app.route("/favicon.png")
def apple_touch_icon():
    fav = BASE_DIR / "apple-touch-icon.png"
    if not fav.exists():
        fav = STATIC_DIR / "img" / "suzanne_icon_circle_180.png"
    resp = send_file(fav, mimetype="image/png")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp

@app.route("/splash-poster.jpg")
@app.route("/splash_video_poster.jpg")
def splash_poster():
    poster = STATIC_DIR / "img" / "splash_video_poster.jpg"
    if not poster.exists():
        poster = BASE_DIR / "splash_video_poster.jpg"
    if poster.exists():
        resp = send_file(poster, mimetype="image/jpeg")
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp
    return "Not found", 404

@app.route("/manifest.json")
def pwa_manifest():
    mfile = STATIC_DIR / "manifest.json"
    if mfile.exists():
        resp = Response(mfile.read_text(encoding="utf-8"), mimetype="application/manifest+json")
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp
    return jsonify({"error": "manifest not found"}), 404

@app.route("/sw.js")
def service_worker():
    swfile = STATIC_DIR / "sw.js"
    if swfile.exists():
        resp = Response(swfile.read_text(encoding="utf-8"), mimetype="application/javascript")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Service-Worker-Allowed"] = "/"
        return resp
    return "Service Worker not found", 404

@app.route("/static/<path:filename>")
def static_files(filename):
    resp = send_from_directory(STATIC_DIR, filename)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp

@app.route("/1.mp4")
@app.route("/video/1.mp4")
def serve_brand_video():
    vpath = BASE_DIR / "1.mp4"
    if not vpath.exists():
        vpath = STATIC_DIR / "1.mp4"
    if vpath.exists():
        resp = stream_file_response(vpath, "video/mp4")
        resp.headers["Cache-Control"] = "public, max-age=604800, immutable"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Range, Accept-Encoding"
        return resp
    return "Video bulunamadı", 404

# ─── P15: güvenlik başlıkları (tüm yanıtlara) ───
@app.after_request
def _add_security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not request.path.startswith("/stream/") and not request.path.startswith("/static/"):
        resp.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; media-src 'self' https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; connect-src 'self' https:; frame-src https://www.youtube.com https://drive.google.com; manifest-src 'self'; worker-src 'self'"
    return resp

# ─── JSON hata handler'ları (yalnızca /api/ prefix'li istekler) ───
@app.errorhandler(404)
def _handle_404(err):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "Uç nokta bulunamadı"}), 404
    return "Sayfa bulunamadı", 404

@app.errorhandler(500)
def _handle_500(err):
    logger.exception("Sunucu hatasi")
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "Sunucu hatası"}), 500
    return "Sunucu hatası", 500

@app.route("/projeler/<path:filename>")
def projeler_files(filename):
    return send_from_directory(PROJELER_DIR, filename)

# ─── HIGH PERFORMANCE HTTP 206 CLOUD VIDEO STREAMING ENDPOINT ───
def stream_file_response(path: Path, mimetype: str):
    file_size = path.stat().st_size
    range_header = request.headers.get('Range', None)

    if not range_header:
        return send_file(str(path), mimetype=mimetype)

    byte1, byte2 = 0, None
    m = re.search(r'bytes=(\d+)-(\d*)', range_header)
    if m:
        g = m.groups()
        byte1 = int(g[0])
        if g[1]:
            byte2 = int(g[1])

    # O6: RFC 7233 — başlangıç dosya sonunu aşarsa 416; bitiş sınırlanır
    if byte1 >= file_size or (byte2 is not None and byte2 < byte1):
        return Response('', 416, headers={
            'Content-Range': f'bytes */{file_size}',
            'Accept-Ranges': 'bytes'})
    if byte2 is not None and byte2 >= file_size:
        byte2 = file_size - 1

    length = file_size - byte1
    if byte2 is not None:
        length = byte2 - byte1 + 1

    chunk_size = 1024 * 1024  # 1MB chunks
    def generate():
        with open(path, 'rb') as f:
            f.seek(byte1)
            remaining = length
            while remaining > 0:
                read_bytes = min(chunk_size, remaining)
                data = f.read(read_bytes)
                if not data:
                    break
                remaining -= len(data)
                yield data

    resp = Response(generate(), 206, mimetype=mimetype, content_type=mimetype, direct_passthrough=True)
    resp.headers.add('Content-Range', f'bytes {byte1}-{byte1 + length - 1}/{file_size}')
    resp.headers.add('Accept-Ranges', 'bytes')
    resp.headers.add('Content-Length', str(length))
    return resp

@app.route("/file")
def file_serve():
    path_arg = request.args.get("path", "")
    if not path_arg:
        return "path parametresi gerekli", 400
    try:
        rel = os.path.normpath(path_arg).lstrip("/\\")
        if rel.lower().startswith("projeler" + os.sep) or rel.lower().startswith("projeler/"):
            rel = rel[len("projeler"):].lstrip("/\\")
        base = PROJELER_DIR.resolve()
        target = (base / rel).resolve()
        # O2: prefix yerine gerçek ebeveyn kontrolü (resolve() symlink'leri de çözer)
        if target != base and base not in target.parents:
            logger.warning("Yol disari cikma denemesi: %s", path_arg)
            return "Geçersiz yol", 400
        if not target.exists() or not target.is_file():
            return "Dosya bulunamadı", 404
    except Exception:
        return "Hatalı yol", 400

    suffix = target.suffix.lower()
    if suffix == ".mp4":
        resp = stream_file_response(target, "video/mp4")
        resp.headers["Cache-Control"] = "public, max-age=604800"
        return resp
    if suffix == ".pdf":
        resp = send_file(str(target), mimetype="application/pdf")
        resp.headers["Cache-Control"] = "public, max-age=604800"
        return resp
    resp = send_file(str(target))
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp

@app.route("/stream/video/<project_id>")
def stream_video(project_id):
    if not JSON_FILE.exists():
        return "Map file not found", 404

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        projects = json.load(f)

    project = next((p for p in projects if str(p.get("id")) == str(project_id) or str(p.get("db_id")) == str(project_id)), None)
    if not project:
        return "Project not found", 404

    folder_name = (project.get("folder_name") or "").strip().replace("\\", "/").split("/")[-1]
    target_dir = PROJELER_DIR / folder_name
    if not target_dir.resolve().is_relative_to(PROJELER_DIR.resolve()):
        return "Invalid path", 400

    # MP4 selection priority
    _PRIORITY_WORDS_1 = ("tanitim", "intro", "main", "ana", "lansman", "animasyon", "promosyon", "promo")
    _PRIORITY_WORDS_2 = ("slayt", "slideshow", "sunum")

    def _fold_tr(s):
        return (s.replace("İ", "i").replace("I", "i").replace("ı", "i")
                .replace("Ş", "s").replace("ş", "s")
                .replace("Ğ", "g").replace("ğ", "g")
                .replace("Ç", "c").replace("ç", "c")
                .replace("Ö", "o").replace("ö", "o")
                .replace("Ü", "u").replace("ü", "u")
                .lower())

    def _mp4_priority(f: Path):
        name = _fold_tr(f.stem)
        for i, kw in enumerate(_PRIORITY_WORDS_1):
            if kw in name:
                return (0, i, -f.stat().st_size)
        for i, kw in enumerate(_PRIORITY_WORDS_2):
            if kw in name:
                return (1, i, -f.stat().st_size)
        return (2, 0, -f.stat().st_size)

    mp4_files = list(target_dir.glob("*.mp4")) if target_dir.exists() else []
    mp4_files.sort(key=_mp4_priority)
    real_mp4 = None
    for file in mp4_files:
        if file.stat().st_size > 500 * 1024:
            real_mp4 = file
            break

    if not real_mp4 and mp4_files:
        real_mp4 = mp4_files[0]

    if not real_mp4 or not real_mp4.exists():
        drive_url = project.get("drive_video_preview") or project.get("tanitim_cloud_url") or ""
        if drive_url.startswith("http"):
            m = re.search(r"/file/d/([\w-]{15,})", drive_url)
            if m:
                return redirect(f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=media&confirm=t")
            return redirect(drive_url)
        return "Video file not found", 404

    resp = stream_file_response(real_mp4, "video/mp4")
    resp.headers["Cache-Control"] = "public, max-age=604800"
    resp.headers["Accept-Ranges"] = "bytes"
    return resp

@app.route("/stream/pdf/<project_id>")
@app.route("/download/pdf/<project_id>")
def stream_pdf(project_id):
    """watchdog ve projects_map /stream/pdf/<id> bağlantıları için PDF dosyasını servis eder."""
    if not JSON_FILE.exists():
        return "Map file not found", 404
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        projects = json.load(f)
    project = next((p for p in projects if str(p.get("id")) == str(project_id) or str(p.get("db_id")) == str(project_id)), None)
    if not project:
        return "Project not found", 404
    pre = project.get("presentations") or []
    base = PROJELER_DIR.resolve()
    target = None
    if pre:
        folder_name = (project.get("folder_name") or project.get("title") or "").strip().replace("\\", "/").split("/")[-1]
        rel = pre[0].get("path") or pre[0].get("filename") or ""
        filename = os.path.basename(rel)
        # 1. Deneme: projeler / folder_name / filename
        cand1 = (base / folder_name / filename).resolve() if folder_name else None
        if cand1 and cand1.is_relative_to(base) and cand1.exists() and cand1.is_file():
            target = cand1
        else:
            # 2. Deneme: rel doğrudan (projeler/ ön eki temizlenerek)
            clean_rel = rel.replace("projeler/", "").replace("projeler\\", "")
            clean_filename = os.path.basename(clean_rel)
            cand2 = (base / clean_filename).resolve()
            if cand2.is_relative_to(base) and cand2.exists() and cand2.is_file():
                target = cand2

    if not target or not target.exists() or not target.is_file() or target.suffix.lower() != ".pdf":
        drive_url = project.get("drive_pdf_preview") or ""
        if drive_url.startswith("http"):
            return redirect(drive_url)
        return "PDF bulunamadı", 404

    resp = send_file(str(target), mimetype="application/pdf")
    resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp

@app.route("/api/projects/<project_id>/report")
def api_project_report(project_id):
    if not JSON_FILE.exists():
        return jsonify({"success": False, "message": "projects_map.json bulunamadı"}), 404
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        projects = json.load(f)
    project = next((p for p in projects if str(p.get("id")) == str(project_id) or str(p.get("db_id")) == str(project_id)), None)
    if not project:
        return jsonify({"success": False, "message": "Proje bulunamadı"}), 404

    title = project.get("title", "Prestij Projesi")

    # O4/B8: gerçek özet + fiyat/oda verisiyle zengin danışman notu
    summary = ""
    try:
        summary = get_project_summary(title)
    except Exception:
        summary = ""
    pricing = {}
    try:
        pf = BASE_DIR / "nexa_portfolio_data.json"
        if pf.exists():
            pdata = json.loads(pf.read_text(encoding="utf-8"))
            pool = pdata if isinstance(pdata, list) else pdata.get("projects", [])
            for item in pool:
                if str(item.get("title")) == str(title) or str(item.get("name")) == str(title):
                    pricing = item
                    break
    except Exception:
        pricing = {}

    price_display = pricing.get("price_display") or "Fiyat için danışmanımızdan bilgi alınız"
    room_info = pricing.get("room_info") or "Daire tipleri için danışmanımızdan bilgi alınız"
    loc = pricing.get("location") or project.get("location") or "Prestij Lokasyonu"

    report = (
        f"DANISMAN NOTU — {title}\n"
        "===============================================\n\n"
        "📌 PROJE ÖZETİ\n"
        f"• Proje: {title}\n"
        f"• Bölge: {loc}\n"
        f"• Fiyat: {price_display}\n"
        f"• Daire Tipleri: {room_info}\n"
        f"• Geliştirici: Coldwell Banker VIP\n\n"
    )
    if summary:
        report += f"💡 NEXA AI PROJE ÖZETİ\n{summary}\n\n"
    else:
        report += (
            "💡 NEXA AI DEĞERLENDİRMESİ\n"
            "Proje için henüz otomatik özet üretilmedi; ayrıntılı bilgi için "
            "Suzanne Hanım ile iletişime geçiniz.\n\n"
        )
    report += "📞 0535 489 56 56\nWhatsApp üzerinden anlık bilgi alabilirsiniz."
    return jsonify({"success": True, "report": report})

# ─── OTONOM VERİ SENKRONU (P19) ───
# NEXA PRIME DB tek doğruluk kaynağı; importer buradan chat/filtre JSON'larını
# üretir, CB sync Susanne ilanlarını DB'ye besler. Elle giriş gerekmez.


def _run_importer() -> bool:
    try:
        import nexa_data_importer
        nexa_data_importer.main()
        return True
    except Exception as e:
        logger.exception("nexa_data_importer hatasi")
        return False


# ─── OTOMATİK PİPELİNE: GITHUB ACTIONS ÇALIŞTIRIR ───
# Bu fonksiyonlar sunucuda DAEMON olarak ÇALIŞMAZ.
# Pipeline (CB sync + importer + self-healing + summaries)
# her 6 saatte bir GitHub Actions (.github/workflows/update_db.yml)
# tarafından tetiklenir. Sunucuda sadece API endpoint'leri kalır.
#
# Manuel tetikleme için:
#   POST /api/nexa-sync        → importer + CB sync
#   POST /api/self-healing/trigger → self-healing
#   GET  /api/self-healing/status  → health score


@app.route("/api/self-healing/status", methods=["GET"])
def api_self_healing_status():
    """Canlı sistem sağlık skoru ve self-healing durumunu döndürür."""
    try:
        import nexa_self_healing
        status = nexa_self_healing.get_current_health_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/self-healing/trigger", methods=["POST"])
def api_self_healing_trigger():
    """Anlık self-healing ve sistem bütünlük onarım döngüsünü tetikler."""
    if not _admin_ok():
        return jsonify({"success": False, "error": "Yetki yok"}), 403
    try:
        import nexa_self_healing
        report = nexa_self_healing.run_full_self_healing_cycle()
        return jsonify({"success": True, "data": report})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nexa-sync", methods=["POST"])
def api_nexa_sync():
    """Otonom pipeline'ı elle tetikler: DB → JSON importer + CB yenileme."""
    if not _admin_ok():
        return jsonify({"success": False, "error": "Yetki yok"}), 403
    importer_ok = _run_importer()
    _refresh_cb_listings_bg()
    try:
        import nexa_self_healing
        nexa_self_healing.run_full_self_healing_cycle()
    except Exception:
        pass
    return jsonify({"success": True, "importer": importer_ok,
                    "ts": datetime.now().isoformat()})


# ─── ANA SAYFA: /site vitrinine yönlendir (eski galeri şablonu kaldırıldı, P14) ───

# ─── RAG & ADMIN DISPLAY ORDER ENGINE ─────────────────────────────────────────
def get_saved_display_order():
    order_file = BASE_DIR / "display_order.json"
    if order_file.exists():
        try:
            with open(order_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def get_all_projects_ordered(include_hidden=False):
    projects_file = BASE_DIR / "projects_map.json"
    if not projects_file.exists():
        return []
    try:
        with open(projects_file, "r", encoding="utf-8") as f:
            projects = json.load(f)
    except Exception:
        return []

    saved_orders = get_saved_display_order()
    order_map = {str(item.get("id")): item for item in saved_orders if isinstance(item, dict)}

    # Attach order metadata
    for p in projects:
        p_id = str(p.get("id"))
        if p_id in order_map:
            meta = order_map[p_id]
            p["rank"] = meta.get("rank", 999)
            p["is_pinned"] = meta.get("is_pinned", False)
            p["is_hidden"] = meta.get("is_hidden", False)
        else:
            p["rank"] = 999
            p["is_pinned"] = False
            p["is_hidden"] = False

    # Sort: Pinned first, then by rank, then original order
    projects.sort(key=lambda x: (
        0 if x.get("is_pinned") else 1,
        x.get("rank", 999)
    ))

    if not include_hidden:
        projects = [p for p in projects if not p.get("is_hidden")]

    return projects

ADMIN_PIN = os.getenv("NEXA_ADMIN_PIN") or os.getenv("ADMIN_PIN") or "nexa2026vip"
_admin_fail_hits = {}
_admin_fail_lock = threading.Lock()

def _check_admin_auth():
    """PIN kontrolü: Header, Bearer token veya URL parametresi ile doğrular; brute-force korumalı."""
    admin_pin = os.getenv("NEXA_ADMIN_PIN") or os.getenv("ADMIN_PIN") or ADMIN_PIN or "nexa2026vip"
    ip = _get_client_ip()
    now = time.time()
    with _admin_fail_lock:
        fails = [t for t in _admin_fail_hits.get(ip, []) if now - t < 60]
        if len(fails) >= 6:
            logger.warning("Admin brute-force block for IP: %s", ip)
            return False, (jsonify({"success": False, "error": "Too Many Requests", "message": "Çok fazla hatalı deneme. 1 dakika bekleyin."}), 429)
    
    pin = request.headers.get("X-Admin-Pin") or request.args.get("pin") or request.cookies.get("admin_pin") or ""
    auth = request.headers.get("Authorization", "")
    if not pin and auth.startswith("Bearer "):
        pin = auth[7:].strip()

    import secrets as _secrets
    is_valid = bool(pin and _secrets.compare_digest(str(pin), str(admin_pin)))
    if not is_valid:
        with _admin_fail_lock:
            fails.append(now)
            _admin_fail_hits[ip] = fails
        return False, (jsonify({"success": False, "error": "Unauthorized", "message": "Yetkisiz erişim. Geçersiz PIN."}), 403)
    return True, None

def _admin_ok():
    ok, _ = _check_admin_auth()
    return ok

@app.route("/admin")
def admin_page():
    ok, err_resp = _check_admin_auth()
    if not ok:
        return err_resp
    admin_file = BASE_DIR / "admin.html"
    if admin_file.exists():
        return send_file(admin_file)
    return "Admin paneli arayüzü bulunamadı.", 404

@app.route("/api/admin/projects-order", methods=["GET", "POST"])
def admin_projects_order_api():
    ok, err_resp = _check_admin_auth()
    if not ok:
        return err_resp
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        order_list = data.get("order", [])
        if not isinstance(order_list, list):
            return jsonify({"success": False, "message": "Geçersiz veri formatı. 'order' bir liste olmalıdır."}), 400
        
        sanitized = []
        for it in order_list:
            if isinstance(it, dict) and it.get("id"):
                try:
                    sanitized.append({
                        "id": str(it.get("id")),
                        "rank": int(it.get("rank", 999)),
                        "is_pinned": bool(it.get("is_pinned", False)),
                        "is_hidden": bool(it.get("is_hidden", False))
                    })
                except (ValueError, TypeError):
                    continue
                    
        order_file = BASE_DIR / "display_order.json"
        try:
            with open(order_file, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, ensure_ascii=False, indent=2)
            logger.info(f"[ADMIN] Proje sıralaması kaydedildi: {len(sanitized)} adet kart güncellendi.")
            return jsonify({"success": True, "count": len(sanitized)})
        except Exception as e:
            logger.exception("Proje siralamasi kaydedilemedi")
            return jsonify({"success": False, "message": "Sıralama dosyası kaydedilemedi"}), 500

    # GET
    projects = get_all_projects_ordered(include_hidden=True)
    return jsonify({
        "success": True,
        "count": len(projects),
        "projects": projects
    })

@app.route("/api/admin/rag-meta", methods=["GET"])
def admin_rag_meta():
    if not _admin_ok():
        return jsonify({"success": False, "message": "Yetkisiz erişim."}), 403
    projects = get_all_projects_ordered(include_hidden=True)
    locations = sorted(list(set(p.get("location") for p in projects if p.get("location"))))
    developers = sorted(list(set(p.get("developer") for p in projects if p.get("developer"))))
    return jsonify({
        "success": True,
        "total_projects": len(projects),
        "locations": locations,
        "developers": developers
    })

@app.route("/api/admin/customers", methods=["GET", "PUT", "DELETE"])
def admin_customers_api():
    ok, err_resp = _check_admin_auth()
    if not ok:
        return err_resp
    
    import sqlite3
    conn = sqlite3.connect(str(NEXA_DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == "GET":
        search = request.args.get("search", "").strip()
        stage = request.args.get("stage", "").strip()
        query = "SELECT * FROM customers WHERE 1=1"
        params = []
        if stage:
            query += " AND stage = ?"
            params.append(stage)
        if search:
            query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ? OR notes LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term, term])
        query += " ORDER BY id DESC LIMIT 200"
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify({"success": True, "customers": rows, "count": len(rows)})

    elif request.method == "PUT":
        data = request.get_json(silent=True) or {}
        cust_id = data.get("id")
        new_stage = data.get("stage")
        if not cust_id or not new_stage:
            conn.close()
            return jsonify({"success": False, "message": "id ve stage zorunludur"}), 400
        cur.execute("UPDATE customers SET stage = ? WHERE id = ?", (new_stage, cust_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Müşteri statüsü '{new_stage}' olarak güncellendi."})

    elif request.method == "DELETE":
        cust_id = request.args.get("id")
        if not cust_id:
            conn.close()
            return jsonify({"success": False, "message": "id zorunludur"}), 400
        cur.execute("DELETE FROM customers WHERE id = ?", (cust_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Müşteri kaydı silindi."})


@app.route("/")
def index():
    return redirect("/site", code=302)


if __name__ == "__main__":
    logger.info("[START] NEXA CB VIP — http://localhost:%s", CFG["port"])
    # Development modunda sadece watchdog + drive-puller başlar
    # (CI pipeline: CB sync, importer, self-healing, summaries → GitHub Actions)
    try:
        import nexa_watchdog
        threading.Thread(target=nexa_watchdog.watchdog_loop, daemon=True, name="watchdog").start()
    except Exception as e:
        logger.warning("watchdog baslatilamadi: %s", e)
    try:
        import nexa_drive_puller
        threading.Thread(target=nexa_drive_puller.drive_loop, daemon=True, name="drive-puller").start()
    except Exception as e:
        logger.warning("drive puller baslatilamadi: %s", e)
    app.run(host=CFG["host"], port=int(CFG["port"]), debug=False, use_reloader=False, threaded=True)

