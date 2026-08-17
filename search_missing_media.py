import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

src_folders = [
    Path(r"C:\Users\USER\Desktop\gayrimenkulmuhendisi-main"),
    Path(r"C:\Users\USER\Desktop\NEXA_PRIME_v2_ENTERPRISE"),
    Path(r"C:\Users\USER\Desktop\all"),
    Path(r"C:\Users\USER\Desktop\ALL100"),
    Path(r"C:\Users\USER\Desktop\ALL50"),
    Path(r"C:\Users\USER\Desktop\BACKUPS"),
]

target_base = Path(r"C:\Users\USER\Desktop\3\projeler")

print("=== SEARCHING FOR ALL PROJECT MEDIA (MP4 & PDF) ===")

all_found = {}
for sf in src_folders:
    if not sf.exists():
        continue
    for p in sf.rglob("*.*"):
        if p.suffix.lower() in [".mp4", ".pdf"]:
            name = p.name.upper()
            if name not in all_found or p.stat().st_size > all_found[name].stat().st_size:
                all_found[name] = p

print(f"Total unique media files found: {len(all_found)}")
for k, v in sorted(all_found.items())[:30]:
    print(f"  - {k:<45} ({v.stat().st_size:>10} bytes) in {v.parent.name}")
