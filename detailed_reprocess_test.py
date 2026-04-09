#!/usr/bin/env python3
"""
Detailed investigation of document reprocess issue
"""

import requests
import json
import tempfile
import os

# Backend URL
BACKEND_URL = "https://ai-calendar-debug.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

def test_document_reprocess_detailed():
    session = requests.Session()
    
    # Login first
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = session.post(
        f"{API_BASE}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    data = response.json()
    auth_token = data["access_token"]
    session.headers.update({"Authorization": f"Bearer {auth_token}"})
    
    print("✅ Login successful")
    
    # Create a test document with more content
    test_content = """This is a comprehensive test document for CaseDesk AI v1.1.3 testing.
    
Document upload and reprocessing functionality verification.

This document contains multiple lines of text to ensure proper text extraction.
It includes various types of content that should be processed by the OCR system.

Test data:
- Date: 2024-04-07
- Subject: Document reprocessing test
- Content: Multiple paragraphs with meaningful text
- Purpose: Verify that the reprocess endpoint works correctly with force=true

The document should be processed successfully and text should be extracted properly."""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        # Upload the document
        with open(temp_file_path, 'rb') as f:
            files = {
                'file': ('detailed_test_document.txt', f, 'text/plain')
            }
            data = {
                'document_type': 'other'
            }
            
            response = session.post(
                f"{API_BASE}/documents/upload",
                files=files,
                data=data
            )
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return
        
        result_data = response.json()
        if not result_data.get("success"):
            print(f"❌ Upload returned success=false: {result_data}")
            return
        
        document_id = result_data.get("document", {}).get("id")
        print(f"✅ Document uploaded successfully: {document_id}")
        
        # Get document details before reprocess
        response = session.get(f"{API_BASE}/documents/{document_id}")
        if response.status_code == 200:
            doc_data = response.json()
            print(f"📄 Document before reprocess:")
            print(f"   - OCR processed: {doc_data.get('ocr_processed', False)}")
            print(f"   - OCR text length: {len(doc_data.get('ocr_text', '') or '')}")
            print(f"   - AI analyzed: {doc_data.get('ai_analyzed', False)}")
        
        # Test reprocess without force first
        print("\n🔄 Testing reprocess without force...")
        response = session.post(f"{API_BASE}/documents/{document_id}/reprocess")
        
        if response.status_code == 200:
            reprocess_data = response.json()
            print(f"✅ Reprocess without force: {reprocess_data}")
        else:
            print(f"❌ Reprocess without force failed: {response.status_code} - {response.text}")
        
        # Test reprocess with force=true
        print("\n🔄 Testing reprocess with force=true...")
        response = session.post(f"{API_BASE}/documents/{document_id}/reprocess?force=true")
        
        if response.status_code == 200:
            reprocess_data = response.json()
            print(f"✅ Reprocess with force: {reprocess_data}")
            
            if reprocess_data.get("success"):
                print("✅ Reprocess successful!")
            else:
                print(f"❌ Reprocess failed: {reprocess_data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Reprocess with force failed: {response.status_code} - {response.text}")
        
        # Get document details after reprocess
        response = session.get(f"{API_BASE}/documents/{document_id}")
        if response.status_code == 200:
            doc_data = response.json()
            print(f"\n📄 Document after reprocess:")
            print(f"   - OCR processed: {doc_data.get('ocr_processed', False)}")
            print(f"   - OCR text length: {len(doc_data.get('ocr_text', '') or '')}")
            print(f"   - AI analyzed: {doc_data.get('ai_analyzed', False)}")
            if doc_data.get('ocr_text'):
                print(f"   - OCR text preview: {doc_data.get('ocr_text', '')[:100]}...")
        
        # Cleanup
        response = session.delete(f"{API_BASE}/documents/{document_id}")
        if response.status_code == 200:
            print(f"\n✅ Cleaned up test document {document_id}")
        
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == "__main__":
    test_document_reprocess_detailed()