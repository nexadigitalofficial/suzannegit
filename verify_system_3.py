import sys
import os
import json
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(r"C:\Users\USER\Desktop\3")
print("=== VERIFYING FOLDER 3 SYSTEM INTEGRITY ===")

# 1. Config
cfg_file = BASE_DIR / "config.json"
if cfg_file.exists():
    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    print(f"[OK] config.json loaded: port={cfg.get('port')}, nexa_db_dir={cfg.get('nexa_db_dir')}, projeler_dir={cfg.get('projeler_dir')}")
else:
    print("[FAIL] config.json not found!")

# 2. projects_map.json
proj_file = BASE_DIR / "projects_map.json"
if proj_file.exists():
    with open(proj_file, "r", encoding="utf-8") as f:
        projects = json.load(f)
    print(f"[OK] projects_map.json loaded: {len(projects)} projects found.")
    for idx, p in enumerate(projects, 1):
        intel = p.get("intelligence", {})
        media = p.get("media", {})
        print(f"  {idx}. [{p.get('id')}] {p.get('title')} | Region: {intel.get('region')} | Price: {intel.get('price_display')}")
else:
    print("[FAIL] projects_map.json not found!")

# 3. Database
db_file = BASE_DIR / "nexa_database.db"
if db_file.exists():
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]
    print(f"[OK] nexa_database.db found ({db_file.stat().st_size} bytes), {len(tables)} tables: {', '.join(tables)}")
    conn.close()
else:
    print("[FAIL] nexa_database.db not found!")

# 4. Projeler Folder
proj_dir = BASE_DIR / "projeler"
if proj_dir.exists():
    subdirs = [d.name for d in proj_dir.iterdir() if d.is_dir()]
    print(f"[OK] Projeler folder found: {len(subdirs)} project folders: {', '.join(subdirs[:6])}...")
else:
    print("[FAIL] Projeler folder not found!")

# 5. Static Documents
docs_dir = BASE_DIR / "static" / "documents"
if docs_dir.exists():
    doc_files = list(docs_dir.iterdir())
    print(f"[OK] Static documents folder found: {len(doc_files)} files/folders.")
else:
    print("[FAIL] Static documents folder not found!")

# 6. Python modules
for mod in ["app", "nexa_ai_engine", "nexa_rag", "nexa_vector_rag", "nexa_data_importer", "fiyat_import"]:
    mod_file = BASE_DIR / f"{mod}.py"
    if mod_file.exists():
        print(f"[OK] {mod}.py exists ({mod_file.stat().st_size} bytes)")
    else:
        print(f"[FAIL] {mod}.py missing!")

print("\n=== SYSTEM VERIFICATION SUMMARY FINISHED ===")
