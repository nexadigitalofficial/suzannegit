import os
import sys
import shutil
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

src_dir = Path(r"C:\Users\USER\Desktop\gayrimenkulmuhendisi-main\projeler")
target_dir = Path(r"C:\Users\USER\Desktop\3\projeler")

if src_dir.exists():
    for folder in src_dir.iterdir():
        if folder.is_dir():
            t_folder = target_dir / folder.name
            t_folder.mkdir(parents=True, exist_ok=True)
            for f in folder.iterdir():
                t_file = t_folder / f.name
                if not t_file.exists() or t_file.stat().st_size != f.stat().st_size:
                    print(f"Copying {f.name} ({f.stat().st_size} bytes) -> {folder.name}")
                    shutil.copy2(f, t_file)

print("Media copy check completed!")
