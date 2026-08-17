import sys
import json
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")
db_path = base / "nexa_database.db"

print("=== 1. UPDATING CANONICAL DATABASE PRICES (nexa_database.db) ===")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# VIP ÜNİVERSİTE Canonical Update:
cur.execute("""
    UPDATE projects 
    SET price_display = '₺1.350.000',
        room_info = '1+1',
        description = 'Yıldırım Beyazıt Üniversitesi Kampüsü karşısında 257 adet 1+1 daire. 825.000 TL peşinat ile kiralama garantili yatırım projesi.',
        ada_no = '190438',
        parsel_no = '15',
        tkgm_verified = 1
    WHERE id = 3 OR name LIKE '%ÜNİVERSİTE%' OR name LIKE '%UNIVERSITE%'
""")

conn.commit()
print(f"Updated VIP ÜNİVERSİTE in DB (rows affected: {cur.rowcount})")

# Verify all project prices in DB
cur.execute("SELECT id, name, price_display, room_info FROM projects WHERE id IN (1, 2, 3, 4, 5, 6, 9, 20)")
for r in cur.fetchall():
    print(f"  - DB Project ID {r[0]}: {r[1]} -> Price: {r[2]} ({r[3]})")
conn.close()

print("\n=== 2. UPDATING NEXA_PROJECT_SUMMARIES.JSON ===")
sum_file = base / "nexa_project_summaries.json"
sdata = {}
if sum_file.exists():
    try:
        sdata = json.loads(sum_file.read_text(encoding="utf-8"))
    except Exception:
        sdata = {}

sdata["VIP ÜNİVERSİTE"] = {
    "summary": "- VIP ÜNİVERSİTE Projesi, Ankara Çubuk Esenboğa'da, Yıldırım Beyazıt Üniversitesi Kampüsü tam karşısında yer almaktadır.\n- Zemin+8 katlı tek blokta toplam 257 adet 1+1 daireden oluşan yüksek prim potansiyelli konut projesidir.\n- Güncel başlangıç fiyatı 1.350.000 TL olup, 825.000 TL peşinat ve esnek ödeme planı sunulmaktadır.\n- Yerden ısıtma ve modern donanımı ile öğrenci/akademisyen kiralama talebi garantilidir.\n- Tapu bilgisi 190438 Ada, 15 Parsel olarak TKGM sisteminde kayıtlı ve onaylıdır.",
    "project_id": 3,
    "price_display": "1.350.000 TL",
    "down_payment": "825.000 TL",
    "rooms": "1+1",
    "units": 257,
    "ts": 1786485900.0
}

with open(sum_file, "w", encoding="utf-8") as f:
    json.dump(sdata, f, ensure_ascii=False, indent=2)
print("Updated nexa_project_summaries.json with canonical VIP Üniversite data!")

print("\n=== 3. UPDATING PROJECTS_MAP.JSON (CANONICAL PROJECTS) ===")
proj_map_file = base / "projects_map.json"
projects = []
if proj_map_file.exists():
    try:
        projects = json.loads(proj_map_file.read_text(encoding="utf-8"))
    except Exception:
        projects = []

# Ensure VIP ÜNİVERSİTE is present in projects_map.json
vip_univ_found = False
for p in projects:
    if "üniversite" in p.get("title", "").lower() or "universite" in p.get("title", "").lower() or p.get("id") == "cbvip-prj-20" or "vip üniversite" in p.get("name", "").lower():
        p["title"] = "VIP ÜNİVERSİTE"
        p["name"] = "VIP ÜNİVERSİTE"
        p["price_display"] = "1.350.000 TL"
        p["price_numeric"] = 1350000
        p["down_payment"] = "825.000 TL"
        p["rooms"] = ["1+1"]
        p["room_types"] = ["1+1"]
        p["location"] = "Esenboğa / Çubuk"
        p["intelligence"] = {
            "region": "Çubuk / Esenboğa",
            "price": 1350000,
            "price_display": "1.350.000 TL",
            "down_payment": "825.000 TL",
            "price_per_sqm": 22500,
            "region_average": 26000,
            "price_diff_percent": -13.5,
            "investment_score": 96,
            "pricing_score": "En Uygun Fiyatlı Yatırım Projesi (1.350.000 TL)",
            "suitable_for": ["kiralik", "yatirim", "ogrenci"],
            "pros": ["Yıldırım Beyazıt Üniversitesi karşısı", "1.350.000 TL rakipsiz başlangıç fiyatı", "825.000 TL peşinat kolaylığı", "257 adet 1+1 daire"],
            "comparison_note": "1.5 Milyon TL ve 2 Milyon TL altı bütçelerde en yüksek kiralama katsayısına ve amortisman hızına sahip projedir."
        }
        vip_univ_found = True

if not vip_univ_found:
    # Add VIP Üniversite as project entry
    vip_entry = {
        "id": "cbvip-prj-vip-universite",
        "db_id": 3,
        "title": "VIP ÜNİVERSİTE",
        "name": "VIP ÜNİVERSİTE",
        "folder_name": "VIP_UNIVERSITE",
        "location": "Esenboğa / Çubuk",
        "developer": "Coldwell Banker VIP & Akademi",
        "status": "Satışta",
        "price_display": "1.350.000 TL",
        "price_numeric": 1350000,
        "down_payment": "825.000 TL",
        "rooms": ["1+1"],
        "room_types": ["1+1"],
        "thumbnail": "/static/img/video_thumbs/video_thumb_20.jpg",
        "image": "/static/img/video_thumbs/video_thumb_20.jpg",
        "has_video": True,
        "has_presentation": True,
        "media": {
            "promo_video_url": "/stream/video/cbvip-prj-20",
            "slideshow_video_url": "/stream/video/cbvip-prj-20",
            "pdf_url": "/static/documents/SUNUM_VIP_UNIVERSITE.pdf",
            "thumbnail_url": "/static/img/video_thumbs/video_thumb_20.jpg"
        },
        "intelligence": {
            "region": "Çubuk / Esenboğa",
            "price": 1350000,
            "price_display": "1.350.000 TL",
            "down_payment": "825.000 TL",
            "price_per_sqm": 22500,
            "region_average": 26000,
            "price_diff_percent": -13.5,
            "investment_score": 96,
            "pricing_score": "En Uygun Fiyatlı Yatırım Projesi (1.350.000 TL)",
            "suitable_for": ["kiralik", "yatirim", "ogrenci"],
            "pros": ["Yıldırım Beyazıt Üniversitesi karşısı", "1.350.000 TL rakipsiz başlangıç fiyatı", "825.000 TL peşinat kolaylığı", "257 adet 1+1 daire"],
            "comparison_note": "1.5 Milyon TL ve 2 Milyon TL altı bütçelerde en yüksek kiralama katsayısına ve amortisman hızına sahip projedir."
        }
    }
    projects.insert(0, vip_entry)

with open(proj_map_file, "w", encoding="utf-8") as f:
    json.dump(projects, f, ensure_ascii=False, indent=2)
print(f"Updated projects_map.json ({len(projects)} projects total)")

print("\n=== 4. UPDATING NEXA_PORTFOLIO_DATA.JSON ===")
port_file = base / "nexa_portfolio_data.json"
if port_file.exists():
    try:
        pdata = json.loads(port_file.read_text(encoding="utf-8"))
        for item in pdata:
            if "üniversite" in item.get("title", "").lower() or "universite" in item.get("title", "").lower():
                item["price_display"] = "1.350.000 TL"
                item["price_numeric"] = 1350000
                item["room_info"] = "1+1"
        with open(port_file, "w", encoding="utf-8") as f:
            json.dump(pdata, f, ensure_ascii=False, indent=2)
        print("Updated nexa_portfolio_data.json with canonical prices!")
    except Exception as e:
        print("Portfolio data update skipped:", e)

print("\n=== SYNCHRONIZATION FINISHED SUCCESSFULLY ===")
