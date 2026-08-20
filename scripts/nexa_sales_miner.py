# -*- coding: utf-8 -*-
"""
nexa_sales_miner.py — Otonom Satış, Excel (XLSX) ve Finansal Bilgi Madencisi
Zero-Storage mimarisiyle hafif JSON ve SQLite tablolarını senkronize eder.
"""

import json
import sqlite3
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
GRAPH_FILE = ROOT_DIR / "nexa_sales_knowledge_graph.json"
MAP_FILE = ROOT_DIR / "projects_map.json"
PRICES_FILE = ROOT_DIR / "nexa_project_prices.json"
SUMMARIES_FILE = ROOT_DIR / "nexa_project_summaries.json"
DB_PATH = ROOT_DIR / "nexa_database.db"


def sync_sales_knowledge():
    if not GRAPH_FILE.exists():
        print("Knowledge graph file not found:", GRAPH_FILE)
        return False

    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    print(f"[1/3] {len(graph)} proje bilgi grafiğinden okundu.")

    # 1. projects_map.json güncelle
    if MAP_FILE.exists():
        projects = json.loads(MAP_FILE.read_text(encoding="utf-8"))
        for p in projects:
            title = p.get("title") or p.get("name") or ""
            matched_info = None
            for s_name, s_data in graph.items():
                if s_name.lower() == title.lower() or (len(s_name) > 4 and s_name.lower() in title.lower()):
                    matched_info = s_data
                    break
            if matched_info:
                p["price_display"] = matched_info["price_display"]
                p["price_min"] = matched_info["price_min"]
                p["price_max"] = matched_info["price_max"]
                p["price_numeric"] = matched_info["price_numeric"]
                p["down_payment"] = matched_info["down_payment"]
                p["installment_terms"] = matched_info.get("installment_terms", "")
                p["monthly_installment"] = matched_info.get("monthly_installment", 0)
                p["room_info"] = matched_info["room_info"]
                p["delivery_months"] = matched_info.get("delivery_months", 24)
                p["il"] = matched_info.get("il", p.get("il", "Ankara"))
                p["ilce"] = matched_info.get("ilce", p.get("ilce", "Çankaya"))
                p["location"] = matched_info.get("location", p.get("location", "Ankara"))
                p["location_full"] = matched_info.get("location_full", p.get("location_full", "Ankara"))
                p["ada_no"] = matched_info.get("ada_no", p.get("ada_no", ""))
                p["parsel_no"] = matched_info.get("parsel_no", p.get("parsel_no", ""))
                p["tkgm_verified"] = matched_info.get("tkgm_verified", True)
                p["category"] = matched_info.get("category", "Markalı Konut Projesi")
                p["sales_highlights"] = matched_info.get("sales_highlights", "")
        MAP_FILE.write_text(json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[2/3] projects_map.json güncellendi ({len(projects)} proje).")

    # 2. nexa_project_prices & summaries
    prices = {}
    summaries = {}
    for name, data in graph.items():
        prices[name] = {
            "price_display": data["price_display"],
            "price_min": data["price_min"],
            "price_max": data["price_max"],
            "price_numeric": data["price_numeric"],
            "down_payment": data["down_payment"],
            "installment_terms": data.get("installment_terms", ""),
            "monthly_installment": data.get("monthly_installment", 0),
            "rooms": [r.strip() for r in data["room_info"].split(",")],
            "description": data.get("sales_highlights", "")
        }
        loc = data.get("location_full", "")
        pd = data.get("price_display", "")
        dp = data.get("down_payment", "")
        it = data.get("installment_terms", "Esnek Vade")
        rm = data.get("room_info", "")
        ada = str(data.get("ada_no", "-"))
        parsel = str(data.get("parsel_no", "-"))
        hl = data.get("sales_highlights", "")
        summaries[name] = {
            "summary": f"- {name} ({loc}): {pd}, Peşinat: {dp}, Ödeme: {it}, Daire: {rm}, Ada: {ada}/{parsel} (TKGM Onaylı). {hl}"
        }
    PRICES_FILE.write_text(json.dumps(prices, ensure_ascii=False, indent=2), encoding="utf-8")
    SUMMARIES_FILE.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3. SQLite güncelle
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        for name, data in graph.items():
            cur.execute("""
                UPDATE projects SET
                    price_display = ?,
                    price_min = ?,
                    price_max = ?,
                    price_numeric = ?,
                    down_payment = ?,
                    installment_terms = ?,
                    monthly_installment = ?,
                    delivery_months = ?,
                    room_info = ?,
                    location = ?,
                    il = ?,
                    ilce = ?,
                    mahalle = ?,
                    ada_no = ?,
                    parsel_no = ?,
                    tkgm_verified = 1
                WHERE name = ? OR name LIKE ?
            """, (
                data["price_display"],
                data["price_min"],
                data["price_max"],
                data["price_numeric"],
                data["down_payment"],
                data.get("installment_terms", ""),
                data.get("monthly_installment", 0),
                data.get("delivery_months", 24),
                data["room_info"],
                data["location"],
                data.get("il", "Ankara"),
                data.get("ilce", "Çankaya"),
                data.get("mahalle", ""),
                data.get("ada_no", ""),
                data.get("parsel_no", ""),
                name,
                f"%{name}%"
            ))
        conn.commit()
        conn.close()
        print("[3/3] SQLite database senkronizasyonu tamamlandı.")
    return True


if __name__ == "__main__":
    sync_sales_knowledge()
    print("Satış bilgileri başarıyla senkronize edildi.")

