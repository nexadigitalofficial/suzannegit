#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render / gunicorn giriş noktası:
- app.py'deki __main__ blokları gunicorn'da çalışmaz, bu yüzden otonom
  thread'ler (importer, self-healing, watchdog, youtube) burada başlatılır.
- Kullanım (Render): gunicorn render_start:app --bind 0.0.0.0:$PORT
"""
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("render.start")


def _boot_background_workers():
    try:
        import nexa_rag
        threading.Thread(target=nexa_rag.generate_all_project_summaries,
                         daemon=True, name="auto-summaries").start()
    except Exception as e:
        logger.warning("summaries baslatilamadi: %s", e)

    try:
        import app as app_mod
        threading.Thread(target=app_mod._autonomous_sync_loop,
                         daemon=True, name="auto-sync").start()
    except Exception as e:
        logger.warning("sync loop baslatilamadi: %s", e)

    try:
        import app as app_mod
        threading.Thread(target=app_mod._autonomous_self_healing_daemon,
                         daemon=True, name="auto-self-healing").start()
    except Exception as e:
        logger.warning("self-healing baslatilamadi: %s", e)

    try:
        import nexa_watchdog
        threading.Thread(target=nexa_watchdog.watchdog_loop,
                         daemon=True, name="watchdog").start()
    except Exception as e:
        logger.warning("watchdog baslatilamadi: %s", e)

    try:
        import nexa_drive_puller
        threading.Thread(target=nexa_drive_puller.drive_loop,
                         daemon=True, name="drive-puller").start()
    except Exception as e:
        logger.warning("drive puller baslatilamadi: %s", e)

    try:
        import app as app_mod
        threading.Thread(target=app_mod._autonomous_youtube_loop,
                         daemon=True, name="youtube-uploader").start()
    except Exception as e:
        logger.warning("youtube uploader baslatilamadi: %s", e)


_boot_background_workers()

from app import app  # noqa: E402  (gunicorn'un import edeceği Flask app)