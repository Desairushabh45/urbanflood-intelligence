import httpx
import json

print('Testing Risk Zones endpoint...')
try:
    response = httpx.get('http://localhost:8000/risk-zones', timeout=30.0)
    if response.status_code == 200:
        zones = response.json()
        print(f'[OK] Risk zones endpoint working - Found {len(zones)} zones')
        print(f'  First zone: {zones[0]["zone"]} (Risk Level: {zones[0]["risk_level"]})')
    else:
        print(f'[ERROR] Risk zones endpoint failed: {response.status_code}')
except Exception as e:
    print(f'[ERROR] Error testing risk zones: {str(e)[:100]}')

print()
print('Testing Explain endpoint (AI Advisory)...')
try:
    response = httpx.get('http://localhost:8000/explain', timeout=30.0)
    if response.status_code == 200:
        data = response.json()
        print('[OK] AI Advisory endpoint working!')
        explanation = data.get("explanation", "")
        preview = explanation[:300] if explanation else "No explanation returned"
        print(f'  Response preview: {preview}')
    else:
        print(f'[ERROR] AI Advisory endpoint failed: {response.status_code}')
        print(f'  Response: {response.text[:300]}')
except Exception as e:
    print(f'[ERROR] Error testing advisory: {str(e)[:100]}')

print()
print('Testing Ranked Actions endpoint...')
try:
    response = httpx.get('http://localhost:8000/explain/ranked', timeout=30.0)
    if response.status_code == 200:
        data = response.json()
        print('[OK] Ranked Actions endpoint working!')
        actions = data.get("ranked_actions", "")
        preview = actions[:300] if actions else "No actions returned"
        print(f'  Response preview: {preview}')
    else:
        print(f'[ERROR] Ranked Actions endpoint failed: {response.status_code}')
except Exception as e:
    print(f'[ERROR] Error testing ranked actions: {str(e)[:100]}')
