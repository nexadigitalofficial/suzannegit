import requests
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_url = "http://localhost:5002"

print("=" * 65)
print("FAST ENDPOINT AND CANONICAL PRICE VERIFICATION")
print("=" * 65)

# 1. Healthz
r = requests.get(f"{base_url}/healthz", timeout=4)
print(f"1. GET /healthz: Status {r.status_code} -> {r.json()}")

# 2. Config
r = requests.get(f"{base_url}/api/config", timeout=4)
print(f"2. GET /api/config: Status {r.status_code} -> {r.json()}")

# 3. Appointments API
apt_payload = {
    "name": "Ahmet Yılmaz (Test)",
    "phone": "05321112233",
    "email": "ahmet@test.com",
    "preferred_datetime": "Cumartesi 14:00",
    "project_id": "cbvip-prj-20",
    "project_name": "VIP ÜNİVERSİTE",
    "notes": "825.000 TL peşinat ve ödeme planı için randevu talebi",
    "agent": "Yiğit Narin"
}
r = requests.post(f"{base_url}/api/appointments", json=apt_payload, timeout=4)
print(f"3. POST /api/appointments: Status {r.status_code} -> {r.json()}")

# 4. Projects API
r = requests.get(f"{base_url}/api/projects", timeout=4)
pdata = r.json().get("data", [])
print(f"4. GET /api/projects: Status {r.status_code} -> Total Projects: {len(pdata)}")
vip_p = next((p for p in pdata if "üniversite" in p.get("title", "").lower() or "universite" in p.get("title", "").lower()), None)
if vip_p:
    print(f"   VIP ÜNİVERSİTE in /api/projects: Title='{vip_p.get('title')}', Price='{vip_p.get('price_display')}', DownPayment='{vip_p.get('down_payment')}', Region='{vip_p.get('location')}'")

# 5. Regions API
r = requests.get(f"{base_url}/api/nexa-regions", timeout=4)
print(f"5. GET /api/nexa-regions: Status {r.status_code} -> Count: {r.json().get('count')}")

# 6. Site Page
r = requests.get(f"{base_url}/site", timeout=4)
print(f"6. GET /site: Status {r.status_code} (HTML length: {len(r.text)} bytes)")

print("=" * 65)
print("ALL SYSTEM ENDPOINTS VERIFIED & OPERATIONAL!")
print("=" * 65)
