#!/usr/bin/env python3
"""
CaseDesk AI Backend Testing - Tasks API Focus
Testing the Tasks API endpoints as requested in the review.
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://task-portal-fix.preview.emergentagent.com/api"
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class TasksAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
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
        print("=== Testing Login ===")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                data={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.user_id = data.get("user", {}).get("id")
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    self.log_test("Login", True, f"Token received, User ID: {self.user_id}")
                    return True
                else:
                    self.log_test("Login", False, "No access_token in response")
                    return False
            else:
                self.log_test("Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Login", False, f"Exception: {str(e)}")
            return False
    
    def test_get_tasks_empty(self):
        """Test 2: GET /api/tasks - should return empty array initially"""
        print("=== Testing GET /api/tasks (empty) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/tasks")
            
            if response.status_code == 200:
                tasks = response.json()
                if isinstance(tasks, list) and len(tasks) == 0:
                    self.log_test("GET /api/tasks (empty)", True, "Returned empty array as expected")
                    return True
                else:
                    self.log_test("GET /api/tasks (empty)", False, f"Expected empty array, got: {tasks}")
                    return False
            else:
                self.log_test("GET /api/tasks (empty)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET /api/tasks (empty)", False, f"Exception: {str(e)}")
            return False
    
    def test_create_task(self):
        """Test 3: POST /api/tasks - create a new task with title 'Test Aufgabe'"""
        print("=== Testing POST /api/tasks ===")
        
        try:
            task_data = {
                "title": "Test Aufgabe",
                "description": "Eine Testaufgabe erstellt durch automatisierte Tests",
                "priority": "medium",
                "status": "todo"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/tasks",
                json=task_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                created_task = response.json()
                
                # Verify required fields
                required_fields = ["id", "title", "user_id", "created_at"]
                missing_fields = [field for field in required_fields if field not in created_task]
                
                if not missing_fields and created_task["title"] == "Test Aufgabe":
                    self.created_task_id = created_task["id"]
                    self.log_test("POST /api/tasks", True, f"Task created with ID: {self.created_task_id}")
                    return True
                else:
                    self.log_test("POST /api/tasks", False, f"Missing fields: {missing_fields} or wrong title")
                    return False
            else:
                self.log_test("POST /api/tasks", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("POST /api/tasks", False, f"Exception: {str(e)}")
            return False
    
    def test_get_tasks_with_data(self):
        """Test 4: GET /api/tasks again - should now return the created task"""
        print("=== Testing GET /api/tasks (with data) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/tasks")
            
            if response.status_code == 200:
                tasks = response.json()
                
                if isinstance(tasks, list) and len(tasks) > 0:
                    # Find our created task
                    test_task = None
                    for task in tasks:
                        if task.get("title") == "Test Aufgabe":
                            test_task = task
                            break
                    
                    if test_task:
                        self.log_test("GET /api/tasks (with data)", True, f"Found created task: {test_task['id']}")
                        return True
                    else:
                        self.log_test("GET /api/tasks (with data)", False, "Created task not found in list")
                        return False
                else:
                    self.log_test("GET /api/tasks (with data)", False, f"Expected non-empty array, got: {tasks}")
                    return False
            else:
                self.log_test("GET /api/tasks (with data)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET /api/tasks (with data)", False, f"Exception: {str(e)}")
            return False
    
    def test_ai_status(self):
        """Test 5: GET /api/ai/status - test the AI status endpoint"""
        print("=== Testing GET /api/ai/status ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/ai/status")
            
            if response.status_code == 200:
                status = response.json()
                
                # Check for expected fields
                expected_fields = ["ollama", "openai"]
                has_expected_fields = all(field in status for field in expected_fields)
                
                if has_expected_fields:
                    self.log_test("GET /api/ai/status", True, f"AI status: {json.dumps(status, indent=2)}")
                    return True
                else:
                    self.log_test("GET /api/ai/status", False, f"Missing expected fields. Got: {status}")
                    return False
            else:
                self.log_test("GET /api/ai/status", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET /api/ai/status", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up: Delete the test task we created"""
        print("=== Cleanup: Deleting test task ===")
        
        if hasattr(self, 'created_task_id'):
            try:
                response = self.session.delete(f"{BACKEND_URL}/tasks/{self.created_task_id}")
                
                if response.status_code == 200:
                    self.log_test("Cleanup - Delete test task", True, "Test task deleted successfully")
                else:
                    self.log_test("Cleanup - Delete test task", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Cleanup - Delete test task", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting CaseDesk AI Tasks API Testing")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {TEST_EMAIL}")
        print("=" * 60)
        
        # Test sequence as requested
        tests = [
            self.test_login,
            self.test_get_tasks_empty,
            self.test_create_task,
            self.test_get_tasks_with_data,
            self.test_ai_status
        ]
        
        success_count = 0
        for test in tests:
            if test():
                success_count += 1
            else:
                # If login fails, stop testing
                if test == self.test_login:
                    print("❌ Login failed - stopping tests")
                    break
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"] and not result["success"]:
                print(f"   Error: {result['details']}")
        
        return passed_tests == total_tests


def main():
    """Main test execution"""
    tester = TasksAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()