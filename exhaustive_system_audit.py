import os
import sys
import json
import sqlite3
import time
import requests
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")
base_url = "http://localhost:5002"

results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "details": []
}

def log_check(test_name, success, msg=""):
    status = "PASS" if success else "FAIL"
    if success:
        results["passed"] += 1
    else:
        results["failed"] += 1
    print(f"[{status}] {test_name}: {msg}")
    results["details"].append({"name": test_name, "status": status, "msg": msg})

print("=" * 75)
print("EXHAUSTIVE DEEP SYSTEM AUDIT & REGRESSION VERIFICATION (360° CHECK)")
print("=" * 75)

# ─── 1. SERVER & ENDPOINT VERIFICATION ───
print("\n--- 1. API & ENDPOINTS TEST ---")

# 1.1 Healthz
try:
    r = requests.get(f"{base_url}/healthz", timeout=4)
    data = r.json()
    log_check("GET /healthz", r.status_code == 200 and data.get("status") == "ok", f"Assistant: {data.get('assistant')}")
except Exception as e:
    log_check("GET /healthz", False, str(e))

# 1.2 Config
try:
    r = requests.get(f"{base_url}/api/config", timeout=4)
    data = r.json()
    log_check("GET /api/config", r.status_code == 200 and data.get("assistant_name") == "Alya", f"Agent: {data.get('default_agent', {}).get('name')}")
except Exception as e:
    log_check("GET /api/config", False, str(e))

# 1.3 Projects API
try:
    r = requests.get(f"{base_url}/api/projects", timeout=4)
    pdata = r.json().get("data", [])
    log_check("GET /api/projects", r.status_code == 200 and len(pdata) >= 22, f"Total Projects: {len(pdata)}")
except Exception as e:
    log_check("GET /api/projects", False, str(e))

# 1.4 Listings API
try:
    r = requests.get(f"{base_url}/api/listings", timeout=4)
    ldata = r.json().get("data", [])
    log_check("GET /api/listings", r.status_code == 200 and len(ldata) > 0, f"Total Listings: {len(ldata)}")
except Exception as e:
    log_check("GET /api/listings", False, str(e))

# 1.5 Regions API
try:
    r = requests.get(f"{base_url}/api/nexa-regions", timeout=4)
    rdata = r.json()
    log_check("GET /api/nexa-regions", r.status_code == 200 and rdata.get("count", 0) >= 20, f"Total Regions/Projects: {rdata.get('count')}")
except Exception as e:
    log_check("GET /api/nexa-regions", False, str(e))

# 1.6 Appointments API
try:
    payload = {
        "name": "Audit Test User",
        "phone": "05339998877",
        "email": "audit@test.com",
        "preferred_datetime": "Pazartesi 15:00",
        "project_id": "cbvip-prj-20",
        "project_name": "VIP ÜNİVERSİTE",
        "notes": "Otomasyon denetim testi",
        "agent": "Yiğit Narin"
    }
    r = requests.post(f"{base_url}/api/appointments", json=payload, timeout=4)
    res = r.json()
    log_check("POST /api/appointments", r.status_code == 200 and res.get("success") is True, f"Lead ID: {res.get('lead_id')}")
except Exception as e:
    log_check("POST /api/appointments", False, str(e))

# 1.7 Site Page
try:
    r = requests.get(f"{base_url}/site", timeout=4)
    html = r.text
    has_hero_2col = "hero-grid-2col" in html
    has_budget_bar = "quick-budget-bar" in html
    has_appointment_modal = "appointmentModal" in html
    has_video_cloud = "playProjectVideo" in html
    all_ui = has_hero_2col and has_budget_bar and has_appointment_modal and has_video_cloud
    log_check("GET /site (HTML & UI Components)", r.status_code == 200 and all_ui, f"Length: {len(html)} chars | 2-Col Hero: {has_hero_2col} | Budget Bar: {has_budget_bar} | Appointment Modal: {has_appointment_modal}")
except Exception as e:
    log_check("GET /site", False, str(e))

# ─── 2. DATABASE INTEGRITY CHECK ───
print("\n--- 2. DATABASE (nexa_database.db) INTEGRITY CHECK ---")
db_path = base / "nexa_database.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check projects
cur.execute("SELECT COUNT(*) FROM projects")
cnt_proj = cur.fetchone()[0]
log_check("DB Table 'projects'", cnt_proj >= 30, f"{cnt_proj} rows found")

# Check VIP Üniversite price in DB
cur.execute("SELECT name, price_display, room_info, ilce, mahalle, ada_no, parsel_no FROM projects WHERE name LIKE '%ÜNİVERSİTE%' OR name LIKE '%UNIVERSITE%' OR id = 3")
vip_row = cur.fetchone()
if vip_row:
    v_dict = dict(vip_row)
    price_ok = "1.350.000" in str(v_dict.get("price_display"))
    log_check("DB VIP Üniversite Canonical Price", price_ok, f"Name='{v_dict.get('name')}', Price='{v_dict.get('price_display')}', Rooms='{v_dict.get('room_info')}', Loc='{v_dict.get('ilce')}/{v_dict.get('mahalle')}', Ada={v_dict.get('ada_no')}/{v_dict.get('parsel_no')}")
else:
    log_check("DB VIP Üniversite Canonical Price", False, "VIP Üniversite row not found in DB")

# Check customers / appointments in DB
cur.execute("SELECT COUNT(*) FROM customers")
cnt_cust = cur.fetchone()[0]
log_check("DB Table 'customers' (Lead capture)", cnt_cust > 0, f"{cnt_cust} registered appointments/leads")

# Check documents and chunks
cur.execute("SELECT COUNT(*) FROM documents")
cnt_docs = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM document_chunks")
cnt_chunks = cur.fetchone()[0]
log_check("DB Tables 'documents' & 'document_chunks'", cnt_docs > 700 and cnt_chunks > 1500, f"{cnt_docs} documents, {cnt_chunks} vector chunks")
conn.close()

# ─── 3. CANONICAL PRICE CONSISTENCY CHECK ───
print("\n--- 3. CANONICAL PRICE CONSISTENCY (SINGLE SOURCE OF TRUTH) ---")

# In projects_map.json
with open(base / "projects_map.json", "r", encoding="utf-8") as f:
    pmap = json.load(f)

def _norm(s):
    return (s or "").replace("İ", "i").replace("I", "ı").replace("ü", "u").replace("Ü", "u").lower()

vip_map = next((p for p in pmap if "univers" in _norm(p.get("title", "")) or "univers" in _norm(p.get("name", ""))), None)
if vip_map:
    intel = vip_map.get("intelligence", {})
    price_str = str(vip_map.get("price_display") or intel.get("price_display"))
    log_check("projects_map.json VIP Üniversite Price", "1.350.000" in price_str, f"Price: {price_str}, Peşinat: {vip_map.get('down_payment') or intel.get('down_payment')}")
else:
    log_check("projects_map.json VIP Üniversite Price", False, "Not found")

# In nexa_portfolio_data.json
with open(base / "nexa_portfolio_data.json", "r", encoding="utf-8") as f:
    pdata = json.load(f)

vip_pdata = next((p for p in pdata if "univers" in _norm(p.get("title", ""))), None)
if vip_pdata:
    price_str = str(vip_pdata.get("price_display"))
    log_check("nexa_portfolio_data.json VIP Üniversite Price", "1.350.000" in price_str, f"Price: {price_str}")
else:
    log_check("nexa_portfolio_data.json VIP Üniversite Price", False, "Not found")

# In nexa_project_summaries.json
with open(base / "nexa_project_summaries.json", "r", encoding="utf-8") as f:
    sdata = json.load(f)

vip_sum = sdata.get("VIP ÜNİVERSİTE", {})
if vip_sum:
    summary_text = vip_sum.get("summary", "")
    log_check("nexa_project_summaries.json VIP Üniversite Summary", "1.350.000" in summary_text and "1.650.000" not in summary_text, f"Contains 1.350.000 TL, zero 1.650.000 TL hallucination")
else:
    log_check("nexa_project_summaries.json VIP Üniversite Summary", False, "Not found in summaries cache")

# ─── 4. ALYA AI ENGINE QUERY & INTENT TEST ───
print("\n--- 4. ALYA AI NLP INTENT & MATCHING TESTS ---")
from nexa_ai_engine import process_nexa_query

test_queries = [
    ("En ucuz proje hangisi?", "1.350.000", "VIP ÜNİVERSİTE"),
    ("2 milyonun altında ne var?", "1.350.000", "VIP ÜNİVERSİTE"),
    ("VIP Üniversite projesinin fiyatı nedir?", "1.350.000", "VIP ÜNİVERSİTE"),
    ("Ankara 1.5 milyon bütçem var", "1.350.000", "VIP ÜNİVERSİTE"),
    ("Bu hafta projeleri yerinde görmek istiyorum randevu alabilir miyim?", "randevu", "lead_score >= 8"),
]

for q, expected_content, desc in test_queries:
    res = process_nexa_query(q)
    text = res.get("response", "")
    lead_s = res.get("lead_score", 3)
    projects_returned = res.get("projects", [])
    
    if "lead_score" in desc:
        success = lead_s >= 8
        log_check(f"Query: '{q}'", success, f"Lead Score: {lead_s} (Hot Lead Qualified)")
    else:
        success = expected_content in text or any(expected_content in str(p.get("price_display")) for p in projects_returned)
        top_project = projects_returned[0].get("title") if projects_returned else "None"
        log_check(f"Query: '{q}'", success, f"Top Match: {top_project} ({projects_returned[0].get('price_display') if projects_returned else ''})")

# ─── 5. VIDEO STREAMING PLAYBACK TEST ───
print("\n--- 5. VIDEO STREAMING & PLAYBACK TEST ---")
sample_pids = ["cbvip-prj-1", "cbvip-prj-2", "cbvip-prj-3", "cbvip-prj-4", "cbvip-prj-20"]
for pid in sample_pids:
    try:
        r = requests.get(f"{base_url}/stream/video/{pid}", headers={"Range": "bytes=0-1000"}, timeout=4)
        log_check(f"Video Stream /stream/video/{pid}", r.status_code in [200, 206], f"Status: {r.status_code}, Content-Type: {r.headers.get('Content-Type')}")
    except Exception as e:
        log_check(f"Video Stream /stream/video/{pid}", False, str(e))

print("\n" + "=" * 75)
print(f"AUDIT COMPLETED: {results['passed']} PASSED, {results['failed']} FAILED")
print("=" * 75)
