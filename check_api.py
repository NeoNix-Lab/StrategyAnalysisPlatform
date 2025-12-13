import requests
import sys

try:
    print("Testing connection to http://127.0.0.1:8000/health...")
    r = requests.get("http://127.0.0.1:8000/health", timeout=2)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")

try:
    print("\nTesting connection to http://localhost:8000/health...")
    r = requests.get("http://localhost:8000/health", timeout=2)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
