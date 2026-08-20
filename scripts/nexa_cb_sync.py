#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXA OTONOM CB PORTFÖY SENKRONİZASYONU
=======================================
Susanne Tenekecioğlu (CB VIP — officeid=470, officeuserid=17983) ilanlarını
cb.com.tr'den otomatik çeker, NEXA PRIME DB'ye upsert eder (is_portfolio=1)
ve RAG bellek (documents + document_chunks) besler.

Elle hiçbir giriş gerekmez:
  - NEXA PRIME sunucusu açılışında ve her 15 dakikada bir otomatik çalışır
  - CLI ile de elle tetiklenebilir:  python scripts/nexa_cb_sync.py
"""
import html as html_mod
import json
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = Path(__file__).resolve().parent.parent / "nexa_database.db"
AGENT_ID = "17983"          # Susanne Tenekecioğlu
OFFICE_ID = "470"           # CB VIP Ankara Çankaya
LISTINGS_URL = f"https://www.cb.com.tr/ilanlar?officeid={OFFICE_ID}&officeuserid={AGENT_ID}"
BASE_URL = "https://www.cb.com.tr"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

AGENT_LAST_LOG = Path(__file__).parent / "nexa_cb_sync_last.json"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def _clean(txt: str) -> str:
    txt = html_mod.unescape(txt or "")
    txt = re.sub(r"<[^>]+>", "", txt)
    return re.sub(r"\s+", " ", txt).strip()


def fetch_agent_listings() -> list:
    """Liste sayfası: JSON-LD ItemList + HTML fallback."""
    html_text = _fetch(LISTINGS_URL)
    listings, seen_links = [], set()

    for script in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S):
        try:
            data = json.loads(script)
            items = data if isinstance(data, list) else data.get("@graph", [data])
            for it in items:
                if not (isinstance(it, dict) and it.get("@type") == "ItemList"):
                    continue
                for el in it.get("itemListElement", []):
                    p = el.get("item", {}) if isinstance(el, dict) else {}
                    if not isinstance(p, dict):
                        continue
                    link = (p.get("@id") or "").strip()
                    if not link:
                        continue
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    offers = p.get("offers") or {}
                    listings.append({
                        "title": _clean(p.get("name", "")),
                        "description": _clean(p.get("description", "")),
                        "link": link,
                        "price": _clean(offers.get("price", "")) if isinstance(offers, dict) else "",
                        "currency": _clean(offers.get("priceCurrency", "")) if isinstance(offers, dict) else "",
                    })
        except Exception:
            continue

    if not listings:
        for m in re.finditer(r'href="([^"]*(?:satilik|kiralik)[^"]*)"', html_text):
            link = m.group(1)
            if link.startswith("/"):
                link = BASE_URL + link
            if link in seen_links:
                continue
            seen_links.add(link)
            listings.append({"title": "", "description": "", "link": link, "price": "", "currency": ""})

    return listings


def fetch_listing_detail(url: str) -> dict:
    """Detay sayfası: özellik tablosu, fiyat, konum, fotoğraflar."""
    html_text = _fetch(url)
    detail = {}

    for block in re.findall(r'<table[^>]*class="[^"]*table-properties[^"]*"[^>]*>(.*?)</table>', html_text, re.S):
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", block, re.S):
            cols = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
            vals = [_clean(c) for c in cols]
            if len(vals) >= 2 and vals[0]:
                detail[vals[0]] = " | ".join(vals[1:])

    photos = []
    gallery = re.search(r'<div[^>]*id="cb-item-gallery"[^>]*>(.*?)</div>', html_text, re.S)
    if gallery:
        for src in re.findall(r'<img[^>]*src="([^"]+)"', gallery.group(1)):
            if src not in photos:
                photos.append(src)
        for src in re.findall(r'<img[^>]*data-src="([^"]+)"', gallery.group(1)):
            if src not in photos:
                photos.append(src)

    detail["_fotograflar"] = photos
    return detail


def parse_location(loc_raw: str) -> dict:
    """'Türkiye, Ankara, Çankaya, Yaşamkent' → il/ilçe/mahalle."""
    il, ilce, mahalle = "", "", ""
    parts = [p.strip() for p in loc_raw.split(",") if p.strip()]
    if len(parts) >= 2:
        il = parts[1]
    if len(parts) >= 3:
        ilce = parts[2]
    if len(parts) >= 4:
        mahalle = parts[3]
    return {"il": il, "ilce": ilce, "mahalle": mahalle}


def build_ilan(entry: dict, detail: dict) -> dict:
    title = entry.get("title") or ""
    ilan_no = ""
    m = re.search(r"/(\d{4,8})/?$", entry.get("link", ""))
    if m:
        ilan_no = m.group(1)
    if not title:
        title = f"CB Portföy İlanı {ilan_no}"

    price = _clean(detail.get("Fiyat", entry.get("price", "")))
    location = _clean(detail.get("Konum", ""))
    loc = parse_location(location)
    area_brut = _clean(detail.get("Metre Kare (Brüt)", ""))
    area_net = _clean(detail.get("Metre Kare (Net)", ""))
    area = ""
    if area_brut:
        area = f"{area_brut} m² Brüt"
        if area_net:
            area += f" / {area_net} m² Net"
    elif area_net:
        area = f"{area_net} m² Net"

    category = _clean(detail.get("Portföy Kategorisi", ""))
    listing_type = "Kiralık" if "kiralık" in (title + " " + location).lower() else "Satılık"
    if "Devren" in title:
        listing_type = "Devren Kiralık"

    features = []
    for key in ["Tapu Durumu", "Bina Yaşı", "Bulunduğu Kat", "Kat Sayısı", "Isıtma",
                "Eşyalı", "Kullanım Durumu", "Krediye Uygun", "Takasa Uygun"]:
        v = _clean(detail.get(key, ""))
        if v:
            features.append(f"{key}: {v}")

    description = entry.get("description") or ""
    if features:
        description = (description + "\n\nÖZELLİKLER: " + " | ".join(features)).strip()

    full_location = " / ".join(x for x in [loc["il"], loc["ilce"], loc["mahalle"]] if x)
    return {
        "cb_ilan_no": ilan_no,
        "cb_url": entry.get("link", ""),
        "name": title,
        "listing_type": listing_type,
        "property_category": category or "Konut / Daire",
        "price_display": price,
        "room_info": "",
        "net_gross_area": area,
        "location": full_location,
        "il": loc["il"],
        "ilce": loc["ilce"],
        "mahalle": loc["mahalle"],
        "ada_no": _clean(detail.get("Ada No", "")),
        "parsel_no": _clean(detail.get("Parsel No", "")),
        "description": description,
        "cover_image_url": detail.get("_fotograflar", [""])[0] or "",
        "tkgm_verified": 1 if (_clean(detail.get("Ada No", "")) and _clean(detail.get("Parsel No", ""))) else 0,
    }


def build_rag_doc(ilan: dict) -> tuple:
    doc_title = f"{ilan['listing_type']} Portföy İlan Detayı - {ilan['name']}"
    content = f"""
PORTFÖY İLAN RAPORU: {ilan['name']}
====================================================
İLAN TÜRÜ: {ilan['listing_type']}
PORTFÖY KATEGORİSİ: {ilan['property_category']}
LİSTE FİYATI: {ilan['price_display'] or 'Belirtilmedi'}
ODA / ALAN: {ilan['room_info'] or '-'} ({ilan['net_gross_area'] or '-'})
LOKASYON: {ilan['location'] or '-'} ({ilan['il'] or '-'} / {ilan['ilce'] or '-'} / {ilan['mahalle'] or '-'})
TAPU / PARSEL: Ada {ilan['ada_no'] or '-'} / Parsel {ilan['parsel_no'] or '-'} (TKGM Onay: {'Evet' if ilan['tkgm_verified'] else 'Hayır'})
KAYNAK: {ilan['cb_url']}
AÇIKLAMA & ÖZELLİKLER: {ilan['description'] or 'Açıklama girilmedi.'}
====================================================
"""
    return doc_title, content


def _ensure_columns(conn: sqlite3.Connection):
    for col, ddl in [
        ("cb_ilan_no", "VARCHAR(50)"),
        ("cb_url", "VARCHAR(500)"),
        ("cb_last_synced", "TIMESTAMP"),
    ]:
        try:
            conn.execute(f"ALTER TABLE projects ADD COLUMN {col} {ddl}")
        except Exception:
            pass
    conn.commit()


def upsert_ilan(conn: sqlite3.Connection, ilan: dict) -> int:
    cb_url = ilan.get("cb_url", "")
    cb_ilan_no = ilan.get("cb_ilan_no", "")
    if cb_ilan_no:
        cur = conn.execute(
            "SELECT id FROM projects WHERE cb_url = ? OR cb_ilan_no = ?",
            (cb_url, cb_ilan_no),
        )
    else:
        cur = conn.execute(
            "SELECT id FROM projects WHERE cb_url = ?",
            (cb_url,),
        )
    row = cur.fetchone()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    doc_title, doc_content = build_rag_doc(ilan)

    if row:
        proj_id = row[0]
        conn.execute("""
            UPDATE projects SET name=?, location=?, il=?, ilce=?, mahalle=?, description=?,
                cover_image_url=?, listing_type=?, property_category=?, price_display=?,
                room_info=?, net_gross_area=?, ada_no=?, parsel_no=?, tkgm_verified=?,
                cb_url=?, cb_last_synced=?
            WHERE id=?
        """, (ilan["name"], ilan["location"], ilan["il"], ilan["ilce"], ilan["mahalle"],
              ilan["description"], ilan["cover_image_url"], ilan["listing_type"],
              ilan["property_category"], ilan["price_display"], ilan["room_info"],
              ilan["net_gross_area"], ilan["ada_no"], ilan["parsel_no"], ilan["tkgm_verified"],
              ilan["cb_url"], now, proj_id))
    else:
        cur = conn.execute("""
            INSERT INTO projects (name, location, il, ilce, mahalle, description, cover_image_url,
                ada_no, parsel_no, tkgm_verified, is_portfolio, listing_type, property_category,
                price_display, room_info, net_gross_area, cb_ilan_no, cb_url, cb_last_synced)
            VALUES (?,?,?,?,?,?,?,?,?,?,1,?,?,?,?,?,?,?,?)
        """, (ilan["name"], ilan["location"], ilan["il"], ilan["ilce"], ilan["mahalle"],
              ilan["description"], ilan["cover_image_url"], ilan["ada_no"], ilan["parsel_no"],
              ilan["tkgm_verified"], ilan["listing_type"], ilan["property_category"],
              ilan["price_display"], ilan["room_info"], ilan["net_gross_area"],
              ilan["cb_ilan_no"], ilan["cb_url"], now))
        proj_id = cur.lastrowid

    cur = conn.execute(
        "SELECT id FROM documents WHERE project_id=? AND title=?", (proj_id, doc_title))
    drow = cur.fetchone()
    if drow:
        conn.execute("UPDATE documents SET content=? WHERE id=?", (doc_content, drow[0]))
        doc_id = drow[0]
    else:
        cur = conn.execute("""
            INSERT INTO documents (project_id, doc_type, title, content, category)
            VALUES (?, 'Bireysel Portföy İlanı', ?, ?, 'İlan Detay')
        """, (proj_id, doc_title, doc_content))
        doc_id = cur.lastrowid

    conn.execute("DELETE FROM document_chunks WHERE document_id=?", (doc_id,))
    conn.execute("INSERT INTO document_chunks (document_id, chunk_text) VALUES (?, ?)",
                 (doc_id, doc_content))
    conn.commit()
    return proj_id


def sync_once(verbose: bool = True) -> dict:
    report = {"ts": datetime.now().isoformat(timespec="seconds"),
              "agent": f"Susanne Tenekecioğlu ({AGENT_ID})", "fetched": 0,
              "upserted": 0, "errors": []}
    try:
        listings = fetch_agent_listings()
    except Exception as e:
        report["errors"].append(f"Liste çekilemedi: {e}")
        if verbose:
            print(f"[CB SYNC] {report['errors'][-1]}")
        return report

    report["fetched"] = len(listings)
    if verbose:
        print(f"[CB SYNC] {len(listings)} ilan bulundu (Susanne {AGENT_ID})")

    if not listings:
        return report

    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_columns(conn)
        for entry in listings:
            try:
                detail = fetch_listing_detail(entry["link"])
                ilan = build_ilan(entry, detail)
                upsert_ilan(conn, ilan)
                report["upserted"] += 1
                if verbose:
                    print(f"  + {ilan['name']} | {ilan['price_display'] or '-'} | {ilan['location'] or '-'}")
            except Exception as e:
                report["errors"].append(f"{entry.get('link', '?')}: {e}")
                if verbose:
                    print(f"  ! {entry.get('link', '?')} hata: {e}")
    finally:
        conn.close()

    AGENT_LAST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if verbose:
        print(f"[CB SYNC] Tamamlandı: {report['upserted']}/{report['fetched']} ilan DB'ye işlendi")
    return report


if __name__ == "__main__":
    t0 = time.time()
    sync_once()
    print(f"[CB SYNC] Süre: {time.time()-t0:.1f} sn")