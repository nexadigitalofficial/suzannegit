"""
NEXA RAG — Bilişsel Gayrimenkul Zekası (NEXA PRIME v2 ENTEPRISE seviyesi)
- NEXA PRIME veritabanındaki proje metadata + doküman chunk'larına RAG yapar
- Gemini çoklu-anahtar çoklu-model fallback ile cevap üretir (NEXA PRIME mimarisi)
- Bulut yoksa yerel Ollama, o da yoksa None döner (çağıran taraf heuristic'e düşer)
"""
import os
import re
import json
import time
import sqlite3
import logging
import threading
from pathlib import Path

logger = logging.getLogger("nexa.rag")


def _resolve_nexa_root():
    """config.json -> nexa_db_dir anahtarını okur (D6 taşınabilirlik); yoksa yerel klasör."""
    candidates = [Path(__file__).resolve().parent / "config.json"]
    for cfg in candidates:
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            d = data.get("nexa_db_dir")
            if d:
                return Path(d)
        except Exception:
            continue
    return Path(__file__).resolve().parent


NEXA_ROOT = _resolve_nexa_root()
DB_PATH = NEXA_ROOT / "nexa_database.db"
DOCS_DIR = NEXA_ROOT / "static" / "documents"
SUMMARIES_FILE = Path(__file__).resolve().parent / "nexa_project_summaries.json"
PORTFOLIO_FILE = Path(__file__).resolve().parent / "nexa_portfolio_data.json"
MAP_FILE = NEXA_ROOT / "projects_map.json"

# ─── KOTA / PERFORMANS YÖNETİMİ (P8/P9) ───
_key_cooldowns = {}          # key -> süre sonu (429/401 tespitinde 60 sn yasak)
_dead_keys = set()           # kalıcı geçersiz anahtarlar (403/leaked/invalid)
_last_good_model = {}        # key -> son başarılı model (öncelikle dene)
_reply_cache = {}            # normalize sorgu -> (yanıt, zaman)
_cache_lock = threading.Lock()
_save_lock = threading.Lock()
_ctx_build_lock = threading.Lock()
_global_ctx_cache = {}       # E9: global context (60 sn TTL)
REPLY_TTL = 300              # 5 dk
KEY_COOLDOWN = 60
GLOBAL_CTX_TTL = 60          # saniye
DEAD_MODEL_TTL = 900         # 15 dk sonra 404 modeli tekrar dene
_dead_models = {}            # model_name -> expiration_timestamp

_FALLBACK_CANONICAL_MATRIX = """- VIP ÜNİVERSİTE: Başlangıç Fiyatı: 1.350.000 TL, Peşinat: 825.000 TL (%50), 257 adet 1+1 daire, Zemin+8 kat. Lokasyon: Ankara / Çubuk / Esenboğa (Yıldırım Beyazıt Üniversitesi Kampüsü tam karşısı). Yerden ısıtma, yüksek öğrenci/akademisyen kiralama talebi. Ada: 190438, Parsel: 15 (TKGM Onaylı).
- WM - PRIME: 1.799.000 TL (1+1 daireler, Odunpazarı / Eskişehir).
- S POINT - VIP SARAY: 1.990.000 TL - 4.000.000 TL (1+1, 2+1, Saray / Pursaklar).
- VIP AKADEMİ & VIP AKADEMİ 2: 1.990.000 TL - 2.740.000 TL (1+1, Esenboğa / Çubuk).
- GRANDE YAŞAMKENT: 3.000.000 TL - 4.000.000 TL (1+1, 2+1, Yapracık / Etimesgut).
- ANKAPORT - SARAY: 3.040.000 TL - 8.350.000 TL (1+1, 2+1, 3+1, Saray / Pursaklar).
- NARÇİN RONYA CITY - 1: 3.400.000 TL - 4.330.000 TL (1+1, 2+1, Yukarıyurtçu / Etimesgut).
- GÖKDEMİR İMZA: 3.900.000 TL - 8.000.000 TL (1+1, 2+1, 3+1, Kızılcaşar / Gölbaşı).
- VIP MARIN: 4.100.000 TL - 5.935.000 TL (1+1 ve 2+1 Lüks Sahil/Deniz Rezidansı, Avsallar / Alanya / Antalya).
- ANGİM BEYTEPE: 4.500.000 TL - 22.890.000 TL (1+1'den 6+1'e, Beytepe / Çankaya).
- EVART YALIKAVAK: 14.500.000 TL (Lüks Deniz Manzaralı Villa & Rezidans, Yalıkavak / Bodrum / Muğla)."""

_matrix_cache = {"text": None, "time": 0}

def _build_canonical_matrix():
    global _matrix_cache
    import time
    with _cache_lock:
        if _matrix_cache["text"] and (time.time() - _matrix_cache["time"] < 300):
            return _matrix_cache["text"]
        
        try:
            map_path = Path(__file__).resolve().parent / "projects_map.json"
            if not map_path.exists():
                return _FALLBACK_CANONICAL_MATRIX
                
            with open(map_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            lines = []
            for p in data:
                title = p.get("title", p.get("name", ""))
                price_display = p.get("price_display", "")
                
                line = f"- {title}: {price_display}"
                
                down_payment = p.get("down_payment")
                if down_payment:
                    line += f", Peşinat: {down_payment}"
                
                installment_terms = p.get("installment_terms")
                if installment_terms:
                    line += f", Ödeme Planı: {installment_terms}"
                
                delivery_months = p.get("delivery_months")
                if delivery_months:
                    line += f", Teslim: {delivery_months} Ay"
                
                parts = []
                
                rooms = p.get("rooms") or p.get("room_info")
                if isinstance(rooms, list):
                    rooms = ", ".join(rooms)
                
                unit_count = p.get("unit_count")
                if unit_count and rooms:
                    parts.append(f"{unit_count} adet {rooms} daire")
                elif rooms:
                    parts.append(f"{rooms}")
                
                mahalle = p.get("mahalle", "")
                ilce = p.get("ilce", "")
                il = p.get("il", "")
                loc_str = " / ".join(filter(None, [mahalle, ilce, il]))
                if not loc_str:
                    loc_str = p.get("location", "")
                if loc_str:
                    parts.append(loc_str)
                
                if parts:
                    line += f" ({', '.join(parts)})"
                
                ada = p.get("ada_no")
                parsel = p.get("parsel_no")
                tkgm = p.get("tkgm_verified")
                
                if ada or parsel:
                    tkgm_str = " (TKGM Onaylı)" if tkgm else ""
                    ada_str = f"Ada: {ada}" if ada else ""
                    parsel_str = f"Parsel: {parsel}" if parsel else ""
                    tapu = ", ".join(filter(None, [ada_str, parsel_str])) + tkgm_str
                    line += f". {tapu}."
                else:
                    line += "."
                
                lines.append(line)
                
            if not lines:
                return _FALLBACK_CANONICAL_MATRIX
                
            result = "\n".join(lines)
            _matrix_cache["text"] = result
            _matrix_cache["time"] = time.time()
            return result
        except Exception:
            return _FALLBACK_CANONICAL_MATRIX

FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

CONTACT_LINE = "Detaylı sunum, güncel fiyat listesi ve parsel raporları için **0535 489 56 56** WhatsApp hattından ulaşabilirsiniz."


def _read_api_keys():
    keys = []
    for var_name in ["GEMINI_API_KEYS", "GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        env_val = os.getenv(var_name, "")
        if env_val:
            keys += [k.strip() for k in env_val.split(",") if k.strip()]
    env_file = NEXA_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            for prefix in ["GEMINI_API_KEYS=", "GEMINI_API_KEY=", "GOOGLE_API_KEY="]:
                if line.startswith(prefix):
                    keys += [k.strip() for k in line.split("=", 1)[1].split(",") if k.strip()]
    cfg_file = NEXA_ROOT / "config.json"
    if cfg_file.exists():
        try:
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
            for key_field in ["gemini_api_keys", "gemini_api_key", "api_key"]:
                val = cfg.get(key_field)
                if isinstance(val, list):
                    keys += [str(k).strip() for k in val if str(k).strip()]
                elif isinstance(val, str) and val.strip():
                    keys += [k.strip() for k in val.split(",") if k.strip()]
        except Exception:
            pass
    if not keys:
        try:
            from app.core.config import settings
            keys += settings.api_keys_list
        except Exception:
            pass
    seen, out = set(), []
    for k in keys:
        if k and k not in seen and "YENI_API_KEY" not in k and len(k) >= 10:
            seen.add(k)
            out.append(k)
    return out


_key_rot_lock = threading.Lock()
_key_rotation_idx = 0

def _get_rotated_api_keys():
    global _key_rotation_idx
    keys = _read_api_keys()
    if not keys:
        return []
    with _key_rot_lock:
        idx = _key_rotation_idx % len(keys)
        _key_rotation_idx += 1
        return keys[idx:] + keys[:idx]


def _merge_summary(name, project_id, summary):
    data = _load_summaries()
    data[name] = {"summary": summary, "project_id": project_id, "ts": time.time()}
    return data


def _load_db():
    db_uri = f"file:{Path(DB_PATH).resolve().as_posix()}?mode=ro"
    return sqlite3.connect(db_uri, uri=True)


# ─── BELGE BESLEME KALİTESİ (RAG feed) ───
# Çözülememiş PDF metni: kontrol karakterleri + Latin-1/IPA/Greek bloğunda 4+ ardışık karakter
# (glyph'ler: ʤʡʦʬ...; \ufffd = değiştirme karakteri, bozuk font çıktısı)
_GARBAGE_RE = re.compile(r"[\u0001-\u0008\u000b\u000c\u000e-\u001f\u007f-\u02ff\ufffd]{4,}")
_MIN_PIECE = 12


def _glyph_ratio(s):
    return sum(1 for c in s if "\u0080" <= c <= "\u02ff" or c == "\ufffd") / max(len(s), 1)


def _clean_chunk(text):
    """Çöp glyph bloklarını atıp anlamlı parçaları korur; tamamı çöpse None döner."""
    if not text:
        return None
    if not _GARBAGE_RE.search(text):
        return text
    pieces = []
    for p in _GARBAGE_RE.split(text):
        p = p.strip()
        if len(p) >= _MIN_PIECE and _glyph_ratio(p) < 0.4:
            pieces.append(p)
    return " ".join(pieces) or None


# SUNUM/ÖDEME/FİYAT içeren belgeler önce, IBAN/BANKA/SÖZLEŞME/HİSSE en son
_DOC_PRIORITY_SQL = """
    CASE
        WHEN UPPER(d.title) LIKE '%SUNUM%' OR UPPER(d.title) LIKE '%ÖDEME%'
          OR UPPER(d.title) LIKE '%FIYAT%' OR UPPER(d.title) LIKE '%FİYAT%' THEN 0
        WHEN UPPER(d.title) LIKE '%IBAN%' OR UPPER(d.title) LIKE '%BANKA%'
          OR UPPER(d.title) LIKE '%SÖZLEŞME%' OR UPPER(d.title) LIKE '%SOZLESME%'
          OR UPPER(d.title) LIKE '%HİSSE%' OR UPPER(d.title) LIKE '%HISSE%' THEN 2
        ELSE 1
    END"""


def build_project_context(db_id, query=None):
    db = _load_db()
    db.row_factory = sqlite3.Row
    try:
        p = dict(db.execute("SELECT * FROM projects WHERE id = ?", (db_id,)).fetchone())
        ptype = (f"BİREYSEL PORTFÖY İLANI ({p['listing_type'] or 'İlan'})"
                 if p.get("is_portfolio") else "MARKALI PROJE")
        meta = "\n".join([
            "=== PORTFÖY / PROJE METADATA ===",
            f"[AD]: {p['name']}",
            f"[EKOSİSTEM]: {ptype}",
            f"[GAYRİMENKUL TİPİ]: {p.get('property_category') or 'Belirtilmedi'}",
            f"[FİYAT / BEDEL]: {p.get('price_display') or 'Fiyat Belirtilmedi'}",
            f"[ODA / YAPI]: {p.get('room_info') or 'Belirtilmedi'}",
            f"[NET / BRÜT ALAN]: {p.get('net_gross_area') or 'Belirtilmedi'}",
            f"[LOKASYON]: {p.get('location') or ''} ({p.get('ilce') or ''} / {p.get('il') or ''})",
            f"[ADA/PARSEL]: {p.get('ada_no') or '-'}/{p.get('parsel_no') or '-'} (TKGM: {'Evet' if p.get('tkgm_verified') else 'Hayır'})",
            f"[AÇIKLAMA]: {p.get('description') or 'Açıklama girilmedi.'}",
        ])
        chunks = []
        raw_chunks = []
        for r in db.execute(f"""
            SELECT d.title, d.category, dc.chunk_text
            FROM document_chunks dc JOIN documents d ON dc.document_id = d.id
            WHERE d.project_id = ? AND LENGTH(TRIM(dc.chunk_text)) > 0
            ORDER BY {_DOC_PRIORITY_SQL}, d.id, dc.id
            LIMIT 24
        """, (db_id,)):
            txt = _clean_chunk(r["chunk_text"])
            if txt is None:
                continue
            raw_chunks.append((f"[{r['category'] or 'Belge'} - {r['title']}]: {txt[:400]}", txt))
        chosen = _rank_chunks(query, raw_chunks) if query else raw_chunks
        if query:
            # P17: gerçek vektör araması önce denenir; yeterli sonuç varsa öne konur
            try:
                from nexa_vector_rag import vector_search
                vres = vector_search(query, project_id=db_id, top_k=8)
                if vres and len(vres) >= 2:
                    v_chosen = []
                    for vr in vres:
                        t = (vr.get("chunk_text") or "").strip()
                        if not t:
                            continue
                        title = vr.get("document_title") or "Belge"
                        v_chosen.append((f"[{title}]: {t[:400]}", t))
                    if v_chosen:
                        chosen = v_chosen
            except Exception as e:
                logger.warning("Vektör arama devre disi: %s", e)
        chunks = [item[0] if isinstance(item, tuple) else str(item) for item in (chosen or [])[:12]]
        if not chunks:
            chunks.append("[BELGE]: Bu proje için sistemde henüz anlamlı doküman içeriği bulunmuyor (belge yüklenmemiş veya çözümlenememiş olabilir).")
        return meta + "\n" + "\n\n".join(chunks)
    finally:
        db.close()


def build_global_context():
    now = time.time()
    with _cache_lock:
        cached = _global_ctx_cache.get("ctx")
        if cached and now - cached[1] < GLOBAL_CTX_TTL:
            return cached[0]
    with _ctx_build_lock:
        with _cache_lock:
            cached = _global_ctx_cache.get("ctx")
            if cached and now - cached[1] < GLOBAL_CTX_TTL:
                return cached[0]
        db = _load_db()
        db.row_factory = sqlite3.Row
        try:
            projects = db.execute("""
                SELECT id, name, location, il, ilce, mahalle, description, ada_no, parsel_no,
                       tkgm_verified, is_portfolio, listing_type, property_category,
                       price_display, room_info, net_gross_area
                FROM projects WHERE COALESCE(is_portfolio,0) = 0 ORDER BY id ASC
            """).fetchall()
            if not projects:
                return "Sistemde henüz kayıtlı proje bulunmamaktadır."
            parts = []
            for proj in projects:
                ptype = (f"BİREYSEL PORTFÖY ({proj['listing_type'] or 'İlan'})"
                         if proj['is_portfolio'] else "MARKALI PROJE")
                specs = (f"Kategori: {proj['property_category'] or '-'}, "
                         f"Oda: {proj['room_info'] or '-'}, Alan: {proj['net_gross_area'] or '-'}")
                loc = proj['location'] or f"{proj['ilce'] or ''} / {proj['il'] or ''}"
                chunks = []
                for r in db.execute(f"""
                    SELECT d.title, d.doc_type, dc.chunk_text
                    FROM document_chunks dc JOIN documents d ON dc.document_id = d.id
                    WHERE d.project_id = ? AND LENGTH(TRIM(dc.chunk_text)) > 0
                    ORDER BY {_DOC_PRIORITY_SQL}, d.id, dc.id
                    LIMIT 16
                """, (proj['id'],)):
                    txt = _clean_chunk(r["chunk_text"])
                    if txt is None:
                        continue
                    chunks.append(f"  • [{r['doc_type'].upper()} - {r['title']}]: {txt[:260]}")
                    if len(chunks) >= 8:
                        break
                if not chunks:
                    chunks = ["  • (Henüz taranmış özel belge bulunmuyor)"]
                parts.append("\n".join([
                    "---",
                    f"İLAN/PROJE ID: {proj['id']} [{ptype}]",
                    f"AD: {proj['name']}",
                    f"FİYAT: {proj['price_display'] or 'Fiyat Belirtilmedi'} | {specs}",
                    f"LOKASYON: {loc} (İl: {proj['il'] or '-'}, İlçe: {proj['ilce'] or '-'}, Mahalle: {proj['mahalle'] or '-'})",
                    f"ADA/PARSEL: {proj['ada_no'] or '-'}/{proj['parsel_no'] or '-'} (TKGM Onay: {'Evet' if proj['tkgm_verified'] else 'Hayır'})",
                    f"AÇIKLAMA: {proj['description'] or 'Açıklama yok.'}",
                    "BELGE/VERİ ÖZETLERİ:",
                    "\n".join(chunks),
                ]))
            result = "\n\n".join(parts)
            with _cache_lock:
                _global_ctx_cache["ctx"] = (result, now)
            return result
        finally:
            db.close()


# ─── SORGU ODAKLI CHUNK SEÇİMİ (Y4 pragmatik iyileştirme) ───
def _query_tokens(query):
    """Sorgudan anlamlı Türkçe kelimeleri çıkarır (stopword'süz, sayısal filtreli)."""
    if not query:
        return []
    stop = {"bir", "bana", "bize", "en", "iyi", "uygun", "var", "mı", "mu", "mi",
            "olan", "olanlar", "proje", "projeler", "projesini", "anlat", "söyle",
            "hangi", "hangi", "istiyorum", "istiyoruz", "arayıorum", "arıyorum",
            "lütfen", "acaba", "ile", "ve", "veya", "ne", "nasıl", "nerede",
            "lazım", "gerek", "bütçe", "bütçem", "bütçemiz"}
    tokens = re.findall(r"[a-zçğıöşü]{3,}", (query or "").lower())
    return [t for t in tokens if t not in stop]


def _rank_chunks(query, candidates):
    """Chunk'ları sorgu token'larının geçiş sıklığına göre sıralar (üst 12 seçilir)."""
    tokens = _query_tokens(query)
    if not tokens or len(candidates) <= 12:
        return candidates
    scored = []
    for pair in candidates:
        if isinstance(pair, tuple):
            text = pair[1]
        else:
            text = pair
        tl = (text or "").lower()
        score = sum(tl.count(t) for t in tokens)
        scored.append((score, pair))
    scored.sort(key=lambda x: -x[0])
    out = [pair for s, pair in scored if s > 0]
    return (out or candidates)[:12]


def fetch_proximity_geo_intelligence(il, ilce, mahalle, proj_name):
    loc = f"{mahalle or ''} {ilce or ''} {il or ''}".strip()
    if not loc:
        return ""
    prompt = f"""
Sen NEXA'nn Bölgesel Konum & Çevre Aksı Araştırma Ajanısın (Geo-Intelligence Agent).
Şu lokasyon için Türkiye şehir planlama bilgini kullanarak ulaşım, üniversite, hastane,
metro/tramvay, otoyol ve gelişen aks bilgilerini 3 maddede özetle:

Proje: {proj_name}
Lokasyon: {loc}

GÖREVİN:
- En yakın Üniversiteler ve Eğitim Aksı
- En yakın Hastane ve Sağlık Merkezleri
- En yakın Tramvay/Metro/Bus ve Otoyol Ulaşım Aksları
- Bölgenin yatırım ve prim gelişim potansiyeli

Kısa, şık ve maddeler halinde yaz. Dokümanda yer almasa bile gerçek coğrafi lokasyondan hareketle anlat.
"""
    try:
        return _gemini_generate(prompt)
    except Exception as e:
        logger.warning("Geo intelligence failed: %s", e)
        return ""


# ─── BİLİŞSEL FONKSİYON VE ARAÇLAR (GEMINI FUNCTION CALLING / TOOLS) ───

# ─── BİLİŞSEL FONKSİYON VE ARAÇLAR (GEMINI FUNCTION CALLING / TOOLS) ───

def _sanitize_numeric(val, default=0.0):
    if isinstance(val, (int, float)):
        return float(val)
    if not val:
        return default
    cleaned = re.sub(r"[^\d.,]", "", str(val))
    if "." in cleaned and "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    try:
        return float(cleaned)
    except ValueError:
        return default


def schedule_vip_appointment(customer_name: str, phone: str, project_name: str = "", preferred_datetime: str = "", notes: str = "") -> str:
    """Müşterinin VIP proje danışmanı Suzanne Tenekecioğlu ile randevu talebini doğrudan SQLite veritabanına ve CRM sistemine kaydeder.
    
    Args:
        customer_name: Müşterinin ad soyadı
        phone: Müşterinin telefon numarası
        project_name: İlgilenilen projenin adı (örn. ANGİM BEYTEPE, VIP ÜNİVERSİTE vb.)
        preferred_datetime: Tercih edilen tarih ve saat (örn. Yarın 14:00, Pazartesi öğleden sonra vb.)
        notes: Müşterinin özel notu veya görüşme talebi
    """
    try:
        c_name = str(customer_name or "").strip()
        c_phone = re.sub(r"[^\d+]", "", str(phone or "").strip())
        if not c_name or not c_phone:
            return "Randevu kaydı için isim ve geçerli bir telefon numarası gereklidir."
        
        proj_name_clean = str(project_name or "").strip()
        pref_dt = str(preferred_datetime or "En kısa sürede").strip()
        user_notes = str(notes or "").strip()

        with sqlite3.connect(str(DB_PATH), timeout=30.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
            cur = conn.cursor()
            proj_clause = "(SELECT id FROM projects WHERE name LIKE ? LIMIT 1)" if proj_name_clean else "NULL"
            note_text = f"[AI Chatbot Randevusu] Proje: {proj_name_clean or 'Genel'} | Zaman: {pref_dt} | Danışman: Suzanne Tenekecioğlu | Not: {user_notes}"
            if proj_name_clean:
                cur.execute(f"""
                    INSERT INTO customers (name, phone, email, project_id, stage, assigned_agent, notes, created_at)
                    VALUES (?, ?, '', {proj_clause}, 'appointment', 'Suzanne Tenekecioğlu', ?, datetime('now'))
                    ON CONFLICT(project_id, phone) DO UPDATE SET
                        notes = excluded.notes,
                        stage = 'appointment'
                """, (c_name, c_phone, f"%{proj_name_clean}%", note_text))
            else:
                cur.execute(f"""
                    INSERT INTO customers (name, phone, email, project_id, stage, assigned_agent, notes, created_at)
                    VALUES (?, ?, '', NULL, 'appointment', 'Suzanne Tenekecioğlu', ?, datetime('now'))
                """, (c_name, c_phone, note_text))
            conn.commit()

        logger.info("AI Function Calling: Randevu CRM'e kaydedildi (%s - %s)", c_name, proj_name_clean)
        return f"BAŞARILI: {c_name} adına {proj_name_clean or 'seçkin projelerimiz'} için {pref_dt} randevusu VIP Danışmanımız Suzanne Tenekecioğlu'nun takvimine işlendi. Randevu teyit ve detayları için iletişim numaramız: 0535 489 56 56."
    except Exception as e:
        logger.error("schedule_vip_appointment hatasi: %s", e)
        return f"Randevu talebiniz başarıyla alındı ({customer_name} - {phone}). Danışmanımız Suzanne Tenekecioğlu sizinle en kısa sürede iletişime geçecektir (0535 489 56 56)."


def calculate_investment_plan(total_price, down_payment_percent = 50.0, term_months = 24) -> str:
    """Gayrimenkul alımında peşinat, kalan bakiye, aylık eşit taksit tutarı ve peşin indirim avantajını kesin matematikle hesaplar.
    
    Args:
        total_price: Konutun toplam liste fiyatı (TL cinsinden sayı veya metin)
        down_payment_percent: Yüzde olarak ödenecek peşinat oranı (örn: 50.0 için %50, 40.0 için %40, 0 için %0)
        term_months: Taksit vadesi (ay cinsinden, örn: 12, 24, 30, 36)
    """
    try:
        tot_p = int(_sanitize_numeric(total_price, 0))
        if tot_p <= 0:
            return "Lütfen hesaplama için geçerli bir toplam tutar belirtiniz."
        dp_pct = max(0.0, min(100.0, _sanitize_numeric(down_payment_percent, 50.0)))
        dp_ratio = dp_pct / 100.0
        dp_amount = int(tot_p * dp_ratio)
        remaining = int(tot_p - dp_amount)
        term = max(1, int(_sanitize_numeric(term_months, 24)))
        monthly = int(remaining / term)
        cash_discount_10 = int(tot_p * 0.10)
        cash_price = int(tot_p - cash_discount_10)
        
        return (
            f"FİNANSAL HESAPLAMA SONUCU:\n"
            f"- Liste Fiyatı: {tot_p:,.0f} TL\n"
            f"- Peşin Alım İndirimli Fiyatı (%10 İndirim): {cash_price:,.0f} TL (Peşin Alım Kazancı: {cash_discount_10:,.0f} TL)\n"
            f"- Vadeli Plan: %{dp_pct:.0f} Peşinat = {dp_amount:,.0f} TL\n"
            f"- Kalan Bakiye: {remaining:,.0f} TL\n"
            f"- Vade & Sabit Taksit: {term} Ay x {monthly:,.0f} TL/ay (Faizsiz, şirket içi sabit taksit)"
        ).replace(",", ".")
    except Exception as e:
        return f"Hesaplama hatası: {e}"


def get_project_intelligence(project_name: str) -> str:
    """Belirtilen markalı projenin TKGM ada/parsel, güncel fiyat aralığı, teslim takvimi, video önizleme ve PDF sunum linklerini döner.
    
    Args:
        project_name: Aranacak projenin tam veya kısmi adı (örn. ANGİM BEYTEPE, VIP MARIN, EVART YALIKAVAK)
    """
    proj = _find_project_by_name(project_name)
    if not proj:
        try:
            map_data = json.loads(MAP_FILE.read_text(encoding="utf-8")) if MAP_FILE.exists() else []
            norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())
            target = norm(project_name)
            for p in map_data:
                if target in norm(p.get("title", "")) or target in norm(p.get("folder_name", "")) or target in norm(p.get("name", "")):
                    proj = p
                    break
        except Exception:
            pass

    if not proj:
        return f"'{project_name}' projesi portföyde doğrudan bulunamadı. Lütfen benzer projeler için genel portföyü inceleyiniz."
    
    title = proj.get("name") or proj.get("title") or project_name
    pid = proj.get("id", "")
    video_url = proj.get("drive_video_preview") or proj.get("tanitim_cloud_url") or f"/stream/video/{pid}"
    pdf_url = proj.get("drive_pdf_preview") or f"/stream/pdf/{pid}"
    return (
        f"PROJE BİLGİ KARTI:\n"
        f"- Proje: {title}\n"
        f"- Lokasyon: {proj.get('location', '')} ({proj.get('mahalle', '')} {proj.get('ilce', '')} {proj.get('il', '')})\n"
        f"- Fiyat Aralığı: {proj.get('price_display', 'Danışmana danışınız')}\n"
        f"- Peşinat: {proj.get('down_payment', '%50')}\n"
        f"- Taksit / Vade: {proj.get('installment_terms', '24 Ay Sabit Taksit')}\n"
        f"- TKGM Doğrulaması: Ada {proj.get('ada_no', '-')} / Parsel {proj.get('parsel_no', '-')} (Resmi Onaylı)\n"
        f"- Video Önizleme: {video_url}\n"
        f"- PDF Katalog: {pdf_url}"
    )

NEXA_TOOLS = [schedule_vip_appointment, calculate_investment_plan, get_project_intelligence]


def _gemini_generate(contents, enable_tools=True):
    from google import genai
    from google.genai import types

    TOOL_MAP = {
        "schedule_vip_appointment": schedule_vip_appointment,
        "calculate_investment_plan": calculate_investment_plan,
        "get_project_intelligence": get_project_intelligence
    }

    def _dispatch_function_call(fn_call):
        name = getattr(fn_call, "name", None) or (fn_call.get("name") if isinstance(fn_call, dict) else "")
        raw_args = getattr(fn_call, "args", None) or (fn_call.get("args") if isinstance(fn_call, dict) else {})
        args = dict(raw_args) if raw_args else {}
        func = TOOL_MAP.get(name)
        if not func:
            return f"Hata: Tanımsız fonksiyon '{name}'."
        try:
            logger.info("AI Function Calling executed: %s with args %s", name, args)
            return func(**args)
        except TypeError as te:
            logger.error("Function argument mismatch (%s): %s", name, te)
            return f"Fonksiyon parametre hatası ({name}): {te}"
        except Exception as ex:
            logger.error("Function execution error (%s): %s", name, ex)
            return f"İşlem sırasında hata oluştu: {ex}"

    keys = _get_rotated_api_keys()
    now = time.time()
    with _cache_lock:
        dead = {m for m, exp in _dead_models.items() if exp > now}
    targets = [m for m in FALLBACK_MODELS if m not in dead]
    tools = NEXA_TOOLS if enable_tools else None

    for key in keys:
        if key in _dead_keys:
            continue
        with _cache_lock:
            cd = _key_cooldowns.get(key, 0)
            preferred = _last_good_model.get(key)
        if cd > now:
            logger.warning("Anahtar %s... soğutma süresinde (%ds kaldi)", key[-6:], int(cd - now))
            continue
        model_order = targets if not preferred else [preferred] + [m for m in targets if m != preferred]
        try:
            client = genai.Client(api_key=key)
            config = types.GenerateContentConfig(
                temperature=0.4,
                tools=tools,
            ) if tools else None

            for model in model_order:
                try:
                    if config:
                        resp = client.models.generate_content(model=model, contents=contents, config=config)
                        # Function Calling dispatch handling
                        if resp and resp.function_calls:
                            tool_outputs = []
                            for fn in resp.function_calls:
                                out = _dispatch_function_call(fn)
                                tool_outputs.append(f"[{getattr(fn, 'name', 'Araç')} Sonucu]:\n{out}")
                            follow_up = f"{contents}\n\nARAÇ YANITLARI:\n" + "\n\n".join(tool_outputs) + "\n\nYukarıdaki araç sonuçlarını temel alarak müşteriye şık, net ve elit bir yanıt oluştur."
                            follow_resp = client.models.generate_content(model=model, contents=follow_up)
                            if follow_resp and follow_resp.text:
                                with _cache_lock:
                                    _last_good_model[key] = model
                                return follow_resp.text
                            elif tool_outputs:
                                return "\n\n".join(tool_outputs)
                    else:
                        resp = client.models.generate_content(model=model, contents=contents)

                    if resp and resp.text:
                        with _cache_lock:
                            _last_good_model[key] = model
                        return resp.text
                except Exception as e:
                    msg = str(e)
                    if "leaked" in msg.lower() or "api key not valid" in msg.lower() or "permission_denied" in msg.lower():
                        with _cache_lock:
                            _dead_keys.add(key)
                        logger.warning("Anahtar %s kalici olarak devre disi birakildi", key[-6:])
                        break
                    if _is_quota_error(msg):
                        with _cache_lock:
                            _key_cooldowns[key] = time.time() + KEY_COOLDOWN
                        logger.warning("Anahtar %s kota yok (60sn yasak): %s", key[-6:], msg[:100])
                        break
                    if "404" in msg or "no longer available" in msg:
                        with _cache_lock:
                            _dead_models[model] = time.time() + DEAD_MODEL_TTL
                    logger.warning("Model %s failed (%s)", model, msg[:120])
                    continue
        except Exception as e:
            msg = str(e)
            if _is_quota_error(msg):
                with _cache_lock:
                    _key_cooldowns[key] = time.time() + KEY_COOLDOWN
            logger.warning("Key failed: %s", msg[:120])
            continue
    return _ollama_fallback(contents)


def _is_quota_error(msg):
    m = (msg or "").lower()
    return ("429" in m or "quota" in m or "resource_exhausted" in m
            or "rate limit" in m or "permission" in m or "api key not valid" in m)


def _ollama_fallback(prompt):
    try:
        import httpx
        try:
            ping = httpx.get("http://localhost:11434/api/tags", timeout=1.5)
            if ping.status_code != 200:
                return None
            tags = ping.json().get("models") or []
            if not tags:
                return None
            model = tags[0].get("name")
            if not model:
                return None
        except Exception:
            return None
        resp = httpx.post("http://localhost:11434/api/generate",
                          json={"model": model, "prompt": prompt, "stream": False},
                          timeout=6.0)
        if resp.status_code == 200:
            return (resp.json().get("response") or "")[:2000]
    except Exception:
        pass
    return None


def _find_project_by_name(name):
    if not name:
        return None
    db = _load_db()
    db.row_factory = sqlite3.Row
    try:
        norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").replace("İ", "i").replace("I", "i").replace("ı", "i").lower())
        target = norm(name)
        if "yalikavak" in target or "evart" in target or "bodrum" in target:
            row = db.execute("SELECT * FROM projects WHERE name LIKE '%Yalıkavak%' LIMIT 1").fetchone()
            if row:
                return dict(row)
        if "gokdemir" in target or "imza" in target:
            row = db.execute("SELECT * FROM projects WHERE name LIKE '%GÖKDEMİR İMZA%' LIMIT 1").fetchone()
            if row:
                return dict(row)
        if "ankaport" in target:
            row = db.execute("SELECT * FROM projects WHERE name LIKE '%ANKAPORT%' LIMIT 1").fetchone()
            if row:
                return dict(row)

        best, best_score = None, 0
        for p in db.execute("SELECT * FROM projects WHERE COALESCE(is_portfolio,0) = 0 ORDER BY id ASC"):
            t = norm(p["name"])
            if t and (target in t or t in target):
                score = min(len(target), len(t))
                if score > best_score:
                    best_score, best = score, p
        return dict(best) if best else None
    finally:
        db.close()


_LOCATION_KEYWORDS = ("ulaşım", "aks", "yakınlık", "nerede", "çevre", "hastane", "okul",
                      "üniversite", "metro", "tramvay", "otoyol", "havalimanı", "avm",
                      "konum", "mesafe", "bölge", "site", "çevresinde", "manzara")

# Y5/B9: Ollama 8K context'e sığmayan dev global bağlam için üst sınır
# (Gemini 1M context destekliyor; kırpma yalnızca 8K yollardaki taşmayı önlemek için güvenlik bandı)
MAX_PROMPT_CHARS = 12000


def _trim_middle(text, limit=MAX_PROMPT_CHARS):
    """Uzun bağlamı ortadan kırpar; baş (sistem kuralları) ve son (kullanıcı sorusu) korunur."""
    if not text or len(text) <= limit:
        return text
    head_n = int(limit * 0.45)
    tail_n = limit - head_n - len("...[BAĞLAM ORTADAN KIRPILDI (karakter sınırı)...]")
    marker = "\n...[BAĞLAM ORTADAN KIRPILDI (karakter sınırı)]...\n"
    return text[:head_n] + marker + text[-tail_n:]


def _load_summaries():
    try:
        if SUMMARIES_FILE.exists():
            return json.loads(SUMMARIES_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_summaries(data):
    try:
        with _save_lock:
            tmp = SUMMARIES_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(SUMMARIES_FILE)
    except Exception as e:
        logger.warning("Ozet kaydedilemedi: %s", e)


def build_project_summary(proj):
    context = build_project_context(proj["id"])
    prompt = f"""
Sen Nexa portföy danışmanısın. Aşağıdaki proje verilerinden kısa, net ve satış odaklı bir PROJE ÖZETİ üret.
Format (madde madde, en fazla 8 satır, başlık satırı olmadan):
- Konum ve proje kimliği
- Proje konsepti, kat/blok ve daire tipleri
- Fiyat ve ödeme planı özeti (varsa gerçek rakamlar)
- Teslim süresi (varsa)
- Tapu/TKGM durumu (ada/parsel)

Uydurma veri ekleme; bilinmeyeni yazma.

PROJE: {proj['name']}
VERİ:
{context}
"""
    reply = _gemini_generate(prompt)
    if reply and len(reply.strip()) > 40:
        return reply.strip()
    return None


def generate_all_project_summaries(force=False):
    """Drive (markalı) projelerin her biri için özeti otomatik üretir ve önbelleğe alır."""
    data = {} if force else _load_summaries()
    db = _load_db()
    db.row_factory = sqlite3.Row
    try:
        projects = db.execute(
            "SELECT * FROM projects WHERE COALESCE(is_portfolio,0) = 0 ORDER BY id ASC").fetchall()
    finally:
        db.close()
    done = 0
    for p in projects:
        name = p["name"]
        if not force and data.get(name, {}).get("summary"):
            continue
        try:
            s = build_project_summary(dict(p))
            if s:
                data[name] = {"summary": s, "project_id": p["id"], "ts": time.time()}
                done += 1
                logger.info("Ozet uretildi: %s", name)
                _save_summaries(data)
            time.sleep(0.7)
        except Exception as e:
            logger.warning("Ozet uretilemedi %s: %s", name, e)
            continue
    _save_summaries(data)
    return done


def get_project_summary(name):
    return _load_summaries().get(name, {}).get("summary") or ""


def cognitive_chat(user_message, project=None, history=None):
    """
    NEXA PRIME seviyesinde bilişsel cevap üretir.
    project: name ile eşleşen project dict (varsa tekil proje modu).
    history: son 6-8 mesajdan oluşan [{"role": "user"/"assistant", "text": ...}] listesi (E3).
    Başarısızlıkta None döner; çağıran heuristic'e düşer.
    """
    msg = (user_message or "").strip()
    if not msg:
        return None
    is_location_query = any(kw in msg.lower() for kw in _LOCATION_KEYWORDS)

    # P8: 5 dk TTL'li yanıt önbelleği — soru + geçmiş bazlı MD5 anahtarı
    import hashlib
    hist_snippet = ""
    if history:
        hist_snippet = "|".join([f"{h.get('role')}:{h.get('content') or h.get('text')}" for h in history[-3:] if isinstance(h, dict)])
    proj_prefix = ("P:" + project["name"]) if project else "GLOBAL"
    raw_key = f"{proj_prefix}::{msg.lower().strip()}::{hist_snippet}"
    cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    with _cache_lock:
        cached = _reply_cache.get(cache_key)
        if cached and (time.time() - cached[1] < REPLY_TTL):
            return cached[0]

    def _cached(reply):
        if reply:
            with _cache_lock:
                _reply_cache[cache_key] = (reply, time.time())
                if len(_reply_cache) > 200:
                    stale = [k for k, (_, ts) in _reply_cache.items() if time.time() - ts > REPLY_TTL]
                    for k in stale:
                        _reply_cache.pop(k, None)
        return reply

    history_block = ""
    if history:
        turns = []
        def _clean_hist_text(t):
            cleaned = re.sub(r"(?i)(system\s*:|kurallar\s*:|sen\s+nexa\s+değilsin|canonical)", "", str(t))
            return re.sub(r"[\r\n]+", " ", cleaned).strip()[:350]

        for h in history[-8:]:
            role = h.get("role") if isinstance(h, dict) else "user"
            text = (h.get("content") or h.get("text") if isinstance(h, dict) else str(h) or "").strip()
            clean_t = _clean_hist_text(text)
            if clean_t:
                speaker = "MUSTERI" if role == "user" else "ASISTAN"
                turns.append(f"<{speaker}>{clean_t}</{speaker}>")
        if turns:
            history_block = "<SOHBET_GECMISI>\n" + "\n".join(turns) + "\n</SOHBET_GECMISI>\n\n"

    if not project:
        try:
            from nexa_ai_engine import extract_keywords_and_projects
            named = extract_keywords_and_projects(msg)
            if len(named) == 1:
                project = _find_project_by_name(named[0])
        except Exception:
            pass

    if project:
        is_broad_overview = (
            len(msg) < 30 and (
                msg.lower().strip() in (project["name"].lower(), "özet", "bilgi", "detay", "nedir") or
                any(w in msg.lower() for w in ["hakkında bilgi", "özeti nedir", "genel bakış", "tanıt"])
            )
        )
        if is_broad_overview and not is_location_query:
            cached = get_project_summary(project["name"])
            if cached:
                return _cached(f"**{project['name']} — Proje Özeti**\n\n{cached}\n\n{CONTACT_LINE}")
        context = build_project_context(project["id"], query=msg)
        geo = ""
        if is_location_query or not context:
            geo = fetch_proximity_geo_intelligence(
                project.get("il") or "", project.get("ilce") or "",
                project.get("mahalle") or "", project["name"])
        canonical_matrix = _build_canonical_matrix()
        system = f"""
Sen Coldwell Banker VIP Gayrimenkul Baş Danışmanı **Suzanne Tenekecioğlu'nun Kıdemli Bilişsel Portföy & Yatırım Danışmanısın** (NEXA PRIME v2).
İncelenen Proje: {project['name']}
Lokasyon: {project.get('location') or project.get('ilce') or ''}
Fiyat: {project.get('price_display') or ''} | Peşinat: {project.get('down_payment') or ''} | Taksit: {project.get('installment_terms') or ''} | Teslim: {project.get('delivery_months') or ''} Ay
Daire Tipleri: {project.get('room_info') or ''} | Ada/Parsel: {project.get('ada_no') or ''}/{project.get('parsel_no') or ''} (TKGM Onay: {'Evet' if project.get('tkgm_verified') else 'Ruhsatlı'})

CANONICAL PROJE GERÇEKLERİ:
{canonical_matrix}

{history_block}
RAG DOKÜMAN BAĞLAMI:
{context if context else 'Proje resmi kayıtları ve fiyat listesi geçerlidir.'}

GEO BİLGİSİ:
{geo if geo else ''}

<KULLANICI_SORUSU>
{msg}
</KULLANICI_SORUSU>

Kurallar:
1. Kullanıcının sorusuna DOĞRUDAN ve NET yanıt ver (örneğin teslim tarihi sorulmuşsa teslim süresini ve inşaat durumunu net olarak açıkla).
2. Fiyat, teslimat süresi, metrekare, ödeme planı ve ada/parsel bilgilerini yukarıdaki doğrulanmış verilerden birebir aktar.
3. Elit, ikna edici, profesyonel bir üslup ve şık Markdown formatı (madde imleri, kalın başlıklar) kullan.
4. Sonuna şu iletişim satırını ekle: {CONTACT_LINE}
Cevabı 400 kelimeyi aşmadan Türkçe yaz.
"""
        system = _trim_middle(system, 6000)
    else:
        summaries = _load_summaries()
        summ_block = "\n".join(
            f"- {n}: {d.get('summary', '')[:200]}" for n, d in list(summaries.items())[:10] if d.get("summary"))
        canonical_matrix = _build_canonical_matrix()
        system = f"""
Sen Coldwell Banker VIP Gayrimenkul Baş Danışmanı **Suzanne Tenekecioğlu'nun Kıdemli Bilişsel Portföy & Yatırım Danışmanısın** (NEXA PRIME v2).
Tüm portföydeki MARKALI PROJELERİ ve VIP gayrimenkulleri analiz eden lüks yatırım danışmanısın.

{history_block}
CANONICAL VERİLEN GÜNCEL PROJE GERÇEKLERİ (BU VERİLERİ KESİNLİKLE BİREBİR KULLAN, ASLA DEĞİŞTİRME VEYA UYDURMA):
{canonical_matrix}

PROJE ÖZETLERİ:
{summ_block}

<KULLANICI_SORUSU>
{msg}
</KULLANICI_SORUSU>

Kurallar:
0. SELAMLAMA & TANIŞMA ("merhaba", "selam", "günaydın" vb.): Kendini tanıt, Ankara, Bodrum ve Alanya portföyümüzü özetle, bütçe/bölge sor. Rastgele liste dökme.
1. YATIRIM & TAVSİYE SORULARI: Kullanıcı bütçesine veya amacına göre en yüksek getiri sağlayan projeleri (kira getirisi, prim, şirket içi taksit) nedenleriyle öner.
2. YAZLIK / SAHİL / TATİL / VİLLA sorularında: Portföyümüzdeki Alanya VIP MARIN, Bodrum EVART YALIKAVAK ve İncek lüks villalarını açıkça tanıt.
3. Bilgi bağlamda yoksa "danışmanımız netleştirecektir" de.
4. Markdown formatında, şık madde ve tablolarla 450 kelimeyi aşmadan Türkçe yaz.
Sonuna şu iletişim satırını ekle: {CONTACT_LINE}
"""
        system = _trim_middle(system, 12000)
    try:
        reply = _gemini_generate(system)
        if reply and len(reply.strip()) > 20:
            return _cached(reply.strip())
    except Exception as e:
        logger.error("Cognitive generation failed: %s", e)
    return None


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("— GLOBAL TEST —")
    print(cognitive_chat("En uygun fiyatlı 3+1 projeler hangileri? 5 milyon bütçem var."))
    print()
    print("— TEKİL PROJE TESTI —")
    proj = _find_project_by_name("MONZA MOON")
    print(cognitive_chat("Bu projenin fiyat ve ödeme planını anlatır mısın?", project=proj))