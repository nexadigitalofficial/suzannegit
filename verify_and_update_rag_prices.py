import sys
import json
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = Path(r"C:\Users\USER\Desktop\3")
db_path = base / "nexa_database.db"

print("=== 1. DATABASE PROJECTS (projects table) ===")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, name, price_display, room_info, il, ilce, mahalle FROM projects ORDER BY id").fetchall()
for r in rows:
    p = dict(r)
    print(f" ID: {p['id']:>2} | Name: {p['name']:35} | Price: {str(p.get('price_display')):20} | Rooms: {str(p.get('room_info')):10} | Loc: {p.get('ilce')}/{p.get('mahalle')}")
conn.close()

print("\n=== 2. PROJECTS_MAP.JSON ===")
with open(base / "projects_map.json", "r", encoding="utf-8") as f:
    pmap = json.load(f)
for p in pmap:
    intel = p.get("intelligence", {})
    print(f" ID: {p.get('id'):15} | Title: {p.get('title'):30} | Price: {intel.get('price_display'):18} | Region: {intel.get('region')}")

print("\n=== 3. NEXA PROJECT SUMMARIES & PRICES JSON ===")
sum_file = base / "nexa_project_summaries.json"
if sum_file.exists():
    with open(sum_file, "r", encoding="utf-8") as f:
        sdata = json.load(f)
    print(f"Summaries cached for {len(sdata)} projects:")
    for k, v in list(sdata.items())[:6]:
        print(f"  * {k}: {v.get('summary', '')[:90]}...")
