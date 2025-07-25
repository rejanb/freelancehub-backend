# Test API Endpoints
import requests
import json

base_url = "http://127.0.0.1:8000"

def test_endpoints():
    print("Testing API Endpoints...")
    
    # Test basic project list
    try:
        response = requests.get(f"{base_url}/api/projects/projects/")
        print(f"✅ Projects list: {response.status_code}")
    except:
        print("❌ Projects list: Failed")
    
    # Test specific project
    try:
        response = requests.get(f"{base_url}/api/projects/projects/25/")
        print(f"✅ Project detail: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Project: {data.get('title', 'N/A')}")
            print(f"   Attachments: {len(data.get('attachments', []))}")
    except:
        print("❌ Project detail: Failed")
    
    # Test upload endpoint (should be available now)
    print(f"\n📁 Upload endpoint should be available at:")
    print(f"   POST {base_url}/api/projects/projects/25/upload_attachment/")
    
    print(f"\n📥 Download endpoint should be available at:")
    print(f"   GET {base_url}/api/projects/projects/25/download_attachment/{{attachment_id}}/")

if __name__ == "__main__":
    test_endpoints()
