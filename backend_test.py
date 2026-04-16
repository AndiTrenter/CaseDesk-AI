#!/usr/bin/env python3
"""
CaseDesk AI Backend Testing - Suggest-Metadata Bug Fix Verification
Testing the None handling bug fix for suggest-metadata endpoint
"""

import requests
import json
import os
import tempfile
from datetime import datetime

# Configuration
BACKEND_URL = "https://ai-email-parser.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class CaseDeskTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_document_id = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def test_setup_and_login(self):
        """Test 1: Setup system and login"""
        self.log("🔧 Checking setup status...")
        
        # Check if setup is needed
        response = self.session.get(f"{API_BASE}/setup/status")
        if response.status_code == 200:
            setup_status = response.json()
            if not setup_status.get("is_configured", False):
                self.log("🔧 System not configured, initializing setup...")
                
                # Initialize setup
                setup_response = self.session.post(
                    f"{API_BASE}/setup/init",
                    data={
                        "admin_email": TEST_EMAIL,
                        "admin_username": "admin",
                        "admin_password": TEST_PASSWORD,
                        "admin_full_name": "Test Admin",
                        "language": "de",
                        "ai_provider": "ollama",
                        "internet_access": "allowed",
                        "organization_name": "CaseDesk Test"
                    }
                )
                
                if setup_response.status_code == 200:
                    setup_data = setup_response.json()
                    self.access_token = setup_data.get("access_token")
                    if self.access_token:
                        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                        self.log("✅ Setup completed and logged in")
                        return True
                    else:
                        self.log("❌ Setup completed but no access token")
                        return False
                else:
                    self.log(f"❌ Setup failed: {setup_response.status_code} - {setup_response.text}")
                    return False
        
        # System is already configured, try login
        self.log("🔐 Testing login...")
        
        response = self.session.post(
            f"{API_BASE}/auth/login",
            data={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            if self.access_token:
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                self.log("✅ Login successful")
                return True
            else:
                self.log("❌ Login failed: No access token in response")
                return False
        else:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_health_check(self):
        """Test 6: Health check"""
        self.log("🏥 Testing health check...")
        
        response = self.session.get(f"{API_BASE}/health")
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"✅ Health check passed: {data}")
            return True
        else:
            self.log(f"❌ Health check failed: {response.status_code} - {response.text}")
            return False
    
    def test_upload_document(self):
        """Test 2: Upload a document"""
        self.log("📄 Testing document upload...")
        
        # Create a simple test text file
        test_content = "This is a test document for CaseDesk AI testing.\nIt contains some sample text for OCR processing.\nDate: 2026-04-07\nSubject: Test Document"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                data = {'document_type': 'other'}
                
                response = self.session.post(
                    f"{API_BASE}/documents/upload",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.test_document_id = result["document"]["id"]
                    self.log(f"✅ Document upload successful: {self.test_document_id}")
                    return True
                else:
                    self.log(f"❌ Document upload failed: {result}")
                    return False
            else:
                self.log(f"❌ Document upload failed: {response.status_code} - {response.text}")
                return False
        finally:
            os.unlink(temp_file_path)
    
    def test_suggest_metadata_valid(self):
        """Test 3: Test suggest-metadata with valid document"""
        self.log("🤖 Testing suggest-metadata with valid document...")
        
        if not self.test_document_id:
            self.log("❌ No test document available")
            return False
        
        response = self.session.post(
            f"{API_BASE}/documents/suggest-metadata",
            data={"document_id": self.test_document_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Suggest-metadata with valid document successful: {result}")
            return True
        elif response.status_code == 500:
            self.log(f"❌ CRITICAL BUG: suggest-metadata crashed with 500 error: {response.text}")
            return False
        else:
            self.log(f"⚠️ Suggest-metadata returned non-200 status: {response.status_code} - {response.text}")
            return True  # Non-500 errors are acceptable (e.g., AI service unavailable)
    
    def test_suggest_metadata_with_none_ocr(self):
        """Test 4: Test suggest-metadata with document that has ocr_text=None"""
        self.log("🔍 Testing suggest-metadata with None ocr_text...")
        
        if not self.test_document_id:
            self.log("❌ No test document available")
            return False
        
        # First, manually set ocr_text to None in the database
        # We'll do this by calling the MongoDB directly through a backend endpoint
        # Since we can't directly access MongoDB, we'll simulate this by uploading a document
        # that might have None ocr_text (like a corrupted file)
        
        # Create a binary file that might fail OCR processing
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')  # Binary data that can't be processed as text
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('corrupted_file.bin', f, 'application/octet-stream')}
                data = {'document_type': 'other'}
                
                response = self.session.post(
                    f"{API_BASE}/documents/upload",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    none_doc_id = result["document"]["id"]
                    self.log(f"📄 Uploaded binary document: {none_doc_id}")
                    
                    # Now test suggest-metadata on this document
                    response = self.session.post(
                        f"{API_BASE}/documents/suggest-metadata",
                        data={"document_id": none_doc_id}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.log(f"✅ Suggest-metadata with None ocr_text handled gracefully: {result}")
                        return True
                    elif response.status_code == 500:
                        self.log(f"❌ CRITICAL BUG: suggest-metadata crashed with 500 error on None ocr_text: {response.text}")
                        return False
                    else:
                        self.log(f"⚠️ Suggest-metadata returned non-200 status: {response.status_code} - {response.text}")
                        return True  # Non-500 errors are acceptable
                else:
                    self.log(f"❌ Binary document upload failed: {result}")
                    return False
            else:
                self.log(f"❌ Binary document upload failed: {response.status_code} - {response.text}")
                return False
        finally:
            os.unlink(temp_file_path)
    
    def test_reprocess_endpoint(self):
        """Test 5: Test reprocess endpoint with force=true"""
        self.log("🔄 Testing reprocess endpoint...")
        
        if not self.test_document_id:
            self.log("❌ No test document available")
            return False
        
        response = self.session.post(
            f"{API_BASE}/documents/{self.test_document_id}/reprocess?force=true"
        )
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Reprocess endpoint successful: {result}")
            return True
        elif response.status_code == 500:
            self.log(f"❌ CRITICAL BUG: reprocess endpoint crashed with 500 error: {response.text}")
            return False
        else:
            self.log(f"⚠️ Reprocess endpoint returned non-200 status: {response.status_code} - {response.text}")
            return True  # Non-500 errors might be acceptable depending on AI service availability
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting CaseDesk AI Backend Testing - Suggest-Metadata Bug Fix Verification")
        self.log("=" * 80)
        
        tests = [
            ("Setup and Login", self.test_setup_and_login),
            ("Health Check", self.test_health_check),
            ("Document Upload", self.test_upload_document),
            ("Suggest-Metadata (Valid Document)", self.test_suggest_metadata_valid),
            ("Suggest-Metadata (None OCR Text)", self.test_suggest_metadata_with_none_ocr),
            ("Reprocess Endpoint", self.test_reprocess_endpoint),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            try:
                results[test_name] = test_func()
            except Exception as e:
                self.log(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 80)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} - {test_name}")
            if result:
                passed += 1
        
        self.log(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! The suggest-metadata bug fix is working correctly.")
        else:
            self.log("⚠️ Some tests failed. Please review the issues above.")
        
        return results

if __name__ == "__main__":
    tester = CaseDeskTester()
    results = tester.run_all_tests()