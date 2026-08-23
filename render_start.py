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
import time

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

    # Cognitive Nucleus: Otonom bilişsel akıl yürütme, anomali ve sağlık izleme döngüsü
    try:
        from nexa_autonomous_system import cognitive_nucleus
        def _cognitive_loop():
            while True:
                try:
                    cognitive_nucleus.run_single_cognitive_cycle()
                except Exception as ce:
                    logger.debug("Cognitive cycle error: %s", ce)
                time.sleep(60)

        threading.Thread(
            target=_cognitive_loop,
            daemon=True,
            name="cognitive-nucleus"
        ).start()
        logger.info("cognitive-nucleus daemon started")
    except Exception as e:
        logger.warning("cognitive-nucleus başlatılamadı: %s", e)

    logger.info("Background workers booted (watchdog + drive-puller + cognitive-nucleus)")


_boot_background_workers()

from app import app  # noqa: E402  (gunicorn'un import edeceği Flask app)