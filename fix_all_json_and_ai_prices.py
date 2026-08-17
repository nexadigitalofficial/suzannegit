import sys
import json
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")

print("=== FIXING ALL JSON DATA AND CANONICAL PRICES ===")

# Canonical definitions for all 22 projects
CANONICAL = {
    "cbvip-prj-1": {
        "title": "ANGİM BEYTEPE",
        "price_display": "4.500.000 - 22.890.000 TL",
        "price_numeric": 4500000,
        "price_min": 4500000,
        "price_max": 22890000,
        "down_payment": "",
        "il": "Ankara", "ilce": "Çankaya", "mahalle": "Beytepe",
        "room_info": "1+1, 2+1, 3+1, 4+1, 5+1, 6+1",
        "ada_no": "80907", "parsel_no": "1", "tkgm_verified": True
    },
    "cbvip-prj-2": {
        "title": "ANKAPORT - SARAY",
        "price_display": "3.040.000 - 8.350.000 TL",
        "price_numeric": 3040000,
        "price_min": 3040000,
        "price_max": 8350000,
        "down_payment": "1.520.000 TL",
        "il": "Ankara", "ilce": "Pursaklar", "mahalle": "Saray",
        "room_info": "1+1, 2+1, 3+1",
        "ada_no": "96400", "parsel_no": "4", "tkgm_verified": True
    },
    "cbvip-prj-3": {
        "title": "EVART YALIKAVAK",
        "price_display": "14.500.000 TL",
        "price_numeric": 14500000,
        "price_min": 14500000,
        "price_max": 14500000,
        "down_payment": "7.250.000 TL",
        "il": "Muğla", "ilce": "Bodrum", "mahalle": "Yalıkavak",
        "room_info": "2+1, 3+1 Villa & Rezidans",
        "ada_no": "624", "parsel_no": "18", "tkgm_verified": True
    },
    "cbvip-prj-4": {
        "title": "GRANDE YAŞAMKENT",
        "price_display": "3.000.000 - 4.000.000 TL",
        "price_numeric": 3000000,
        "price_min": 3000000,
        "price_max": 4000000,
        "down_payment": "1.500.000 TL",
        "il": "Ankara", "ilce": "Etimesgut", "mahalle": "Yapracık",
        "room_info": "1+1, 2+1",
        "ada_no": "49912", "parsel_no": "4", "tkgm_verified": True
    },
    "cbvip-prj-5": {
        "title": "GÖKDEMİR İMZA",
        "price_display": "3.900.000 - 8.000.000 TL",
        "price_numeric": 3900000,
        "price_min": 3900000,
        "price_max": 8000000,
        "down_payment": "1.950.000 TL",
        "il": "Ankara", "ilce": "Gölbaşı", "mahalle": "Kızılcaşar",
        "room_info": "1+1, 2+1, 3+1",
        "ada_no": "118274", "parsel_no": "2", "tkgm_verified": True
    },
    "cbvip-prj-6": {
        "title": "IDEA - START BRAVO",
        "price_display": "2.100.000 - 3.200.000 TL",
        "price_numeric": 2100000,
        "price_min": 2100000,
        "price_max": 3200000,
        "down_payment": "1.050.000 TL",
        "il": "Ankara", "ilce": "Etimesgut", "mahalle": "Bağlıca",
        "room_info": "1+1, 2+1",
        "ada_no": "47285", "parsel_no": "1", "tkgm_verified": True
    },
    "cbvip-prj-7": {
        "title": "MONZA EYLÜL CONCEPT",
        "price_display": "2.800.000 - 3.900.000 TL",
        "price_numeric": 2800000,
        "price_min": 2800000,
        "price_max": 3900000,
        "down_payment": "1.400.000 TL",
        "il": "Ankara", "ilce": "Yenimahalle", "mahalle": "Çakırlar",
        "room_info": "1+1, 2+1",
        "ada_no": "63452", "parsel_no": "7", "tkgm_verified": True
    },
    "cbvip-prj-8": {
        "title": "MONZA MOON",
        "price_display": "2.650.000 - 3.750.000 TL",
        "price_numeric": 2650000,
        "price_min": 2650000,
        "price_max": 3750000,
        "down_payment": "1.325.000 TL",
        "il": "Ankara", "ilce": "Yenimahalle", "mahalle": "Batıkent",
        "room_info": "1+1, 2+1",
        "ada_no": "63452", "parsel_no": "8", "tkgm_verified": True
    },
    "cbvip-prj-9": {
        "title": "NARÇİN RONYA CITY - 1",
        "price_display": "3.400.000 - 4.330.000 TL",
        "price_numeric": 3400000,
        "price_min": 3400000,
        "price_max": 4330000,
        "down_payment": "1.700.000 TL",
        "il": "Ankara", "ilce": "Etimesgut", "mahalle": "Yukarıyurtçu",
        "room_info": "1+1, 2+1",
        "ada_no": "48820", "parsel_no": "3", "tkgm_verified": True
    },
    "cbvip-prj-10": {
        "title": "NEVA - START BRAVO",
        "price_display": "2.200.000 - 3.400.000 TL",
        "price_numeric": 2200000,
        "price_min": 2200000,
        "price_max": 3400000,
        "down_payment": "1.100.000 TL",
        "il": "Ankara", "ilce": "Etimesgut", "mahalle": "Bağlıca",
        "room_info": "1+1, 2+1",
        "ada_no": "47285", "parsel_no": "2", "tkgm_verified": True
    },
    "cbvip-prj-11": {
        "title": "S POINT - VIP SARAY",
        "price_display": "1.990.000 - 4.000.000 TL",
        "price_numeric": 1990000,
        "price_min": 1990000,
        "price_max": 4000000,
        "down_payment": "995.000 TL",
        "il": "Ankara", "ilce": "Pursaklar", "mahalle": "Saray",
        "room_info": "1+1, 2+1",
        "ada_no": "96400", "parsel_no": "6", "tkgm_verified": True
    },
    "cbvip-prj-12": {
        "title": "TRIOLE YAŞAM",
        "price_display": "2.950.000 - 4.200.000 TL",
        "price_numeric": 2950000,
        "price_min": 2950000,
        "price_max": 4200000,
        "down_payment": "1.475.000 TL",
        "il": "Ankara", "ilce": "Etimesgut", "mahalle": "Eryaman",
        "room_info": "1+1, 2+1",
        "ada_no": "48110", "parsel_no": "2", "tkgm_verified": True
    },
    "cbvip-prj-13": {
        "title": "NEST İNCEK",
        "price_display": "5.500.000 - 9.800.000 TL",
        "price_numeric": 5500000,
        "price_min": 5500000,
        "price_max": 9800000,
        "down_payment": "2.750.000 TL",
        "il": "Ankara", "ilce": "Gölbaşı", "mahalle": "İncek",
        "room_info": "2+1, 3+1, 4+1",
        "ada_no": "115200", "parsel_no": "1", "tkgm_verified": True
    },
    "cbvip-prj-14": {
        "title": "BORDO YAŞAM",
        "price_display": "2.450.000 - 3.850.000 TL",
        "price_numeric": 2450000,
        "price_min": 2450000,
        "price_max": 3850000,
        "down_payment": "1.225.000 TL",
        "il": "Ankara", "ilce": "Sincan", "mahalle": "Yenikent",
        "room_info": "1+1, 2+1",
        "ada_no": "102400", "parsel_no": "5", "tkgm_verified": True
    },
    "cbvip-prj-15": {
        "title": "EXCELANCE VADİ",
        "price_display": "6.200.000 - 12.500.000 TL",
        "price_numeric": 6200000,
        "price_min": 6200000,
        "price_max": 12500000,
        "down_payment": "3.100.000 TL",
        "il": "Ankara", "ilce": "Çankaya", "mahalle": "Dikmen Vadi",
        "room_info": "2+1, 3+1, 4+1",
        "ada_no": "29100", "parsel_no": "4", "tkgm_verified": True
    },
    "cbvip-prj-16": {
        "title": "EXCELANCE BEYTEPE",
        "price_display": "7.500.000 - 16.000.000 TL",
        "price_numeric": 7500000,
        "price_min": 7500000,
        "price_max": 16000000,
        "down_payment": "3.750.000 TL",
        "il": "Ankara", "ilce": "Çankaya", "mahalle": "Beytepe",
        "room_info": "3+1, 4+1, 5+1",
        "ada_no": "80910", "parsel_no": "3", "tkgm_verified": True
    },
    "cbvip-prj-17": {
        "title": "GÖKDEMİR STAR",
        "price_display": "3.200.000 - 4.600.000 TL",
        "price_numeric": 3200000,
        "price_min": 3200000,
        "price_max": 4600000,
        "down_payment": "1.600.000 TL",
        "il": "Ankara", "ilce": "Etimesgut", "mahalle": "Yaşamkent",
        "room_info": "1+1, 2+1",
        "ada_no": "49915", "parsel_no": "2", "tkgm_verified": True
    },
    "cbvip-prj-18": {
        "title": "JOVEN PORT",
        "price_display": "2.850.000 - 4.100.000 TL",
        "price_numeric": 2850000,
        "price_min": 2850000,
        "price_max": 4100000,
        "down_payment": "1.425.000 TL",
        "il": "Ankara", "ilce": "Pursaklar", "mahalle": "Saray",
        "room_info": "1+1, 2+1",
        "ada_no": "96410", "parsel_no": "1", "tkgm_verified": True
    },
    "cbvip-prj-19": {
        "title": "JOVEN KAMPÜS",
        "price_display": "1.950.000 - 2.800.000 TL",
        "price_numeric": 1950000,
        "price_min": 1950000,
        "price_max": 2800000,
        "down_payment": "975.000 TL",
        "il": "Ankara", "ilce": "Çubuk", "mahalle": "Esenboğa",
        "room_info": "1+1",
        "ada_no": "190440", "parsel_no": "8", "tkgm_verified": True
    },
    "cbvip-prj-20": {
        "title": "VIP ÜNİVERSİTE",
        "price_display": "1.350.000 TL",
        "price_numeric": 1350000,
        "price_min": 1350000,
        "price_max": 1350000,
        "down_payment": "825.000 TL",
        "il": "Ankara", "ilce": "Çubuk", "mahalle": "Esenboğa",
        "room_info": "1+1",
        "ada_no": "190438", "parsel_no": "15", "tkgm_verified": True,
        "description": "Yıldırım Beyazıt Üniversitesi Kampüsü tam karşısında 257 adet 1+1 daire. 825.000 TL peşinat ile yüksek kiralama getirili prestijli yatırım projesi."
    },
    "cbvip-prj-21": {
        "title": "SMD TWIN",
        "price_display": "3.600.000 - 5.200.000 TL",
        "price_numeric": 3600000,
        "price_min": 3600000,
        "price_max": 5200000,
        "down_payment": "1.800.000 TL",
        "il": "Ankara", "ilce": "Yenimahalle", "mahalle": "Batı Sitesi",
        "room_info": "2+1, 3+1",
        "ada_no": "62100", "parsel_no": "5", "tkgm_verified": True
    },
    "cbvip-prj-22": {
        "title": "SMD PROTOKOL",
        "price_display": "4.200.000 - 6.800.000 TL",
        "price_numeric": 4200000,
        "price_min": 4200000,
        "price_max": 6800000,
        "down_payment": "2.100.000 TL",
        "il": "Ankara", "ilce": "Pursaklar", "mahalle": "Protokol Yolu",
        "room_info": "2+1, 3+1, 4+1",
        "ada_no": "96450", "parsel_no": "2", "tkgm_verified": True
    }
}

# 1. Update projects_map.json
map_file = base / "projects_map.json"
with open(map_file, "r", encoding="utf-8") as f:
    projects = json.load(f)

for p in projects:
    pid = p.get("id")
    if pid in CANONICAL:
        c = CANONICAL[pid]
        p["title"] = c["title"]
        p["name"] = c["title"]
        p["price_display"] = c["price_display"]
        p["price_numeric"] = c["price_numeric"]
        p["price_min"] = c["price_min"]
        p["price_max"] = c["price_max"]
        p["down_payment"] = c["down_payment"]
        p["il"] = c["il"]
        p["ilce"] = c["ilce"]
        p["mahalle"] = c["mahalle"]
        p["location"] = f"{c['ilce']}, {c['il']}"
        p["room_info"] = c["room_info"]
        p["ada_no"] = c["ada_no"]
        p["parsel_no"] = c["parsel_no"]
        p["tkgm_verified"] = c["tkgm_verified"]
        if "description" in c:
            p["description"] = c["description"]
        
        intel = p.setdefault("intelligence", {})
        intel["price"] = c["price_numeric"]
        intel["price_display"] = c["price_display"]
        intel["down_payment"] = c["down_payment"]
        intel["region"] = f"{c['ilce']}, {c['il']}"

with open(map_file, "w", encoding="utf-8") as f:
    json.dump(projects, f, ensure_ascii=False, indent=2)
print("1. projects_map.json updated with UTF-8 and canonical values!")

# 2. Update nexa_portfolio_data.json
port_file = base / "nexa_portfolio_data.json"
with open(port_file, "r", encoding="utf-8") as f:
    items = json.load(f)

for it in items:
    pid = it.get("id")
    if pid in CANONICAL:
        c = CANONICAL[pid]
        it["title"] = c["title"]
        it["price_display"] = c["price_display"]
        it["price_numeric"] = c["price_numeric"]
        it["down_payment"] = c["down_payment"]
        it["il"] = c["il"]
        it["ilce"] = c["ilce"]
        it["mahalle"] = c["mahalle"]
        it["room_info"] = c["room_info"]
        it["ada_no"] = c["ada_no"]
        it["parsel_no"] = c["parsel_no"]
        it["tkgm_verified"] = c["tkgm_verified"]
        if "description" in c:
            it["description"] = c["description"]

with open(port_file, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print("2. nexa_portfolio_data.json updated with UTF-8 and canonical values!")

# 3. Update nexa_database.db
db_path = Path(r"C:\Users\USER\Desktop\NEXA_PRIME_v2_ENTERPRISE\nexa_database.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

for pid, c in CANONICAL.items():
    cur.execute("""
        UPDATE projects SET
            name = ?,
            price_display = ?,
            il = ?,
            ilce = ?,
            mahalle = ?,
            location = ?,
            room_info = ?,
            ada_no = ?,
            parsel_no = ?,
            tkgm_verified = ?
        WHERE id = ? OR name LIKE ?
    """, (
        c["title"],
        c["price_display"],
        c["il"],
        c["ilce"],
        c["mahalle"],
        f"{c['ilce']}, {c['il']}",
        c["room_info"],
        c["ada_no"],
        c["parsel_no"],
        1 if c["tkgm_verified"] else 0,
        int(pid.replace("cbvip-prj-", "")),
        f"%{c['title'][:6]}%"
    ))

conn.commit()
conn.close()
print("3. nexa_database.db updated with canonical values!")

print("=== ALL PRICE DATA FULLY SYNCHRONIZED ===")
