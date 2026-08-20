#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render / gunicorn giriş noktası:
- app.py'deki __main__ blokları gunicorn'da çalışmaz, bu yüzden otonom
  thread'ler burada başlatılır.
- CI/CD pipeline (CB sync, data import, self-healing, AI summaries)
  artık GitHub Actions (.github/workflows/update_db.yml) tarafından
  her 6 saatte bir çalıştırılır. Sunucuda sadece hafif runtime daemon'ları kalır.
- Kullanım (Render): gunicorn render_start:app --bind 0.0.0.0:$PORT
"""
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("render.start")


def _boot_background_workers():
    # ─── SUNUCUDA KALAN DAEMLER (FILESYSTEM ERIŞİMİ GEREKTİRENLER) ───

    # Watchdog: projeler/ klasöründeki PDF değişikliklerini izler,
    # metin çıkarır, DB'ye document_chunks olarak yazar.
    # Hafif, 2 dakikada bir, disk I/O odaklı.
    try:
        import nexa_watchdog
        threading.Thread(
            target=nexa_watchdog.watchdog_loop,
            daemon=True,
            name="watchdog"
        ).start()
        logger.info("watchdog daemon started")
    except Exception as e:
        logger.warning("watchdog başlatılamadı: %s", e)

    # Drive Puller: Google Drive paylaşılan klasöründen yeni/degisen
    # dosyaları projeler/ altına indirir. Media dosyaları (PDF, MP4)
    # gitignore'dadır, bu yüzden sunucuda indirilmesi ZORUNLUDUR.
    try:
        import nexa_drive_puller
        threading.Thread(
            target=nexa_drive_puller.drive_loop,
            daemon=True,
            name="drive-puller"
        ).start()
        logger.info("drive-puller daemon started")
    except Exception as e:
        logger.warning("drive-puller başlatılamadı: %s", e)

    # ─── GITHUB ACTIONS'A TAŞINAN DAEMLER (SUNUCUDAN KALDIRILDI) ───
    #
    # ✗ auto-sync (CB.com.tr + Data Importer)
    #   → GitHub Actions: scripts/nexa_cb_sync.py + nexa_data_importer.py
    #
    # ✗ auto-self-healing
    #   → GitHub Actions: nexa_self_healing.run_full_self_healing_cycle()
    #
    # ✗ auto-summaries (AI özet üretimi)
    #   → GitHub Actions: nexa_rag.generate_all_project_summaries()
    #
    # ✗ youtube-uploader
    #   → GitHub Actions'a taşındı (opsiyonel, videosu olmayan kartlar için)
    #
    # Bu daemon'ların sunucudan kaldırılması:
    # - RAM/CPU kullanımını %60-70 azaltır
    # - Tek hata noktasını (self-healing JSON corruption) ortadan kaldırır
    # - Render Pro'da daha stabil, hızlı yanıt süreleri sağlar
    #

    logger.info("Background workers booted (watchdog + drive-puller only)")


_boot_background_workers()

from app import app  # noqa: E402  (gunicorn'un import edeceği Flask app)