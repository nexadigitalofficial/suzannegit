#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXA AI v2 — Enhanced Project Analysis Pipeline
Masaüstü NEXA_PRIME v2 Enterprise veritabanından aktarılan GERÇEK proje/portföy verisiyle çalışır.
Her sorgu, bütçe / bölge / oda / amaç kıstaslarına göre GERÇEK puanlanır;
her proje için kendi verisinden (ilçe, ada/parsel, TKGM onayı, fiyat, oda, alan)
farklı gerekçeler (rationale) döndürülür.
Dialog yöneticisi: niyet tespiti, varlık çıkarma,clarification & context memory desteklidir.
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "nexa_portfolio_data.json"
MAP_FILE = BASE_DIR / "projects_map.json"

# ─── VERİ YÜKLEME ───
import logging as _eng_log
_eng_logger = logging.getLogger("nexa.engine")

def load_portfolio():
    """Öncelik: güncel proje haritası (31 kart); portföy ilanları zengin dosyadan eklenir."""
    items = []
    if MAP_FILE.exists():
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                for it in json.load(f):
                    it = dict(it)
                    it.setdefault("type", "project")
                    items.append(it)
        except Exception as e:
            _eng_logger.warning("projects_map.json yuklenemedi: %s", e)
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                for it in json.load(f):
                    if it.get("type") == "portfolio":
                        items.append(it)
        except Exception as e:
            _eng_logger.warning("nexa_portfolio_data.json yuklenemedi (portfoy atlandi): %s", e)
    return items

# ─── NİTELİK ÇIKARIMI ───
ILCELER = [
    "çankaya", "cankaya", "etimesgut", "yenimahalle", "pursaklar", "çubuk", "cubuk",
    "gölbaşı", "golbasi", "sincan", "odunpazarı", "odunpazari", "bodrum", "alanya",
    "yahşihan", "yahsihan", "keçiören", "kecioren", "mamak", "eryaman", "batıkent",
    "muğla", "mugla", "yalıkavak", "yalikavak",
]

MAHALLELER = [
    "beytepe", "yasamkent", "yasamkent", "çakırlar", "cakirlar", "incek",
    "çayyolu", "cayyolu", "ümitköy", "umitkoy", "yalıkavak", "cevizlidere",
    "egrikin", "eğrikin", "horos", "mustafa kemal", "atatürk", "adil bey",
]

PROJE_SINONIMLERI = {
    "angim": "ANGİM BEYTEPE", "angim beytepe": "ANGİM BEYTEPE", "beytepe": "ANGİM BEYTEPE",
    "ankaport": "ANKAPORT - SARAY", "ankaport saray": "ANKAPORT - SARAY",
    "evart": "EVART YALIKAVAK", "evart yalikavak": "EVART YALIKAVAK",
    "grande": "GRANDE YAŞAMKENT", "grande yaşamkent": "GRANDE YAŞAMKENT",
    "gökdemir star": "GÖKDEMİR STAR", "gokdemir star": "GÖKDEMİR STAR",
    "gökdemir imza": "GÖKDEMİR İMZA", "gokdemir imza": "GÖKDEMİR İMZA",
    "gökdemir": "GÖKDEMİR İMZA", "gokdemir": "GÖKDEMİR İMZA",
    "idea": "IDEA - START BRAVO", "start bravo": "IDEA - START BRAVO",
    "joven": "JOVEN KAMPÜS", "joven kampüs": "JOVEN KAMPÜS", "joven port": "JOVEN PORT",
    "bordo": "BORDO YAŞAM", "bordo yaşam": "BORDO YAŞAM",
    "monza moon": "MONZA MOON", "monza": "MONZA EYLÜL CONCEPT",
    "narcin": "NARÇİN RONYA CITY - 1", "narcın": "NARÇİN RONYA CITY - 1", "ronya": "NARÇİN RONYA CITY - 1",
    "neva": "NEVA - START BRAVO", "nest": "NEST İNCEK", "nest incek": "NEST İNCEK",
    "s point": "S POINT - VIP SARAY", "spoint": "S POINT - VIP SARAY",
    "smd": "SMD TWIN", "smd twin": "SMD TWIN", "smd protokol": "SMD PROTOKOL",
    "triole": "TRIOLE YAŞAM", "excelance": "EXCELANCE VADİ", "excelance vadi": "EXCELANCE VADİ",
    "excelance beytepe": "EXCELANCE BEYTEPE",
    "verde": "VERDE MONA", "verde mona": "VERDE MONA",
    "vip akademi": "VIP AKADEMİ", "vip akademi 2": "VIP AKADEMİ 2",
    "vip marin": "VIP MARIN", "vip yaşamkent": "VIP YAŞAMKENT - GÖKDEMİR STAR",
    "vip yenikent": "VIP YENİKENT", "vip çakırlar": "VIP ÇAKIRLAR",
    "vip üniversite": "VIP ÜNİVERSİTE", "viva": "VIVA - START BRAVO",
    "wm prime": "WM - PRIME", "wm": "WM - PRIME",
}

def norm_text(t):
    """Metni normalize eder: küçük harf, Türküceraretler temizler."""
    s = (t or "").replace("İ", "i").replace("I", "ı").lower()
    s = s.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    return s.replace("\u0307", "")

# ─── NİYET TESPİTİ ───
def detect_intent(text):
    """
    Kullanıcının mesajını analiz ederek PRIMARY intent ve SECONDARY intent'leri belirler.
    Returns: (primary_intent, secondary_intents_list, entities_dict)
    """
    t = norm_text(text)
    
    # Intent definitions with keywords
    intents = {
        "project_search": ["proje", "ilan", "arayıorum", "bul", "projeler"],
        "villa_search": ["yazlık", "villa", "villas", "luxury", "premium", "duplex", "vip villa"],
        "rental_search": ["kiralık", "kiralik", "kira", "kiracı", "kiralama"],
        "budget_inquiry": ["bütçe", "fiyat", "maliyet", "para", "cost"],
        "region_inquiry": ["bölge", "il", "ilçe", "nerede", "where", "bolge"],
        "room_query": ["oda", "odasını", "3+1", "2+1", "1+1", "oda sayısı"],
        "tkdm_inquiry": ["tkgm", "tapu", "kira assimil"],
        "comparison": ["karşılaştırma", "farklı mı", "farklı projeler"],
        "small_talk": ["merhaba", "nasılsın", "günaydın", "hoşça kal", "teşekkür"],
    }
    
    # Score each intent by keyword matches
    scores = {}
    for intent, keywords in intents.items():
        score = sum(1 for w in keywords if w in t)
        if score > 0:
            scores[intent] = score
    
    # Primary intent: highest score (break ties by predefined order)
    primary = max(scores.keys(), key=lambda k: (scores[k], list(intents.keys()).index(k))) if scores else "general"
    
    # Secondary intents: other intents with score > 0
    secondary = [k for k, v in scores.items() if k != primary]
    
    # Entity extraction
    entities = extract_all_entities(text)
    
    return primary, secondary, entities


# ─── AĞIRLIKLI SORU SORMA ───
def generate_clarification_question(missing_fields):
    """
    Eksik bilgi gerektendiğinde kullanıcıya sorulacak akıllı soruları üretir.
    """
    questions = {
        "budget": "Bütçeniz ne kadardır? (örnek: 5 milyon TL, 10-15 milyon TL aralığı)",
        "region": "Hangi bölgeyi tercih ediyorsunuz? (Ankara, Çankaya, Şişli, bodrum vb.)",
        "rooms": "Kaç oda arıyorsunuz? (1+1, 2+1, 3+1 vb.)",
        "property_type": "Hangı tipi arıyorsunuz? (daire, villa,_ofis)",
        "timeframe": "Projeniz ne zaman teslim edilecek? (hemen, 3 ay, 6 ay vb.)",
    """
    
    questions_list = []
    for field in missing_fields:
        if field in questions:
            questions_list.append(questions[field])
    
    if len(questions_list) == 1:
        return questions_list[0]
    elif len(questions_list) == 2:
        return f"{questions_list[0]} ve {questions_list[1]}?"
    elif len(questions_list) >= 3:
        return "Lütfen aşağıdaki bilgileri giriniz: " + "; ".join(questions_list[:3])
    else:
        return "Lütfen ekstra bilgi giriniz."


# ─── CONTEXT YÖNETİCİ ───
class ConversationContext:
    """Kullanıcı ile yapılan etkileşimi hafızalandır ve ileriye taşır."""
    def __init__(self):
        self.budget = None
        self.region = None
        self.rooms = None
        self.property_type = None
        self.want_type = None
        self.goals = []
        self.conversation_history = []
        
    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def add_history(self, user_msg, bot_resp):
        self.conversation_history.append({"user": user_msg, "bot_resp": bot_resp})
        # Keep only last 8 exchanges to manage memory
        if len(self.conversation_history) > 8:
            self.conversation_history = self.conversation_history[-8:]

# ─── VARLIK ÇIKARIMI ───
def extract_all_entities(text):
    """Metinden tüm çıkarılabilir varlığı (entities) çeker."""
    t = norm_text(text)
    entities = {}
    
    # Budget extraction
    budget = extract_budget(text)
    if budget:
        entities["budget"] = budget
    
    # Region extraction
    region = extract_region(text)
    if region:
        entities["region"] = region
    
    # Room count
    rooms = extract_rooms(text)
    if rooms:
        entities["rooms"] = rooms
    
    # Property type detection
    prop_type = detect_property_type(t)
    if prop_type:
        entities["property_type"] = prop_type
    
    # TKGM status
    tkdm_keywords = ["tkgm", "tapu", "kira assimil"]
    if any(k in t for k in tkdm_keywords):
        entities["tkdm"] = True
    
    # Timeframe
    timeframe_keywords = ["hemen", "bu ay", "bu yil", "yarın", "bu hafta", "3 ay", "6 ay", "teslim"]
    tfound = [kw for kw in timeframe_keywords if kw in t]
    if tfound:
        entities["timeframe"] = tfound[0]
    
    return entities

# ─── ... (diğer fonksiyonlar devam eder) ---
# extract_budget, extract_region, extract_rooms, extract_goals, extract_ada_parsel, 
# extract_keywords_and_projects, score_item, build_project_context, build_global_context
# ve diğer fonksiyonlar ORİGİNAL kodla korunmalıdır.

# ─── SON TESTLER ───
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    tests = [
        "Ankara'da 3+1 proje arıyorum, bütçem 5 milyon",
        "Çankaya İlanları",
        "En Uygun Projeler",
        "Kiralık ofis arıyorum Çankaya'da bütçem 60 bin",
        "5-10M yatırım için lüks proje önerir misin?",
        "Gölbaşı'nda arsa veya villa var mı?",
        "MONZA MOON hakkında bilgi ver",
    ]
    for t in tests:
        print("=" * 70)
        print("SORU:", t)
        # process_nexa_query would be called here in the original code
        print("(test modu - process_nexa_query kullanılmıyor)")
"