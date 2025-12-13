import urllib.request
import sys

def test_url(url):
    print(f"Testing {url}...")
    try:
        # Increased timeout
        with urllib.request.urlopen(url, timeout=5) as response:
            print(f"Status: {response.getcode()}")
            print(f"Body: {response.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")

test_url("http://127.0.0.1:8000/health")
