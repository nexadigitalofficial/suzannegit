import requests
base_url = 'http://127.0.0.1:8099'

# Test 1: 'yazlık istiyorum'
payload = {'message': 'yazlık istiyorum', 'history': []}
r = requests.post(f'{base_url}/api/nexa-ai-chat', json=payload)
j = r.json()
print('=== Test 1: yazlık istiyorum ===')
gi = j.get('extracted_info', {})
print('Goals:', gi.get('goals'))
wt = j.get('extracted_info', {}).get('want_type')
print('Want type:', wt)
proj = j.get('projects', [])
print('Projects:')
for p in proj:
    print('  -', p.get('title'), '|', p.get('match_percent'), '% |', p.get('region'))
print()

# Test 2: 'satılık'
payload2 = {'message': 'satılık projeler', 'history': []}
r2 = requests.post(f'{base_url}/api/nexa-ai-chat', json=payload2)
j2 = r2.json()
print('=== Test 2: satılık projeler ===')
gi2 = j2.get('extracted_info', {})
print('Goals:', gi2.get('goals'))
wt2 = j2.get('extracted_info', {}).get('want_type')
print('Want type:', wt2)
proj2 = j2.get('projects', [])
print('Projects:')
for p in proj2:
    print('  -', p.get('title'), '|', p.get('match_percent'), '% |', p.get('region'))
print()

# Test 3: 'villa'
payload3 = {'message': 'villa', 'history': []}
r3 = requests.post(f'{base_url}/api/nexa-ai-chat', json=payload3)
j3 = r3.json()
print('=== Test 3: villa ===')
gi3 = j3.get('extracted_info', {})
print('Goals:', gi3.get('goals'))
wt3 = j3.get('extracted_info', {}).get('want_type')
print('Want type:', wt3)
proj3 = j3.get('projects', [])
print('Projects:')
for p in proj3:
    print('  -', p.get('title'), '|', p.get('match_percent'), '% |', p.get('region'))
print()

# Test 4: 'yazlık satılık'
payload4 = {'message': 'yazlık satılık', 'history': []}
r4 = requests.post(f'{base_url}/api/nexa-ai-chat', json=payload4)
j4 = r4.json()
print('=== Test 4: yazlık satılık ===')
gi4 = j4.get('extracted_info', {})
print('Goals:', gi4.get('goals'))
wt4 = j4.get('extracted_info', {}).get('want_type')
print('Want type:', wt4)
proj4 = j4.get('projects', [])
print('Projects:')
for p in proj4:
    print('  -', p.get('title'), '|', p.get('match_percent'), '% |', p.get('region'))
print()