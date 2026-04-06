#!/usr/bin/env python3
"""
CaseDesk AI v1.0.8 Backend Testing Script
Tests the specific endpoints requested in the review.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "https://task-portal-fix.preview.emergentagent.com/api"
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def test_login(self):
        """Test 1: Login and get auth token"""
        print("=== Test 1: Login and Authentication ===")
        
        try:
            # Test login with form data (as per existing working tests)
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
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
                    self.log_test("Login Authentication", True, 
                                f"Token received, user: {data.get('user', {}).get('email', 'unknown')}")
                    return True
                else:
                    self.log_test("Login Authentication", False, 
                                f"No access_token in response: {data}")
                    return False
            else:
                self.log_test("Login Authentication", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Login Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_suggest_for_case_endpoint(self):
        """Test 2: NEW endpoint - GET /api/documents/suggest-for-case/{case_id}"""
        print("=== Test 2: Documents Suggest for Case Endpoint ===")
        
        if not self.auth_token:
            self.log_test("Suggest Documents - Auth Check", False, "No auth token available")
            return False
        
        # First, create a test case
        try:
            case_data = {
                "title": "Mietrechtsstreit",
                "description": "Probleme mit dem Vermieter",
                "reference_number": "TEST-2026-001"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/cases",
                json=case_data
            )
            
            if response.status_code == 200:
                case = response.json()
                case_id = case["id"]
                self.log_test("Create Test Case", True, f"Case created with ID: {case_id}")
                
                # Now test the suggest endpoint
                response = self.session.get(f"{BACKEND_URL}/documents/suggest-for-case/{case_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ["suggestions", "total_available", "ai_powered"]
                    
                    if all(field in data for field in expected_fields):
                        self.log_test("Suggest Documents Endpoint", True, 
                                    f"Response structure correct: suggestions={len(data['suggestions'])}, "
                                    f"total_available={data['total_available']}, ai_powered={data['ai_powered']}")
                        
                        # Clean up: delete test case
                        self.session.delete(f"{BACKEND_URL}/cases/{case_id}")
                        return True
                    else:
                        missing = [f for f in expected_fields if f not in data]
                        self.log_test("Suggest Documents Endpoint", False, 
                                    f"Missing fields: {missing}. Response: {data}")
                        return False
                else:
                    self.log_test("Suggest Documents Endpoint", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    return False
            else:
                self.log_test("Create Test Case", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Suggest Documents Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_tasks_api(self):
        """Test 3: Tasks API - GET and POST /api/tasks"""
        print("=== Test 3: Tasks API ===")
        
        if not self.auth_token:
            self.log_test("Tasks API - Auth Check", False, "No auth token available")
            return False
        
        try:
            # Test GET /api/tasks
            response = self.session.get(f"{BACKEND_URL}/tasks")
            
            if response.status_code == 200:
                tasks = response.json()
                self.log_test("GET /api/tasks", True, 
                            f"Retrieved {len(tasks)} tasks")
                
                # Test POST /api/tasks
                task_data = {
                    "title": "Testaufgabe",
                    "description": "Test task created by backend testing",
                    "priority": "medium",
                    "status": "todo"
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/tasks",
                    json=task_data
                )
                
                if response.status_code == 200:
                    created_task = response.json()
                    task_id = created_task.get("id")
                    
                    if task_id and created_task.get("title") == "Testaufgabe":
                        self.log_test("POST /api/tasks", True, 
                                    f"Task created with ID: {task_id}")
                        
                        # Verify task appears in GET request
                        response = self.session.get(f"{BACKEND_URL}/tasks")
                        if response.status_code == 200:
                            updated_tasks = response.json()
                            task_found = any(t.get("id") == task_id for t in updated_tasks)
                            
                            if task_found:
                                self.log_test("Verify Task Creation", True, 
                                            f"Created task found in task list")
                                
                                # Clean up: delete test task
                                self.session.delete(f"{BACKEND_URL}/tasks/{task_id}")
                                return True
                            else:
                                self.log_test("Verify Task Creation", False, 
                                            "Created task not found in task list")
                                return False
                        else:
                            self.log_test("Verify Task Creation", False, 
                                        f"Failed to retrieve tasks: HTTP {response.status_code}")
                            return False
                    else:
                        self.log_test("POST /api/tasks", False, 
                                    f"Invalid task response: {created_task}")
                        return False
                else:
                    self.log_test("POST /api/tasks", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    return False
            else:
                self.log_test("GET /api/tasks", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Tasks API", False, f"Exception: {str(e)}")
            return False
    
    def test_events_api(self):
        """Test 4: Events API - GET and POST /api/events"""
        print("=== Test 4: Events API ===")
        
        if not self.auth_token:
            self.log_test("Events API - Auth Check", False, "No auth token available")
            return False
        
        try:
            # Test GET /api/events
            response = self.session.get(f"{BACKEND_URL}/events")
            
            if response.status_code == 200:
                events = response.json()
                self.log_test("GET /api/events", True, 
                            f"Retrieved {len(events)} events")
                
                # Test POST /api/events
                start_time = datetime.now() + timedelta(days=1)
                end_time = start_time + timedelta(hours=1)
                
                event_data = {
                    "title": "Testtermin",
                    "description": "Test event created by backend testing",
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "all_day": False
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/events",
                    json=event_data
                )
                
                if response.status_code == 200:
                    created_event = response.json()
                    event_id = created_event.get("id")
                    
                    if event_id and created_event.get("title") == "Testtermin":
                        self.log_test("POST /api/events", True, 
                                    f"Event created with ID: {event_id}")
                        
                        # Verify event appears in GET request
                        response = self.session.get(f"{BACKEND_URL}/events")
                        if response.status_code == 200:
                            updated_events = response.json()
                            event_found = any(e.get("id") == event_id for e in updated_events)
                            
                            if event_found:
                                self.log_test("Verify Event Creation", True, 
                                            f"Created event found in event list")
                                
                                # Clean up: delete test event
                                self.session.delete(f"{BACKEND_URL}/events/{event_id}")
                                return True
                            else:
                                self.log_test("Verify Event Creation", False, 
                                            "Created event not found in event list")
                                return False
                        else:
                            self.log_test("Verify Event Creation", False, 
                                        f"Failed to retrieve events: HTTP {response.status_code}")
                            return False
                    else:
                        self.log_test("POST /api/events", False, 
                                    f"Invalid event response: {created_event}")
                        return False
                else:
                    self.log_test("POST /api/events", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    return False
            else:
                self.log_test("GET /api/events", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Events API", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting CaseDesk AI v1.0.8 Backend Testing")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {TEST_EMAIL}")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            self.test_login,
            self.test_suggest_for_case_endpoint,
            self.test_tasks_api,
            self.test_events_api
        ]
        
        for test in tests:
            test()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"] and not result["success"]:
                print(f"   Error: {result['details']}")
        
        print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed!")
            return False

def main():
    """Main function"""
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()