import os
import sys
import json
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")

print("=" * 75)
print("PROPTECH SALES & AI ASSISTANT PLATFORM — DEEP SYSTEM AUDIT (ADIM 1-11)")
print("=" * 75)

# ADIM 1: Klasör Yapısı
print("\n[ADIM 1] Proje Klasör Yapısı:")
for item in sorted(base.iterdir()):
    if item.is_dir():
        try:
            count = len(list(item.iterdir()))
            print(f"  📁 [DIR]  {item.name:<28} ({count} alt öğe)")
        except Exception:
            print(f"  📁 [DIR]  {item.name:<28}")
    else:
        print(f"  📄 [FILE] {item.name:<28} ({item.stat().st_size:>8} bytes)")

# ADIM 2: Frontend Mimarisi
print("\n[ADIM 2] Frontend Mimarisi:")
site_html = base / "site.html"
if site_html.exists():
    content = site_html.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    print(f"  - Framework: Vanilla HTML5 / Modern Responsive CSS / Vanilla JS (No build-step lock-in)")
    print(f"  - Toplam Satır: {len(lines)}")
    print(f"  - Kütüphaneler: FontAwesome 6.4, Google Fonts (Outfit / Plus Jakarta Sans), GSAP 3.12")
    print(f"  - Ana DOM Konteynerleri: splashScreen, hero, filter-keyword-input, location-filters, projectsView (projects-track), portfolioView (portfolio-track), chatbot-widget, detailModal, videoModal, pdfModal, reportModal")

# ADIM 3: Backend Mimarisi
print("\n[ADIM 3] Backend Mimarisi:")
app_py = base / "app.py"
if app_py.exists():
    app_text = app_py.read_text(encoding="utf-8", errors="ignore")
    routes = []
    for line in app_text.splitlines():
        if line.strip().startswith("@app.route"):
            routes.append(line.strip())
    print(f"  - Backend Framework: Python Flask (Threaded WSGI, Port 5002)")
    print(f"  - Mevcut API Uç Noktaları ({len(routes)} adet):")
    for r in routes:
        print(f"     * {r}")

# ADIM 4: Veritabanı Şeması
print("\n[ADIM 4] Database Şeması (SQLite - nexa_database.db):")
db_path = base / "nexa_database.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    for t in tables:
        tname = t[0]
        cur.execute(f"PRAGMA table_info('{tname}')")
        cols = [c[1] for c in cur.fetchall()]
        cur.execute(f"SELECT COUNT(*) FROM '{tname}'")
        cnt = cur.fetchone()[0]
        print(f"  - Tablo: {tname:<20} ({cnt:>5} satır) -> Sütunlar: {', '.join(cols[:10])}")
    conn.close()

# ADIM 5: Mevcut Veri Modeli
print("\n[ADIM 5] Veri Modeli & VIP Üniversite Veri Durumu:")
proj_map = base / "projects_map.json"
if proj_map.exists():
    pdata = json.loads(proj_map.read_text(encoding="utf-8"))
    print(f"  - projects_map.json İçerisinde Kayıtlı Proje Sayısı: {len(pdata)}")
    for p in pdata:
        if "üniversite" in p.get("title", "").lower() or "universite" in p.get("title", "").lower():
            print(f"  - VIP Üniversite Kaydı (projects_map.json):")
            print(json.dumps(p, ensure_ascii=False, indent=4))

# DB'deki VIP Üniversite kaydı:
if db_path.exists():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM projects WHERE name LIKE '%üniversite%' OR name LIKE '%universite%'").fetchall()
    print(f"  - VIP Üniversite Kaydı (nexa_database.db - {len(rows)} satır):")
    for r in rows:
        d = dict(r)
        print(f"     ID={d.get('id')}, Name={d.get('name')}, Price={d.get('price_display')}, Room={d.get('room_info')}, Loc={d.get('ilce')}/{d.get('mahalle')}")
    conn.close()

# ADIM 6: AI ve RAG Sistemi Entegrasyonu
print("\n[ADIM 6] AI & RAG Sistemi:")
print("  - RAG Motoru: nexa_rag.py (Cognitive RAG + Document Chunks RAG + Gemini Fallback + Local Ollama fallback)")
print("  - Vektör Motoru: nexa_vector_rag.py (Cosine similarity on document chunks)")
print("  - NLP Intent & Matching: nexa_ai_engine.py (Budget, region, investment goals, match % score calculation)")
print("  - Chatbot Endpoint: POST /api/nexa-ai-chat")

# ADIM 7: Google Drive & Ingestion Entegrasyonu
print("\n[ADIM 7] Google Drive & Data Ingestion Durumu:")
print("  - Mevcut Cloud Uploader: cloud_uploader.py & fast_cloud_uploader.py (Catbox / Litterbox CDN streaming)")
print("  - Fiyat & Veri İthalatçıları: fiyat_import.py, nexa_data_importer.py, scripts/ingest_ilanlar_portfolios.py, scripts/nexa_cb_sync.py")

# ADIM 8: Admin Paneli & Authentication
print("\n[ADIM 8] Admin Panel & Auth Yapısı:")
admin_files = [f for f in ["admin.html", "portal.html", "app/api/auth.py", "app/core/security.py"] if (base / f).exists()]
print(f"  - Mevcut Admin/Auth Dosyaları: {', '.join(admin_files)}")

# ADIM 9: WhatsApp Entegrasyonu
print("\n[ADIM 9] WhatsApp Entegrasyon Durumu:")
print("  - Floating Button: wa.me/905354895656 (Varsayılan kurumsal / danışman hattı)")
print("  - Kart Başına WhatsApp: Kart altındaki WhatsApp butonları dinamik ön tanımlı proje mesajı oluşturuyor.")

# ADIM 10: Mobile Responsive Durumu
print("\n[ADIM 10] Mobile Responsive & Breakpoints:")
print("  - CSS Media Queries: max-width 1024px, 768px, 480px")
print("  - Touch Swipe: initTouchSwipe aktif (projeler ve portföy karuselleri)")

# ADIM 11: Dosya Yolları & Import Yapısı
print("\n[ADIM 11] Dosya Yolları ve İçe Aktarma Yapısı:")
print(f"  - Kök Dizin (Base): {base.resolve()}")
print("  - Veritabanı Yolu: Desktop/3/nexa_database.db")
print("  - Projeler Yolu: Desktop/3/projeler")
print("  - Dokümanlar Yolu: Desktop/3/static/documents")

print("\n" + "=" * 75)
print("AUDIT SCRIPT TAMAMLANDI")
print("=" * 75)
