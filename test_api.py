import requests
import sys
import time

def test_api():
    url = "http://127.0.0.1:8000/api/redact"
    file_path = "Red_Herring_Prospectus.docx"
    
    print(f"Testing API endpoint: {url} with file: {file_path}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        data = {'confidence': 0.65, 'reset_cache': 'false'}
        
        response = requests.post(url, files=files, data=data)
        
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        res_json = response.json()
        print("✅ Redaction endpoint success!")
        print(f"Session ID: {res_json.get('session_id')}")
        print(f"Total PII Detected: {res_json['stats'].get('total_pii_detected')}")
        print(f"Unique PII: {res_json['stats'].get('total_unique_pii')}")
        print("Downloads:", res_json.get('downloads'))
        
        # Test download endpoint
        dl_url = f"http://127.0.0.1:8000{res_json['downloads']['redacted']}"
        dl_res = requests.get(dl_url)
        print(f"Redacted File Download test status: {dl_res.status_code}, size: {len(dl_res.content)} bytes")
        
        orig_dl_url = f"http://127.0.0.1:8000{res_json['downloads']['original']}"
        orig_dl_res = requests.get(orig_dl_url)
        print(f"Original Copy File Download test status: {orig_dl_res.status_code}, size: {len(orig_dl_res.content)} bytes")

    else:
        print(f"❌ Failed: {response.text}")

if __name__ == "__main__":
    test_api()
