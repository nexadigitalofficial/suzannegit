import sys
import os
import shutil
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

NEXA_DIR = Path(r"C:\Users\USER\Desktop\NEXA_PRIME_v2_ENTERPRISE")
SUZANNE_PROJELER = Path(r"C:\Users\USER\Desktop\suzanne\projeler")
DIR_3 = Path(r"C:\Users\USER\Desktop\3")

print("=== CHECKING NEXA_PRIME_v2_ENTERPRISE ===")
db_path = NEXA_DIR / "nexa_database.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print(f"nexa_database.db found ({db_path.stat().st_size} bytes), tables:")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM '{t[0]}'")
        cnt = cur.fetchone()[0]
        print(f"  - {t[0]}: {cnt} rows")
    conn.close()
else:
    print("nexa_database.db NOT found!")

print("\n=== COPYING NEXA DATABASE TO 3 ===")
dest_db = DIR_3 / "nexa_database.db"
if db_path.exists():
    shutil.copy2(db_path, dest_db)
    print(f"Copied nexa_database.db to {dest_db}")
    for ext in ["-shm", "-wal"]:
        f_ext = NEXA_DIR / f"nexa_database.db{ext}"
        if f_ext.exists():
            shutil.copy2(f_ext, DIR_3 / f"nexa_database.db{ext}")
            print(f"Copied {f_ext.name} to 3")

print("\n=== COPYING PROJELER TO 3/projeler ===")
dest_proj = DIR_3 / "projeler"
dest_proj.mkdir(exist_ok=True)

if SUZANNE_PROJELER.exists():
    for item in SUZANNE_PROJELER.iterdir():
        target = dest_proj / item.name
        if item.is_dir():
            if not target.exists():
                print(f"Copying directory: {item.name}...")
                shutil.copytree(item, target)
            else:
                # Copy any missing files
                for sub in item.iterdir():
                    sub_target = target / sub.name
                    if not sub_target.exists():
                        print(f"Copying file: {item.name}/{sub.name}")
                        if sub.is_dir():
                            shutil.copytree(sub, sub_target)
                        else:
                            shutil.copy2(sub, sub_target)
        else:
            if not target.exists():
                shutil.copy2(item, target)
    print("Projeler folder sync complete!")
else:
    print("Suzanne/projeler not found!")

print("\n=== CHECKING OTHER FILES IN NEXA_PRIME_v2_ENTERPRISE ===")
for root, dirs, files in os.walk(NEXA_DIR):
    rel_root = Path(root).relative_to(NEXA_DIR)
    if ".git" in str(rel_root):
        continue
    for f in files:
        if f.endswith((".py", ".json", ".db", ".txt", ".csv", ".pkl", ".env")):
            print(f"NEXA file: {rel_root / f}")
