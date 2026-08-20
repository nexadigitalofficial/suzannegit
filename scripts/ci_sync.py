#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions CI Sync Orchestrator
Sıra: CB Sync → Data Import → Self-Healing → AI Summaries
Hata yakalama + loglama + exit code yönetimi ile.
"""

import sys
import os
import traceback
import logging
import time
from datetime import datetime

# Proje kök dizinini path'e ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ci_sync")


def run_step(name: str, func, *args, **kwargs) -> tuple[bool, str]:
    """Tek bir adımı çalıştır, hata yakala, süre ölç."""
    log.info("▶ %s başlıyor...", name)
    t0 = time.time()
    try:
        result = func(*args, **kwargs)
        dt = time.time() - t0
        log.info("✓ %s tamam (%.1fs)", name, dt)
        return True, f"{name} OK ({dt:.1f}s)"
    except Exception as e:
        dt = time.time() - t0
        log.error("✗ %s HATA (%.1fs): %s", name, dt, e)
        log.debug(traceback.format_exc())
        return False, f"{name} FAILED: {e}"


def main():
    log.info("=" * 60)
    log.info("CI SYNC BAŞLADI — %s", datetime.utcnow().isoformat())
    log.info("=" * 60)

    results = []
    any_failed = False

    # 1. CB.com.tr Senkronizasyonu
    try:
        from scripts.nexa_cb_sync import sync_once
        ok, msg = run_step("CB Sync", sync_once, verbose=True)
    except ImportError:
        ok, msg = False, "CB Sync modülü bulunamadı (scripts/nexa_cb_sync.py)"
    results.append((ok, msg))
    if not ok:
        any_failed = True

    # 2. Data Importer (DB → JSON fiyat/oda çıkarma)
    try:
        import nexa_data_importer
        ok, msg = run_step("Data Importer", nexa_data_importer.main)
    except ImportError:
        ok, msg = False, "Data Importer modülü bulunamadı (nexa_data_importer.py)"
    results.append((ok, msg))
    if not ok:
        any_failed = True

    # 3. Self-Healing (DB şema + kanonik veri + RAG + NLP)
    try:
        import nexa_self_healing
        ok, msg = run_step("Self-Healing", nexa_self_healing.run_full_self_healing_cycle)
    except ImportError:
        ok, msg = False, "Self-Healing modülü bulunamadı (nexa_self_healing.py)"
    results.append((ok, msg))
    if not ok:
        any_failed = True

    # 4. AI Summaries (Gemini ile proje özetleri)
    try:
        import nexa_rag
        ok, msg = run_step("AI Summaries", nexa_rag.generate_all_project_summaries)
    except ImportError:
        ok, msg = False, "RAG modülü bulunamadı (nexa_rag.py)"
    results.append((ok, msg))
    if not ok:
        any_failed = True

    # 5. Sales & Financial Miner (Excel XLSX & Finansal Bilgi Senkronizasyonu)
    try:
        from scripts.nexa_sales_miner import sync_sales_knowledge
        ok, msg = run_step("Sales Miner", sync_sales_knowledge)
    except ImportError:
        ok, msg = False, "Sales Miner modülü bulunamadı (scripts/nexa_sales_miner.py)"
    results.append((ok, msg))
    if not ok:
        any_failed = True

    # Özet
    log.info("=" * 60)
    log.info("CI SYNC ÖZET")
    log.info("=" * 60)
    for ok, msg in results:
        status = "✓" if ok else "✗"
        log.info("  %s %s", status, msg)

    log.info("=" * 60)

    if any_failed:
        log.error("CI SYNC KISMİ BAŞARISIZ — exit code 1")
        sys.exit(1)

    log.info("CI SYNC TAM BAŞARILI — exit code 0")
    sys.exit(0)


if __name__ == "__main__":
    main()