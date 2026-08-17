import os
import sys
import shutil
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SRC_NEXA = Path(r"C:\Users\USER\Desktop\NEXA_PRIME_v2_ENTERPRISE")
DST_3 = Path(r"C:\Users\USER\Desktop\3")

print("=== COPYING STATIC/DOCUMENTS FROM NEXA TO 3 ===")
src_docs = SRC_NEXA / "static" / "documents"
dst_docs = DST_3 / "static" / "documents"
if src_docs.exists():
    print(f"Copying {src_docs} to {dst_docs}...")
    shutil.copytree(src_docs, dst_docs, dirs_exist_ok=True)
    print("Static/documents copied successfully!")

print("\n=== COPYING APP FOLDER (SERVICES/MODELS/CORE/API) ===")
src_app = SRC_NEXA / "app"
dst_app = DST_3 / "app"
if src_app.exists():
    print(f"Copying {src_app} to {dst_app}...")
    shutil.copytree(src_app, dst_app, dirs_exist_ok=True)
    print("App services copied successfully!")

print("\n=== COPYING SCRIPTS FOLDER ===")
src_scripts = SRC_NEXA / "scripts"
dst_scripts = DST_3 / "scripts"
if src_scripts.exists():
    print(f"Copying {src_scripts} to {dst_scripts}...")
    shutil.copytree(src_scripts, dst_scripts, dirs_exist_ok=True)
    print("Scripts copied successfully!")

print("\n=== COPYING .ENV AND OTHER ESSENTIAL CONFIGS ===")
for fname in [".env", "requirements.txt"]:
    src_file = SRC_NEXA / fname
    dst_file = DST_3 / fname
    if src_file.exists() and not dst_file.exists():
        shutil.copy2(src_file, dst_file)
        print(f"Copied {fname}")

print("\n=== VERIFYING DESTINATION CONTENTS IN 3 ===")
for root, dirs, files in os.walk(DST_3):
    rel = Path(root).relative_to(DST_3)
    if "projeler" in str(rel) or "documents" in str(rel) or "__pycache__" in str(rel):
        continue
    print(f"  {rel}: {len(files)} files, {len(dirs)} subdirs")

print("Copy completed successfully!")
