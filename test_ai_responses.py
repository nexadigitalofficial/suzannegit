import sys
import json
from nexa_ai_engine import process_nexa_query

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

tests = [
    "2 milyonun altında ne var?",
    "VIP Üniversite projesinin fiyatı ve detayları nedir?",
    "Ankara 1.5 milyon bütçem var yatırım arıyorum",
    "En ucuz proje hangisi?"
]

for q in tests:
    print("=" * 65)
    print("SORU:", q)
    res = process_nexa_query(q)
    print("AI YANITI:")
    print(res.get("response"))
    projects = res.get("projects", [])
    print(f"EŞLEŞEN KART SAYISI: {len(projects)}")
    for c in projects[:3]:
        print(f" * {c.get('title')} | {c.get('price_display')} | {c.get('region')} | %{c.get('match_percent')}")
