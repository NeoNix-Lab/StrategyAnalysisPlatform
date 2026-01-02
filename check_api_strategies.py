import requests
import json

API_URL = "http://127.0.0.1:8000/api/strategies/"

try:
    print(f"🌍 Requesting: {API_URL}")
    response = requests.get(API_URL)
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Received {len(data)} strategies.")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Failed: {response.text}")

except Exception as e:
    print(f"❌ Connection Error: {str(e)}")
