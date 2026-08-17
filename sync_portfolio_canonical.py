import sys
import json
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")
port_file = base / "nexa_portfolio_data.json"
map_file = base / "projects_map.json"

pmap = {}
if map_file.exists():
    with open(map_file, "r", encoding="utf-8") as f:
        for p in json.load(f):
            title = p.get("title") or p.get("name")
            if title:
                pmap[title.upper()] = p

# Load portfolio items
with open(port_file, "r", encoding="utf-8") as f:
    items = json.load(f)

for it in items:
    title = (it.get("title") or "").upper()
    
    # VIP ÜNİVERSİTE canonical fix
    if "ÜNİVERSİTE" in title or "UNIVERSITE" in title or it.get("id") == "cbvip-prj-20" or it.get("db_id") == 3:
        it["title"] = "VIP ÜNİVERSİTE"
        it["price_display"] = "1.350.000 TL"
        it["price_numeric"] = 1350000
        it["down_payment"] = "825.000 TL"
        it["room_info"] = "1+1"
        it["ilce"] = "Çubuk"
        it["mahalle"] = "Esenboğa"
        it["description"] = "Yıldırım Beyazıt Üniversitesi Kampüsü karşısında 257 adet 1+1 daire. 825.000 TL peşinat ile yüksek kiralama getirili prestijli yatırım projesi."
    
    # Match against projects_map.json
    matched_p = None
    for k, v in pmap.items():
        if k in title or title in k:
            matched_p = v
            break
            
    if matched_p and not it.get("price_display"):
        intel = matched_p.get("intelligence", {})
        it["price_display"] = matched_p.get("price_display") or intel.get("price_display") or ""
        it["price_numeric"] = matched_p.get("price_numeric") or intel.get("price") or 0
        it["down_payment"] = matched_p.get("down_payment") or intel.get("down_payment") or ""
        if not it.get("room_info"):
            rooms = matched_p.get("rooms") or matched_p.get("room_types") or []
            it["room_info"] = ", ".join(rooms) if isinstance(rooms, list) else str(rooms)

# Write back
with open(port_file, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Successfully synchronized {len(items)} items in nexa_portfolio_data.json!")
