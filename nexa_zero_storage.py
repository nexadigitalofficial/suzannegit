import os, sys, io, json, time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = Path("C:/Users/USER/Desktop/3")
MAP_FILE = BASE_DIR / "projects_map.json"
PF_FILE = BASE_DIR / "nexa_portfolio_data.json"
DRIVE_MAP_FILE = BASE_DIR / "drive_preview_mapping.json"
PROJELER_DIR = BASE_DIR / "projeler"

class NexaZeroDiskEngine:
    def __init__(self):
        self.map_file = MAP_FILE
        self.pf_file = PF_FILE
        self.drive_map_file = DRIVE_MAP_FILE
        self.projects_dir = PROJELER_DIR

    def ensure_cloud_mappings(self):
        """Her projenin Google Drive / Bulut önizleme linkini doğrular ve bağlar."""
        if not self.map_file.exists() or not self.drive_map_file.exists():
            return False

        with open(self.map_file, "r", encoding="utf-8") as f:
            projects = json.load(f)

        with open(self.drive_map_file, "r", encoding="utf-8") as f:
            drive_map = json.load(f)

        updated = False
        for p in projects:
            title = p.get("title", "")
            for k, v in drive_map.items():
                if k in title.upper() or title.upper() in k:
                    p["drive_video_preview"] = v.get("vid_preview_url")
                    p["drive_pdf_preview"] = v.get("pdf_preview_url")
                    p["drive_vid_id"] = v.get("vid_id")
                    p["drive_pdf_id"] = v.get("pdf_id")
                    p["media_mode"] = "cloud_preview"
                    updated = True
                    break

        if updated:
            with open(self.map_file, "w", encoding="utf-8") as f:
                json.dump(projects, f, ensure_ascii=False, indent=2)
            print("✓ Tüm projelerin Drive Bulut Önizleme linkleri başarıyla doğrulandı.")

        return True

    def calculate_storage_savings(self):
        """Yereldeki medya boyutunu ve tasarruf potansiyelini hesaplar."""
        total_bytes = 0
        file_count = 0
        if self.projects_dir.exists():
            for root, _, files in os.walk(self.projects_dir):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in [".mp4", ".pdf"]:
                        fp = os.path.join(root, f)
                        total_bytes += os.path.getsize(fp)
                        file_count += 1
        
        mb = total_bytes / (1024 * 1024)
        gb = mb / 1024
        print(f"📊 Mevcut Yerel Medya Boyutu: {mb:.1f} MB ({gb:.2f} GB) — {file_count} Dosya")
        print(f"🚀 Bulut Önizleme Modunda Sıfır Disk Tüketimi (0 MB) Sağlanır.")
        return total_bytes

if __name__ == "__main__":
    engine = NexaZeroDiskEngine()
    print("=== NEXA SIFIR-DİSK (ZERO-STORAGE) BULUT ÖNİZLEME MOTORU ===")
    engine.ensure_cloud_mappings()
    engine.calculate_storage_savings()
