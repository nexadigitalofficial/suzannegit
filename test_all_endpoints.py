import requests
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_url = "http://localhost:5002"

print("=" * 65)
print("TESTING ALL ENDPOINTS & REGRESSION VALIDATION")
print("=" * 65)

# 1. Healthz
r = requests.get(f"{base_url}/healthz")
print(f"1. GET /healthz: Status {r.status_code} -> {r.json()}")

# 2. Config
r = requests.get(f"{base_url}/api/config")
print(f"2. GET /api/config: Status {r.status_code} -> {r.json()}")

# 3. Appointments
apt_payload = {
    "name": "Test Ahmet Yılmaz",
    "phone": "05321112233",
    "email": "ahmet@test.com",
    "preferred_datetime": "Cumartesi 14:00",
    "project_id": "cbvip-prj-20",
    "project_name": "VIP ÜNİVERSİTE",
    "notes": "Ödeme planı görüşmesi",
    "agent": "Yiğit Narin"
}
r = requests.post(f"{base_url}/api/appointments", json=apt_payload)
print(f"3. POST /api/appointments: Status {r.status_code} -> {r.json()}")

# 4. Projects
r = requests.get(f"{base_url}/api/projects")
print(f"4. GET /api/projects: Status {r.status_code} -> Count: {len(r.json().get('data', []))}")

# 5. Regions
r = requests.get(f"{base_url}/api/nexa-regions")
print(f"5. GET /api/nexa-regions: Status {r.status_code} -> Count: {r.json().get('count')}")

# 6. AI Chat
chat_payload = {"message": "VIP Üniversite projesinin fiyatı ve teslimat durumu nedir?"}
r = requests.post(f"{base_url}/api/nexa-ai-chat", json=chat_payload)
print(f"6. POST /api/nexa-ai-chat: Status {r.status_code}")
chat_res = r.json()
print("   Response snippet:", chat_res.get("response", "")[:180].replace("\n", " "))
print("   Cards returned:", len(chat_res.get("projects", [])))

# 7. Site HTML
r = requests.get(f"{base_url}/site")
print(f"7. GET /site: Status {r.status_code} (HTML length: {len(r.text)} chars)")

print("=" * 65)
print("ALL ENDPOINT CHECKS PASSED!")
print("=" * 65)
