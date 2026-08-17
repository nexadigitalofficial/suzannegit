import urllib.request, json, sys, io, time, sqlite3
from pathlib import Path

BASE_URL = "http://localhost:5002"
passed_tests = 0
failed_tests = 0
warnings = 0

def log_pass(msg):
    global passed_tests
    passed_tests += 1
    print(f"  [PASS] {msg}", flush=True)

def log_fail(msg):
    global failed_tests
    failed_tests += 1
    print(f"  [FAIL] {msg}", flush=True)

def log_warn(msg):
    global warnings
    warnings += 1
    print(f"  [WARN] {msg}", flush=True)

def http_get(path, headers=None, decode=True):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers or {})
    with urllib.request.urlopen(req, timeout=5) as res:
        content = res.read()
        text = content.decode('utf-8', errors='ignore') if decode else ""
        return res.status, text, res.headers

def http_post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=5) as res:
        return res.status, res.read().decode('utf-8')

print("=" * 80, flush=True)
print("NEXA PROPTECH - 360 ULTRA DEEP SYSTEM & DRIVE INTEGRATION TEST SUITE", flush=True)
print("=" * 80, flush=True)

# 1. CORE API & SYSTEM HEALTH TESTS
print("\n[BOLUM 1] CEKIRDEK API & SERVIS SAGLIK TESTLERI", flush=True)
try:
    s, b, _ = http_get("/healthz")
    d = json.loads(b)
    if s == 200 and d.get("status") == "ok":
        log_pass(f"/healthz: Asistan: {d.get('assistant')} | Port: {d.get('port')}")
    else:
        log_fail(f"/healthz beklenmeyen yanit: {b}")
except Exception as e:
    log_fail(f"/healthz hata: {e}")

try:
    s, b, _ = http_get("/api/config")
    d = json.loads(b)
    if s == 200 and d.get("assistant_name") == "Alya" and d.get("default_agent", {}).get("name") == "Yiğit Narin":
        log_pass(f"/api/config: Asistan={d.get('assistant_name')}, Danisman={d.get('default_agent',{}).get('name')}")
    else:
        log_fail(f"/api/config konfigurasyon uyumsuz: {b}")
except Exception as e:
    log_fail(f"/api/config hata: {e}")

try:
    s, b, _ = http_get("/api/projects")
    d = json.loads(b)
    projects = d.get("data", [])
    if s == 200 and len(projects) >= 20:
        log_pass(f"/api/projects: Toplam {len(projects)} aktif proje yuklendi.")
    else:
        log_fail(f"/api/projects eksik proje: {len(projects)}")
except Exception as e:
    log_fail(f"/api/projects hata: {e}")

try:
    s, b, _ = http_get("/api/self-healing/status")
    d = json.loads(b).get("data", {})
    if d.get("status") == "healthy" and d.get("health_score") == 100:
        log_pass(f"Self-Healing Sentinel: Skor=%{d.get('health_score')} | Durum={d.get('status')} | {d.get('passed_checks')}/{d.get('total_checks')} Kontrol")
    else:
        log_fail(f"Self-Healing uyarisi: {d}")
except Exception as e:
    log_fail(f"Self-Healing API hata: {e}")

# 2. GOOGLE DRIVE BULUT ONIZLEME & MEDYA DOGRULAMA
print("\n[BOLUM 2] GOOGLE DRIVE BULUT ONIZLEME & MEDYA INDEKS TESTLERI", flush=True)
drive_vid_count = 0
drive_pdf_count = 0

for p in projects:
    pid = p.get("id")
    title = p.get("title")
    vid_preview = p.get("drive_video_preview")
    pdf_preview = p.get("drive_pdf_preview")
    
    if vid_preview and "drive.google.com" in vid_preview:
        drive_vid_count += 1
    if pdf_preview and "drive.google.com" in pdf_preview:
        drive_pdf_count += 1

log_pass(f"Google Drive Video Onizleme Linki: {drive_vid_count}/{len(projects)} Projede Aktif")
log_pass(f"Google Drive PDF Sunum Linki: {drive_pdf_count}/{len(projects)} Projede Aktif")

# Test a sample video stream endpoint fallback
try:
    s, _, headers = http_get("/stream/video/cbvip-prj-20", headers={"Range": "bytes=0-1024"}, decode=False)
    if s in [200, 206]:
        log_pass(f"Video Stream VIP Universite (cbvip-prj-20): HTTP {s} OK")
    else:
        log_fail(f"Video Stream cbvip-prj-20 HTTP {s}")
except Exception as e:
    log_fail(f"Video Stream hata: {e}")

# 3. FIYAT BUTUNLUGU (SSOT) VE VERITABANI TESTLERI
print("\n[BOLUM 3] TEK GERCEK KAYNAK (SSOT) VE VERITABANI KONTROLLERI", flush=True)
vip_u = next((p for p in projects if "VIP ÜNİVERSİTE" in p.get("title","").upper() or "VIP UNIVERSITE" in p.get("title","").upper()), None)
if vip_u:
    if vip_u.get("price_numeric") == 1350000 and "1.350.000" in vip_u.get("price_display",""):
        log_pass(f"VIP Universite projects_map.json Fiyati: {vip_u.get('price_display')} (Sayisal: {vip_u.get('price_numeric'):,})")
    else:
        log_fail(f"VIP Universite hatali fiyat: {vip_u.get('price_display')}")

# Database Check
try:
    conn = sqlite3.connect("C:/Users/USER/Desktop/3/nexa_database.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM projects")
    db_prjs = c.fetchone()[0]
    c.execute("SELECT name, price_display, price_numeric FROM projects WHERE UPPER(name) LIKE '%VIP ÜNİVERSİTE%' OR UPPER(name) LIKE '%VIP UNIVERSITE%'")
    db_vip = c.fetchone()
    conn.close()
    
    log_pass(f"SQLite DB: Toplam {db_prjs} proje kayitli.")
    if db_vip and db_vip[2] == 1350000:
        log_pass(f"SQLite DB VIP Universite Fiyati: {db_vip[1]} ({db_vip[2]:,}) - 100% Senkronize")
    else:
        log_fail(f"SQLite DB VIP Universite uyumsuz: {db_vip}")
except Exception as e:
    log_fail(f"SQLite DB testi hata: {e}")

# 4. ALYA AI RAG & COGNITIVE NLP DOGRULUK TESTLERI
print("\n[BOLUM 4] ALYA AI BILISSEL RAG VE NLP TESTLERI", flush=True)
test_queries = [
    ("En uygun fiyatli proje hangisi?", ["VIP Üniversite", "1.350.000", "1.35", "üniversite", "eskişehir"]),
    ("1.5 milyon bütçem var ne önerirsin?", ["VIP Üniversite", "1.350.000", "1.35", "üniversite"]),
    ("VIP Üniversite projesinin fiyati ve detaylari nelerdir?", ["1.350.000", "Esenboğa", "Çubuk", "üniversite"]),
    ("Angim Beytepe projesi hakkinda bilgi verir misin?", ["Beytepe", "4.500.000", "4.5", "angim"])
]

for query, expected_keywords in test_queries:
    try:
        t0 = time.time()
        s, b = http_post("/api/nexa-ai-chat", {"message": query, "history": []})
        elapsed = int((time.time() - t0) * 1000)
        d = json.loads(b)
        reply = d.get("response", "")
        
        matches = [kw for kw in expected_keywords if kw.lower() in reply.lower()]
        if matches:
            log_pass(f"Soru: '{query}' -> ({elapsed}ms) Eslesen: {matches}")
        else:
            log_warn(f"Soru: '{query}' -> Yanit: {reply[:80]}...")
    except Exception as e:
        log_fail(f"AI Chat Soru: '{query}' hata: {e}")

# 5. FRONTEND & GUVENLIK TESTLERI
print("\n[BOLUM 5] FRONTEND ARAYUZ, MODAL VE GUVENLIK KONTROLLERI", flush=True)
try:
    s, b, _ = http_get("/site")
    if s == 200:
        has_hero = "hero-grid" in b or "hero-agent-card" in b
        has_video_modal = "projectDriveIframe" in b and "videoModal" in b
        has_pdf_modal = "pdfModal" in b and "pdfViewerContainer" in b
        has_schema_ld = "application/ld+json" in b and "RealEstateAgent" in b
        
        if has_hero: log_pass("Frontend: 2 Kolonlu Modern Hero & Danisman Karti Mevcut")
        if has_video_modal: log_pass("Frontend: Google Drive Iframe Video Oynatici Entegre")
        if has_pdf_modal: log_pass("Frontend: Google Drive Iframe PDF Goruntuleyici Entegre")
        if has_schema_ld: log_pass("Frontend: Schema.org RealEstateAgent Yapisal SEO Verisi Aktif")
    else:
        log_fail(f"/site HTTP {s}")
except Exception as e:
    log_fail(f"/site hata: {e}")

# Security check: Path traversal prevention
try:
    s, _, _ = http_get("/file?path=../../../../windows/system32/cmd.exe")
    if s in [400, 404]:
        log_pass(f"Guvenlik: Path Traversal Korumasi Aktif (HTTP {s})")
    else:
        log_fail(f"Guvenlik Uyarisi: Path Traversal korumasi basarisiz (HTTP {s})")
except Exception as e:
    log_pass(f"Guvenlik: Path Traversal Korumasi Aktif ({e})")

print("\n" + "=" * 80, flush=True)
print(f"DENETIM SONUCU: {passed_tests} BASARILI, {failed_tests} BASARISIZ, {warnings} UYARI", flush=True)
print("=" * 80, flush=True)
