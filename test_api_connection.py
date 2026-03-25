import requests
import json
import time

# Configuration
BASE_URL = "https://agridirect-civ.onrender.com"
API_URL = f"{BASE_URL}/api"
TEST_PHONE = "+2250102030405"
TEST_PASS = "password123"

def test_connection():
    # 1. Test Root
    print(f"🌍 1. Testing Root: {BASE_URL}/")
    try:
        t0 = time.time()
        r_root = requests.get(f"{BASE_URL}/", timeout=15)
        print(f"✅ Root Status: {r_root.status_code} (took {time.time()-t0:.2f}s)")
    except Exception as e:
        print(f"❌ Root Failed: {str(e)}")

    # 2. Test API Auth
    url = f"{API_URL}/auth/token/"
    payload = {
        "phone_number": TEST_PHONE,
        "password": TEST_PASS
    }
    
    print(f"\n🚀 2. Testing API Auth: {url}")
    try:
        t0 = time.time()
        response = requests.post(url, json=payload, timeout=30)
        print(f"✅ API Status: {response.status_code} (took {time.time()-t0:.2f}s)")
        
        if response.status_code == 200:
            print("🌟 Login Successful!")
            # print(f"🔑 Tokens: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"⚠️ Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("🕒 Error: API Connection timed out.")
    except Exception as e:
        print(f"💥 Error: {str(e)}")

if __name__ == "__main__":
    test_connection()
