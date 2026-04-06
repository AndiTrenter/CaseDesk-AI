#!/usr/bin/env python3
"""
CaseDesk AI v1.0.9 Backend Testing
Testing NEW features as requested in review
"""
import requests
import json
import time
import os
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://task-portal-fix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_case_id = None
        self.test_document_id = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def test_login(self):
        """Test 1: Login and get auth token"""
        self.log("🔐 Testing login...")
        
        # Use form data for login as per backend implementation
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(f"{API_BASE}/auth/login", data=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            
            # Set auth header for future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
            
            self.log(f"✅ Login successful! User ID: {self.user_id}")
            return True
        else:
            self.log(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_document_download_token_system(self):
        """Test 2: Document Download Token System"""
        self.log("📄 Testing Document Download Token System...")
        
        # First, create a test document if none exists
        test_doc_created = False
        
        # Check if we have any documents
        response = self.session.get(f"{API_BASE}/documents")
        if response.status_code == 200:
            documents = response.json()
            if documents:
                self.test_document_id = documents[0]["id"]
                self.log(f"📄 Using existing document: {self.test_document_id}")
            else:
                # Create a test document
                self.log("📄 No documents found, creating test document...")
                test_content = b"Test document content for token testing"
                files = {
                    'file': ('test_document.txt', test_content, 'text/plain')
                }
                data = {
                    'document_type': 'other'
                }
                
                response = self.session.post(f"{API_BASE}/documents/upload", files=files, data=data)
                if response.status_code == 200:
                    doc_data = response.json()
                    self.test_document_id = doc_data["document"]["id"]
                    test_doc_created = True
                    self.log(f"✅ Test document created: {self.test_document_id}")
                else:
                    self.log(f"❌ Failed to create test document: {response.status_code} - {response.text}")
                    return False
        else:
            self.log(f"❌ Failed to list documents: {response.status_code} - {response.text}")
            return False
        
        # Test download token generation
        self.log("🔑 Testing download token generation...")
        response = self.session.get(f"{API_BASE}/documents/{self.test_document_id}/download-token")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("token")
            expires_in = token_data.get("expires_in")
            
            if token and expires_in == 300:
                self.log(f"✅ Download token generated successfully (expires in {expires_in}s)")
                
                # Test document view with token
                self.log("👁️ Testing document view with token...")
                view_response = requests.get(f"{API_BASE}/documents/{self.test_document_id}/view?token={token}")
                
                if view_response.status_code == 200:
                    self.log("✅ Document view with token successful!")
                    
                    # Clean up test document if we created it
                    if test_doc_created:
                        self.session.delete(f"{API_BASE}/documents/{self.test_document_id}")
                        self.log("🧹 Test document cleaned up")
                    
                    return True
                else:
                    self.log(f"❌ Document view with token failed: {view_response.status_code}")
                    return False
            else:
                self.log(f"❌ Invalid token response: {token_data}")
                return False
        else:
            self.log(f"❌ Download token generation failed: {response.status_code} - {response.text}")
            return False
    
    def test_zip_download_endpoint(self):
        """Test 3: NEW ZIP Download Endpoint for cases"""
        self.log("📦 Testing NEW ZIP Download Endpoint...")
        
        # First create a test case
        self.log("📁 Creating test case...")
        case_data = {
            "title": "Test Case for ZIP Download",
            "description": "Test case to verify ZIP download functionality",
            "reference_number": "TEST-ZIP-001"
        }
        
        response = self.session.post(f"{API_BASE}/cases", json=case_data)
        if response.status_code == 200:
            case = response.json()
            self.test_case_id = case["id"]
            self.log(f"✅ Test case created: {self.test_case_id}")
        else:
            self.log(f"❌ Failed to create test case: {response.status_code} - {response.text}")
            return False
        
        # Create and assign a test document to the case
        self.log("📄 Creating and assigning test document to case...")
        test_content = b"Test document content for ZIP download testing"
        files = {
            'file': ('zip_test_document.txt', test_content, 'text/plain')
        }
        data = {
            'case_id': self.test_case_id,
            'document_type': 'other'
        }
        
        response = self.session.post(f"{API_BASE}/documents/upload", files=files, data=data)
        if response.status_code == 200:
            doc_data = response.json()
            test_doc_id = doc_data["document"]["id"]
            self.log(f"✅ Test document assigned to case: {test_doc_id}")
        else:
            self.log(f"❌ Failed to create/assign document: {response.status_code} - {response.text}")
            return False
        
        # Test ZIP download endpoint
        self.log("📦 Testing ZIP download endpoint...")
        response = self.session.get(f"{API_BASE}/cases/{self.test_case_id}/documents-zip")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_disposition = response.headers.get('content-disposition', '')
            
            if content_type == 'application/zip':
                self.log("✅ ZIP download successful! Content-Type: application/zip")
                self.log(f"📦 Content-Disposition: {content_disposition}")
                
                # Verify ZIP content size
                zip_size = len(response.content)
                self.log(f"📦 ZIP file size: {zip_size} bytes")
                
                # Clean up
                self.session.delete(f"{API_BASE}/documents/{test_doc_id}")
                self.session.delete(f"{API_BASE}/cases/{self.test_case_id}")
                self.log("🧹 Test case and document cleaned up")
                
                return True
            else:
                self.log(f"❌ Wrong content type: {content_type} (expected: application/zip)")
                return False
        else:
            self.log(f"❌ ZIP download failed: {response.status_code} - {response.text}")
            return False
    
    def test_tasks_api(self):
        """Test 4: Tasks API (verify "Failed to load tasks" issue)"""
        self.log("📋 Testing Tasks API...")
        
        # Test GET /api/tasks - must return 200 with array
        self.log("📋 Testing GET /api/tasks...")
        response = self.session.get(f"{API_BASE}/tasks")
        
        if response.status_code == 200:
            tasks = response.json()
            if isinstance(tasks, list):
                self.log(f"✅ GET /api/tasks successful! Returned {len(tasks)} tasks")
                
                # Test POST /api/tasks - create a task
                self.log("📋 Testing POST /api/tasks...")
                task_data = {
                    "title": "Test Task for API Verification",
                    "description": "Testing task creation to verify API functionality",
                    "priority": "medium",
                    "status": "todo"
                }
                
                response = self.session.post(f"{API_BASE}/tasks", json=task_data)
                if response.status_code == 200:
                    created_task = response.json()
                    task_id = created_task.get("id")
                    self.log(f"✅ Task created successfully: {task_id}")
                    
                    # Test GET /api/tasks again to verify the created task appears
                    self.log("📋 Verifying task appears in GET /api/tasks...")
                    response = self.session.get(f"{API_BASE}/tasks")
                    if response.status_code == 200:
                        tasks = response.json()
                        task_found = any(task.get("id") == task_id for task in tasks)
                        if task_found:
                            self.log("✅ Created task found in task list!")
                            
                            # Clean up
                            self.session.delete(f"{API_BASE}/tasks/{task_id}")
                            self.log("🧹 Test task cleaned up")
                            return True
                        else:
                            self.log("❌ Created task not found in task list")
                            return False
                    else:
                        self.log(f"❌ Failed to verify task list: {response.status_code}")
                        return False
                else:
                    self.log(f"❌ Task creation failed: {response.status_code} - {response.text}")
                    return False
            else:
                self.log(f"❌ GET /api/tasks returned non-array: {type(tasks)}")
                return False
        else:
            self.log(f"❌ GET /api/tasks failed: {response.status_code} - {response.text}")
            return False
    
    def test_events_api(self):
        """Test 5: Events API"""
        self.log("📅 Testing Events API...")
        
        # Test GET /api/events - must return 200
        self.log("📅 Testing GET /api/events...")
        response = self.session.get(f"{API_BASE}/events")
        
        if response.status_code == 200:
            events = response.json()
            if isinstance(events, list):
                self.log(f"✅ GET /api/events successful! Returned {len(events)} events")
                
                # Test POST /api/events - create an event
                self.log("📅 Testing POST /api/events...")
                event_data = {
                    "title": "Test Event for API Verification",
                    "description": "Testing event creation to verify API functionality",
                    "start_time": "2024-12-31T10:00:00",
                    "end_time": "2024-12-31T11:00:00",
                    "all_day": False
                }
                
                response = self.session.post(f"{API_BASE}/events", json=event_data)
                if response.status_code == 200:
                    created_event = response.json()
                    event_id = created_event.get("id")
                    self.log(f"✅ Event created successfully: {event_id}")
                    
                    # Test GET /api/events again to verify the created event appears
                    self.log("📅 Verifying event appears in GET /api/events...")
                    response = self.session.get(f"{API_BASE}/events")
                    if response.status_code == 200:
                        events = response.json()
                        event_found = any(event.get("id") == event_id for event in events)
                        if event_found:
                            self.log("✅ Created event found in event list!")
                            
                            # Clean up
                            self.session.delete(f"{API_BASE}/events/{event_id}")
                            self.log("🧹 Test event cleaned up")
                            return True
                        else:
                            self.log("❌ Created event not found in event list")
                            return False
                    else:
                        self.log(f"❌ Failed to verify event list: {response.status_code}")
                        return False
                else:
                    self.log(f"❌ Event creation failed: {response.status_code} - {response.text}")
                    return False
            else:
                self.log(f"❌ GET /api/events returned non-array: {type(events)}")
                return False
        else:
            self.log(f"❌ GET /api/events failed: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("🚀 Starting CaseDesk AI v1.0.9 Backend Testing...")
        self.log(f"🌐 Backend URL: {BACKEND_URL}")
        self.log(f"👤 Test User: {TEST_EMAIL}")
        
        results = {}
        
        # Test 1: Login
        results["login"] = self.test_login()
        if not results["login"]:
            self.log("❌ Login failed - cannot continue with other tests")
            return results
        
        # Test 2: Document Download Token System
        results["document_download_token"] = self.test_document_download_token_system()
        
        # Test 3: ZIP Download Endpoint
        results["zip_download"] = self.test_zip_download_endpoint()
        
        # Test 4: Tasks API
        results["tasks_api"] = self.test_tasks_api()
        
        # Test 5: Events API
        results["events_api"] = self.test_events_api()
        
        # Summary
        self.log("\n" + "="*60)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        self.log(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! CaseDesk AI v1.0.9 backend is working correctly.")
        else:
            self.log("⚠️ Some tests failed. Please check the issues above.")
        
        return results

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()