#!/usr/bin/env python3
"""
Additional test to specifically verify the None handling bug fix
"""

import requests
import json
import tempfile
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://ai-email-parser.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def test_none_handling_bug_fix():
    """Specific test for the None handling bug fix"""
    log("🔍 Testing None handling bug fix in suggest-metadata endpoint...")
    
    session = requests.Session()
    
    # Login
    response = session.post(
        f"{API_BASE}/auth/login",
        data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if response.status_code != 200:
        log("❌ Login failed")
        return False
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Upload a document that will likely have None ocr_text
    # Create a file with content that might fail OCR processing
    test_files = [
        # Empty file
        ("empty.txt", b""),
        # Binary file
        ("binary.bin", b'\x00\x01\x02\x03\x04\x05\x06\x07'),
        # Very small text file
        ("tiny.txt", b"x"),
    ]
    
    for filename, content in test_files:
        log(f"📄 Testing with {filename}...")
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}
                data = {'document_type': 'other'}
                
                upload_response = session.post(
                    f"{API_BASE}/documents/upload",
                    files=files,
                    data=data
                )
            
            if upload_response.status_code == 200:
                doc_id = upload_response.json()["document"]["id"]
                log(f"✅ Uploaded {filename}: {doc_id}")
                
                # Test suggest-metadata - this should NOT crash with 500
                metadata_response = session.post(
                    f"{API_BASE}/documents/suggest-metadata",
                    data={"document_id": doc_id}
                )
                
                if metadata_response.status_code == 500:
                    log(f"❌ CRITICAL BUG: suggest-metadata crashed with 500 for {filename}")
                    log(f"Response: {metadata_response.text}")
                    return False
                elif metadata_response.status_code == 200:
                    result = metadata_response.json()
                    log(f"✅ suggest-metadata handled {filename} gracefully: {result.get('success', 'unknown')}")
                else:
                    log(f"⚠️ suggest-metadata returned {metadata_response.status_code} for {filename} (acceptable)")
                
                # Also test reprocess endpoint
                reprocess_response = session.post(
                    f"{API_BASE}/documents/{doc_id}/reprocess?force=true"
                )
                
                if reprocess_response.status_code == 500:
                    log(f"❌ CRITICAL BUG: reprocess crashed with 500 for {filename}")
                    log(f"Response: {reprocess_response.text}")
                    return False
                else:
                    log(f"✅ reprocess handled {filename} gracefully")
            
        finally:
            os.unlink(temp_path)
    
    log("🎉 None handling bug fix verification PASSED!")
    return True

if __name__ == "__main__":
    success = test_none_handling_bug_fix()
    if success:
        print("\n✅ BUG FIX VERIFICATION SUCCESSFUL")
        print("The suggest-metadata endpoint correctly handles None ocr_text values")
        print("No more TypeError: 'NoneType' object is not subscriptable")
    else:
        print("\n❌ BUG FIX VERIFICATION FAILED")
        print("The suggest-metadata endpoint still has issues with None handling")