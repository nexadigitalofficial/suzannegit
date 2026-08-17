#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXA OTOMATİK YOUTUBE YÜKLEYİCİ
Drive'da videosu olmayan vitrin kartlarının local tanıtım videolarını
YouTube'a (unlisted) yükler ve kartlara youtube_video_preview yazar.
Böylece hosting'de videolar Drive/YouTube üzerinden izlenir.

İlk çalıştırmada bir kez tarayıcıda Google onayı ister; sonrası tam otomatik.
Kullanım: python youtube_uploader.py
"""
import json
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent
MAP_FILE = BASE_DIR / "projects_map.json"
STATE_FILE = BASE_DIR / "youtube_state.json"
CLIENT_SECRETS = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "youtube_token.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def norm_name(s):
    s = (s or "").replace("İ", "i").replace("I", "i").replace("ı", "i")
    s = s.replace("Ş", "s").replace("ş", "s").replace("Ğ", "g").replace("ğ", "g")
    s = s.replace("Ç", "c").replace("ç", "c").replace("Ö", "o").replace("ö", "o")
    s = s.replace("Ü", "u").replace("ü", "u")
    return s.lower()


def find_video(folder):
    d = BASE_DIR / "projeler" / (folder or "")
    if not d.exists():
        return None
    cands = []
    pri = ["tanitim", "lansman", "animasyon", "render", "muteahhit", "kisa", "promo", "slideshow"]
    for f in d.glob("*.mp4"):
        if f.stat().st_size < 50000:
            continue
        score = next((i for i, k in enumerate(pri) if k in norm_name(f.name)), len(pri))
        cands.append((score, f.name, f))
    if not cands:
        return None
    cands.sort(key=lambda x: x[0])
    return cands[0][2]


def get_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent")
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, path, title, desc):
    from googleapiclient.http import MediaFileUpload
    body = {
        "snippet": {"title": title[:95], "description": desc[:4900],
                    "tags": ["NEXA", "gayrimenkul", "Ankara", "proje"], "categoryId": "22"},
        "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(path), chunksize=8 * 1024 * 1024, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"    yukleniyor: %d%%" % int(status.progress() * 100))
    return resp["id"]


def main():
    if not CLIENT_SECRETS.exists():
        print("HATA: client_secrets.json bulunamadi — Google Cloud Console'dan")
        print("      OAuth 2.0 Client (Desktop app) olusturup bu klasore koyun.")
        sys.exit(1)

    cards = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    todo = []
    for c in cards:
        if c.get("drive_video_preview") or c.get("youtube_video_preview"):
            continue
        vid = find_video(c.get("folder_name"))
        if vid:
            todo.append((c, vid))

    if not todo:
        print("Yuklenecek yeni video yok (%d kart tam)" % len(cards))
        return

    print("Yuklenecek %d video bulundu. OAuth onayi gerekebilir..." % len(todo))
    youtube = get_service()
    for c, vid in todo:
        key = c["id"]
        if state.get(key):
            print("  atla (onceki): %s" % c["title"])
            continue
        print("  yukleniyor: %s -> %s" % (c["title"], vid.name))
        try:
            yid = upload_video(youtube, vid,
                               "NEXA | %s — Tanitim Filmi" % c["title"],
                               "NEXA Proptech | %s\nFiyat: %s\nLokasyon: %s" % (
                                   c.get("title"), c.get("price_display") or "Danisiniz",
                                   c.get("location") or c.get("ilce") or "Ankara"))
        except Exception as e:
            print("    HATA: %s" % e)
            continue
        c["youtube_video_preview"] = "https://www.youtube.com/embed/%s" % yid
        state[key] = {"youtube_id": yid, "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
        print("    OK: youtube.com/watch?v=%s" % yid)

    MAP_FILE.write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    print("projects_map.json guncellendi (%d video yuklendi)" % len(state))


if __name__ == "__main__":
    main()