import requests
import time

# Configuration
BASE_URL = "https://agridirect-civ.onrender.com"

def test_health():
    print(f"🌍 Testing Health Check: {BASE_URL}/health/")
    try:
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/health/", timeout=20)
        print(f"✅ Health Status: {r.status_code} (took {time.time()-t0:.2f}s)")
        print(f"📝 Body: {r.text}")
    except Exception as e:
        print(f"❌ Health Failed: {str(e)}")

if __name__ == "__main__":
    test_health()
