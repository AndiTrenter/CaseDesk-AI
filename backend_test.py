#!/usr/bin/env python3
"""
CaseDesk AI v1.1.3 Backend Testing
Testing specific v1.1.3 features as requested:
1. Login and get auth token
2. Test document reprocess endpoint with force flag
3. Verify health endpoint shows version 1.1.3
4. Test document upload endpoint
"""

import requests
import json
import os
import tempfile
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://task-portal-fix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class CaseDeskTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_login(self):
        """Test 1: Login and get auth token"""
        try:
            # Test login with form data (as per previous tests)
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    self.log_result(
                        "Login Authentication", 
                        True, 
                        "Successfully logged in and obtained auth token",
                        {"user_id": data.get("user", {}).get("id"), "token_type": data.get("token_type")}
                    )
                    return True
                else:
                    self.log_result("Login Authentication", False, "No access token in response", data)
                    return False
            else:
                self.log_result("Login Authentication", False, f"Login failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Login Authentication", False, f"Login error: {str(e)}")
            return False
    
    def test_health_version(self):
        """Test 2: Verify health endpoint shows version 1.1.3"""
        try:
            # Test the main health endpoint
            response = self.session.get(f"{API_BASE}/health")
            
            if response.status_code == 200:
                data = response.json()
                version = data.get("version")
                
                if version == "1.1.3":
                    self.log_result(
                        "Health Version Check", 
                        True, 
                        f"Health endpoint correctly shows version {version}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "Health Version Check", 
                        False, 
                        f"Expected version 1.1.3, got {version}",
                        data
                    )
                    return False
            else:
                self.log_result("Health Version Check", False, f"Health endpoint failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Health Version Check", False, f"Health check error: {str(e)}")
            return False
    
    def test_system_version(self):
        """Test 2b: Also check system version endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/system/version")
            
            if response.status_code == 200:
                data = response.json()
                version = data.get("version")
                
                if version == "1.1.3":
                    self.log_result(
                        "System Version Check", 
                        True, 
                        f"System endpoint correctly shows version {version}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "System Version Check", 
                        False, 
                        f"Expected version 1.1.3, got {version}",
                        data
                    )
                    return False
            else:
                self.log_result("System Version Check", False, f"System version endpoint failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("System Version Check", False, f"System version error: {str(e)}")
            return False
    
    def test_document_upload(self):
        """Test 3: Test document upload endpoint still works"""
        try:
            # Create a test file
            test_content = "This is a test document for CaseDesk AI v1.1.3 testing.\nDocument upload functionality verification."
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file_path = f.name
            
            try:
                # Upload the document
                with open(temp_file_path, 'rb') as f:
                    files = {
                        'file': ('test_document_v113.txt', f, 'text/plain')
                    }
                    data = {
                        'document_type': 'other'
                    }
                    
                    response = self.session.post(
                        f"{API_BASE}/documents/upload",
                        files=files,
                        data=data
                    )
                
                if response.status_code == 200:
                    result_data = response.json()
                    if result_data.get("success"):
                        document_id = result_data.get("document", {}).get("id")
                        self.log_result(
                            "Document Upload", 
                            True, 
                            "Document upload successful",
                            {"document_id": document_id, "filename": "test_document_v113.txt"}
                        )
                        return document_id
                    else:
                        self.log_result("Document Upload", False, "Upload returned success=false", result_data)
                        return None
                else:
                    self.log_result("Document Upload", False, f"Upload failed with status {response.status_code}", response.text)
                    return None
                    
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            self.log_result("Document Upload", False, f"Upload error: {str(e)}")
            return None
    
    def test_document_reprocess_force(self, document_id):
        """Test 4: Test document reprocess endpoint with force flag"""
        if not document_id:
            self.log_result("Document Reprocess Force", False, "No document ID available for testing")
            return False
            
        try:
            # Test the reprocess endpoint with force=true
            response = self.session.post(
                f"{API_BASE}/documents/{document_id}/reprocess?force=true"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result(
                        "Document Reprocess Force", 
                        True, 
                        "Document reprocess with force=true successful",
                        {"document_id": document_id, "message": data.get("message")}
                    )
                    return True
                else:
                    self.log_result(
                        "Document Reprocess Force", 
                        False, 
                        f"Reprocess returned success=false: {data.get('error', 'Unknown error')}",
                        data
                    )
                    return False
            else:
                self.log_result("Document Reprocess Force", False, f"Reprocess failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Document Reprocess Force", False, f"Reprocess error: {str(e)}")
            return False
    
    def cleanup_test_document(self, document_id):
        """Clean up test document"""
        if not document_id:
            return
            
        try:
            response = self.session.delete(f"{API_BASE}/documents/{document_id}")
            if response.status_code == 200:
                print(f"✅ Cleaned up test document {document_id}")
            else:
                print(f"⚠️  Failed to clean up test document {document_id}")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
    
    def run_all_tests(self):
        """Run all v1.1.3 tests"""
        print("=" * 60)
        print("CaseDesk AI v1.1.3 Backend Testing")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {TEST_EMAIL}")
        print()
        
        # Test 1: Login
        if not self.test_login():
            print("❌ Cannot proceed without authentication")
            return self.get_summary()
        
        # Test 2: Health version check
        self.test_health_version()
        
        # Test 2b: System version check
        self.test_system_version()
        
        # Test 3: Document upload
        document_id = self.test_document_upload()
        
        # Test 4: Document reprocess with force
        self.test_document_reprocess_force(document_id)
        
        # Cleanup
        if document_id:
            self.cleanup_test_document(document_id)
        
        return self.get_summary()
    
    def get_summary(self):
        """Get test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['message']}")
            print()
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = CaseDeskTester()
    summary = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if summary["failed"] > 0:
        exit(1)
    else:
        exit(0)