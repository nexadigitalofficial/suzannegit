import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")

# Load projects_map.json
with open(base / "projects_map.json", "r", encoding="utf-8") as f:
    projects = json.load(f)

# Update projects
for p in projects:
    pid = p.get("id")
    title = (p.get("title") or p.get("name") or "").upper()
    
    if "ÜNİVERSİTE" in title or "UNIVERSITE" in title or pid == "cbvip-prj-20":
        p["title"] = "VIP ÜNİVERSİTE"
        p["name"] = "VIP ÜNİVERSİTE"
        p["price_display"] = "1.350.000 TL"
        p["price_numeric"] = 1350000
        p["price_min"] = 1350000
        p["price_max"] = 1350000
        p["down_payment"] = "825.000 TL"
        p["ilce"] = "Çubuk"
        p["mahalle"] = "Esenboğa"
        p["location"] = "Çubuk, Ankara"
        p["room_info"] = "1+1"
        p["ada_no"] = "190438"
        p["parsel_no"] = "15"
        p["tkgm_verified"] = True
        intel = p.setdefault("intelligence", {})
        intel["price"] = 1350000
        intel["price_display"] = "1.350.000 TL"
        intel["down_payment"] = "825.000 TL"
        intel["region"] = "Çubuk, Ankara"

    elif "BEYTEPE" in title and "ANG" in title or pid == "cbvip-prj-1":
        p["title"] = "ANGİM BEYTEPE"
        p["name"] = "ANGİM BEYTEPE"
        p["price_display"] = "4.500.000 - 22.890.000 TL"
        p["price_numeric"] = 4500000
        p["price_min"] = 4500000
        p["price_max"] = 22890000
        p["ilce"] = "Çankaya"
        p["mahalle"] = "Beytepe"
        p["location"] = "Çankaya, Ankara"
        intel = p.setdefault("intelligence", {})
        intel["price"] = 4500000
        intel["price_display"] = "4.500.000 - 22.890.000 TL"

    elif "WM" in title or pid == "cbvip-prj-2":
        if p.get("title") == "WM - PRIME" or "PRIME" in title:
            p["price_display"] = "1.799.000 TL"
            p["price_numeric"] = 1799000
            p["price_min"] = 1799000
            p["price_max"] = 1799000

with open(base / "projects_map.json", "w", encoding="utf-8") as f:
    json.dump(projects, f, ensure_ascii=False, indent=2)

# Load and update nexa_portfolio_data.json
with open(base / "nexa_portfolio_data.json", "r", encoding="utf-8") as f:
    items = json.load(f)

for it in items:
    pid = it.get("id")
    title = (it.get("title") or "").upper()
    
    if "ÜNİVERSİTE" in title or "UNIVERSITE" in title or pid == "cbvip-prj-20":
        it["title"] = "VIP ÜNİVERSİTE"
        it["price_display"] = "1.350.000 TL"
        it["price_numeric"] = 1350000
        it["price_min"] = 1350000
        it["price_max"] = 1350000
        it["down_payment"] = "825.000 TL"
        it["ilce"] = "Çubuk"
        it["mahalle"] = "Esenboğa"
        it["room_info"] = "1+1"
        it["ada_no"] = "190438"
        it["parsel_no"] = "15"
        it["tkgm_verified"] = True

    elif "BEYTEPE" in title and "ANG" in title or pid == "cbvip-prj-1":
        it["title"] = "ANGİM BEYTEPE"
        it["price_display"] = "4.500.000 - 22.890.000 TL"
        it["price_numeric"] = 4500000
        it["price_min"] = 4500000
        it["price_max"] = 22890000
        it["ilce"] = "Çankaya"
        it["mahalle"] = "Beytepe"

with open(base / "nexa_portfolio_data.json", "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print("projects_map.json and nexa_portfolio_data.json updated cleanly!")
