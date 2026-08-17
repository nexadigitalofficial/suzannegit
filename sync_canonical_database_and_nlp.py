import sys
import json
import re
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")

# 1. Update nexa_ai_engine.py
ai_engine_path = base / "nexa_ai_engine.py"
ai_code = ai_engine_path.read_text(encoding="utf-8")

# Fix price_numeric and price_range in nexa_ai_engine.py to use item's price_numeric/price_min/price_max directly
price_helper_replacement = """def price_numeric(item):
    if item.get("price_numeric") and isinstance(item.get("price_numeric"), (int, float)) and item.get("price_numeric") > 0:
        return int(item["price_numeric"])
    pd = item.get("price_display") or ""
    m = re.search(r'([\\d][\\d.,]*)\\s*(?:₺|TL|lira)|(?:₺|TL)\\s*([\\d][\\d.,]*)', pd, re.I)
    if not m:
        m2 = re.search(r'([\\d][\\d.,]*)', pd)
        if not m2:
            return None
        return _norm_price_num(m2.group(1))
    return _norm_price_num(m.group(1) or m.group(2))


def price_range(item):
    if item.get("price_min") and item.get("price_max"):
        return int(item["price_min"]), int(item["price_max"])
    if item.get("price_numeric"):
        return int(item["price_numeric"]), int(item.get("price_max") or item["price_numeric"])
    pd = item.get("price_display") or ""
    nums = []
    for m in re.finditer(r'([\\d][\\d.,]*)\\s*(?:₺|TL|lira)|(?:₺|TL)\\s*([\\d][\\d.,]*)', pd, re.I):
        v = _norm_price_num(m.group(1) or m.group(2))
        if v:
            nums.append(v)
    if not nums:
        return None, None
    return min(nums), max(nums)"""

ai_code = re.sub(r'def price_numeric\(item\):.*?return min\(nums\), max\(nums\)', price_helper_replacement, ai_code, flags=re.DOTALL)
ai_engine_path.write_text(ai_code, encoding="utf-8")
print("1. nexa_ai_engine.py price helpers updated!")

# 2. Synchronize nexa_portfolio_data.json and projects_map.json
CANONICAL_LIST = [
    {
        "id": "cbvip-prj-20",
        "title": "VIP ÜNİVERSİTE",
        "price_display": "1.350.000 TL",
        "price_numeric": 1350000, "price_min": 1350000, "price_max": 1350000,
        "down_payment": "825.000 TL",
        "il": "Ankara", "ilce": "Çubuk", "mahalle": "Esenboğa", "location": "Çubuk, Ankara",
        "room_info": "1+1", "rooms": ["1+1"],
        "ada_no": "190438", "parsel_no": "15", "tkgm_verified": True,
        "description": "Yıldırım Beyazıt Üniversitesi Kampüsü tam karşısında 257 adet 1+1 daire. 825.000 TL peşinat ile yüksek kiralama getirili prestijli yatırım projesi."
    },
    {
        "id": "cbvip-prj-1",
        "title": "ANGİM BEYTEPE",
        "price_display": "4.500.000 - 22.890.000 TL",
        "price_numeric": 4500000, "price_min": 4500000, "price_max": 22890000,
        "down_payment": "2.250.000 TL",
        "il": "Ankara", "ilce": "Çankaya", "mahalle": "Beytepe", "location": "Çankaya, Ankara",
        "room_info": "1+1, 2+1, 3+1, 4+1, 5+1, 6+1", "rooms": ["1+1", "2+1", "3+1", "4+1", "5+1", "6+1"],
        "ada_no": "80907", "parsel_no": "1", "tkgm_verified": True,
        "description": "Beytepe lüks aksında prestijli karma yaşam projesi."
    },
    {
        "id": "cbvip-prj-2",
        "title": "ANKAPORT - SARAY",
        "price_display": "3.040.000 - 8.350.000 TL",
        "price_numeric": 3040000, "price_min": 3040000, "price_max": 8350000,
        "down_payment": "1.520.000 TL",
        "il": "Ankara", "ilce": "Pursaklar", "mahalle": "Saray", "location": "Pursaklar, Ankara",
        "room_info": "1+1, 2+1, 3+1", "rooms": ["1+1", "2+1", "3+1"],
        "ada_no": "96400", "parsel_no": "4", "tkgm_verified": True
    },
    {
        "id": "cbvip-prj-3",
        "title": "EVART YALIKAVAK",
        "price_display": "14.500.000 TL",
        "price_numeric": 14500000, "price_min": 14500000, "price_max": 14500000,
        "down_payment": "7.250.000 TL",
        "il": "Muğla", "ilce": "Bodrum", "mahalle": "Yalıkavak", "location": "Bodrum, Muğla",
        "room_info": "2+1, 3+1 Villa & Rezidans", "rooms": ["2+1", "3+1"],
        "ada_no": "624", "parsel_no": "18", "tkgm_verified": True
    },
    {
        "id": "cbvip-prj-4",
        "title": "GRANDE YAŞAMKENT",
        "price_display": "3.000.000 - 4.000.000 TL",
        "price_numeric": 3000000, "price_min": 3000000, "price_max": 4000000,
        "down_payment": "1.500.000 TL",
        "il": "Ankara", "ilce": "Etimesgut", "mahalle": "Yapracık", "location": "Etimesgut, Ankara",
        "room_info": "1+1, 2+1", "rooms": ["1+1", "2+1"],
        "ada_no": "49912", "parsel_no": "4", "tkgm_verified": True
    },
    {
        "id": "cbvip-prj-5",
        "title": "GÖKDEMİR İMZA",
        "price_display": "3.900.000 - 8.000.000 TL",
        "price_numeric": 3900000, "price_min": 3900000, "price_max": 8000000,
        "down_payment": "1.950.000 TL",
        "il": "Ankara", "ilce": "Gölbaşı", "mahalle": "Kızılcaşar", "location": "Gölbaşı, Ankara",
        "room_info": "1+1, 2+1, 3+1", "rooms": ["1+1", "2+1", "3+1"],
        "ada_no": "118274", "parsel_no": "2", "tkgm_verified": True
    }
]

canonical_by_id = {c["id"]: c for c in CANONICAL_LIST}

# Update projects_map.json
map_file = base / "projects_map.json"
with open(map_file, "r", encoding="utf-8") as f:
    projects = json.load(f)

for p in projects:
    pid = p.get("id")
    if pid in canonical_by_id:
        c = canonical_by_id[pid]
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
        p["location"] = c["location"]
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

with open(map_file, "w", encoding="utf-8") as f:
    json.dump(projects, f, ensure_ascii=False, indent=2)

# Update nexa_portfolio_data.json
port_file = base / "nexa_portfolio_data.json"
with open(port_file, "r", encoding="utf-8") as f:
    items = json.load(f)

for it in items:
    pid = it.get("id")
    if pid in canonical_by_id:
        c = canonical_by_id[pid]
        it["title"] = c["title"]
        it["price_display"] = c["price_display"]
        it["price_numeric"] = c["price_numeric"]
        it["price_min"] = c["price_min"]
        it["price_max"] = c["price_max"]
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

print("2. JSON data files successfully synchronized!")
