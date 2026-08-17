import sys
import re
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ai_engine_path = Path(r"C:\Users\USER\Desktop\3\nexa_ai_engine.py")
code = ai_engine_path.read_text(encoding="utf-8")

# 1. Add Cheap / Affordable query detection in score_item
old_scoring_block = """    # 8) Kriter belirtilmediyse (ör. "En Uygun Projeler") Ankara portföyü öne çıkar
    ankara_scope = (not regions) or (len(regions) == 1 and norm_text(regions[0]) == "ankara")
    if ankara_scope and not named_projects and not rooms and not budget:
        if il == "ankara":
            score += 10
            parts.append("Ankara portföyünde öne çıkan proje")"""

new_scoring_block = """    # 8) "En ucuz" / "En uygun" / "Ekonomik" sorgu optimizasyonu
    is_cheap_query = any(w in norm_text(item.get("_query_raw", "")) for w in ["ucuz", "en uygun", "ekonomik", "en dusuk", "dusuk fiyat", "butceme uygun"])
    if is_cheap_query and pmin:
        if pmin <= 1500000:
            score += 45
            parts.append(f"Portföyün en avantajlı başlangıç fiyatına ({item.get('price_display')}) sahip projesidir")
        elif pmin <= 2000000:
            score += 35
            parts.append(f"2 Milyon TL altı bütçede ekonomik seçenektir ({item.get('price_display')})")
        elif pmin <= 3500000:
            score += 20
            parts.append(f"Bölge ortalamasının altında fiyat avantajı sunar")

    # 9) Kriter belirtilmediyse (ör. "En Uygun Projeler") Ankara portföyü öne çıkar
    ankara_scope = (not regions) or (len(regions) == 1 and norm_text(regions[0]) == "ankara")
    if ankara_scope and not named_projects and not rooms and not budget and not is_cheap_query:
        if il == "ankara":
            score += 10
            parts.append("Ankara portföyünde öne çıkan proje")"""

code = code.replace(old_scoring_block, new_scoring_block)

# 2. Add lead scoring and pass query_raw to score_item
old_process_loop = """    scored = []
    for it in items:
        # Kişisel portföy ilanları yalnızca kiralık isteminde skorlanır (kiralık envanter botta görünür)
        if it.get("type") == "portfolio" and want_type != "Kiralık":
            continue
        s, parts = score_item(it, budget, regions, rooms, goals, want_type, named_projects, ada_parsel)
        scored.append((s, it, parts))
    scored.sort(key=lambda x: -x[0])"""

new_process_loop = """    # Lead Qualification Scoring (1-10)
    lead_score = 3
    if any(w in ql for w in ["gormek", "randevu", "bu hafta", "yerinde", "satin al", "arayin", "gorusmek", "ofisiniz"]):
        lead_score = 9  # HOT LEAD
    elif any(w in ql for w in ["butcem", "odeme", "pesinat", "taksit", "kredi", "vade", "nakit"]):
        lead_score = 7  # SERIOUS LEAD
    elif any(w in ql for w in ["fiyat", "kac para", "teslim", "ne zaman", "m2", "kac daire"]):
        lead_score = 5  # CURIOUS LEAD
    else:
        lead_score = 3  # DISCOVERY

    scored = []
    for it in items:
        it["_query_raw"] = q
        # Kişisel portföy ilanları yalnızca kiralık isteminde skorlanır (kiralık envanter botta görünür)
        if it.get("type") == "portfolio" and want_type != "Kiralık":
            continue
        s, parts = score_item(it, budget, regions, rooms, goals, want_type, named_projects, ada_parsel)
        scored.append((s, it, parts))
    scored.sort(key=lambda x: -x[0])"""

code = code.replace(old_process_loop, new_process_loop)

# 3. Add lead_score to return object
old_return_block = """    return {
        "success": True,
        "response": "\\n".join(lines),
        "extracted_info": {
            "budget_tl": budget,
            "regions": regions,
            "rooms": rooms,
            "goals": goals
        },
        "projects": project_cards
    }"""

new_return_block = """    return {
        "success": True,
        "response": "\\n".join(lines),
        "lead_score": lead_score,
        "extracted_info": {
            "budget_tl": budget,
            "regions": regions,
            "rooms": rooms,
            "goals": goals
        },
        "projects": project_cards
    }"""

code = code.replace(old_return_block, new_return_block)

ai_engine_path.write_text(code, encoding="utf-8")
print("nexa_ai_engine.py successfully updated with cheap query ranking and lead scoring!")
