#!/usr/bin/env python3
"""
CaseDesk AI v1.1.2 Backend Testing - Task Status Fix
Testing the validation error fix for legacy task statuses
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://task-portal-fix.preview.emergentagent.com/api"
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class TaskStatusTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.created_task_ids = []
        
    def login(self):
        """Login and get auth token"""
        print("🔐 Testing login...")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(
            f"{BACKEND_URL}/auth/login",
            data=login_data,  # Using form data as per previous tests
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print(f"✅ Login successful - Token: {self.auth_token[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_create_task_with_legacy_open_status(self):
        """Test creating task with legacy 'open' status - should NOT throw validation error"""
        print("\n📝 Testing task creation with legacy 'open' status...")
        
        task_data = {
            "title": "Test mit open status",
            "status": "open",
            "description": "Testing legacy open status",
            "priority": "medium"
        }
        
        response = self.session.post(
            f"{BACKEND_URL}/tasks",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            task = response.json()
            self.created_task_ids.append(task["id"])
            print(f"✅ Task created with 'open' status successfully")
            print(f"   Task ID: {task['id']}")
            print(f"   Status in response: {task.get('status')}")
            return True, task
        else:
            print(f"❌ Failed to create task with 'open' status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
    
    def test_create_task_with_pending_status(self):
        """Test creating task with 'pending' status - should NOT throw validation error"""
        print("\n📝 Testing task creation with 'pending' status...")
        
        task_data = {
            "title": "Test mit pending status",
            "status": "pending",
            "description": "Testing pending status",
            "priority": "high"
        }
        
        response = self.session.post(
            f"{BACKEND_URL}/tasks",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            task = response.json()
            self.created_task_ids.append(task["id"])
            print(f"✅ Task created with 'pending' status successfully")
            print(f"   Task ID: {task['id']}")
            print(f"   Status in response: {task.get('status')}")
            return True, task
        else:
            print(f"❌ Failed to create task with 'pending' status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
    
    def test_create_task_with_todo_status(self):
        """Test creating task with normal 'todo' status"""
        print("\n📝 Testing task creation with normal 'todo' status...")
        
        task_data = {
            "title": "Normale Aufgabe",
            "status": "todo",
            "description": "Testing normal todo status",
            "priority": "low"
        }
        
        response = self.session.post(
            f"{BACKEND_URL}/tasks",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            task = response.json()
            self.created_task_ids.append(task["id"])
            print(f"✅ Task created with 'todo' status successfully")
            print(f"   Task ID: {task['id']}")
            print(f"   Status in response: {task.get('status')}")
            return True, task
        else:
            print(f"❌ Failed to create task with 'todo' status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
    
    def test_get_tasks_status_normalization(self):
        """Test GET /api/tasks - should return tasks without validation errors and normalize 'open' to 'todo'"""
        print("\n📋 Testing GET /api/tasks with status normalization...")
        
        response = self.session.get(f"{BACKEND_URL}/tasks")
        
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ GET /api/tasks successful - Retrieved {len(tasks)} tasks")
            
            # Check for status normalization
            open_tasks_normalized = []
            pending_tasks_normalized = []
            
            for task in tasks:
                print(f"   Task: {task.get('title')} - Status: {task.get('status')}")
                
                if "open status" in task.get('title', ''):
                    open_tasks_normalized.append(task)
                elif "pending status" in task.get('title', ''):
                    pending_tasks_normalized.append(task)
            
            # Verify normalization
            normalization_success = True
            for task in open_tasks_normalized:
                if task.get('status') != 'todo':
                    print(f"❌ Status normalization failed: 'open' task has status '{task.get('status')}', expected 'todo'")
                    normalization_success = False
                else:
                    print(f"✅ Status normalization working: 'open' task normalized to 'todo'")
            
            for task in pending_tasks_normalized:
                if task.get('status') != 'todo':
                    print(f"❌ Status normalization failed: 'pending' task has status '{task.get('status')}', expected 'todo'")
                    normalization_success = False
                else:
                    print(f"✅ Status normalization working: 'pending' task normalized to 'todo'")
            
            return True, normalization_success
        else:
            print(f"❌ GET /api/tasks failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, False
    
    def cleanup_test_tasks(self):
        """Clean up created test tasks"""
        print("\n🧹 Cleaning up test tasks...")
        
        for task_id in self.created_task_ids:
            response = self.session.delete(f"{BACKEND_URL}/tasks/{task_id}")
            if response.status_code == 200:
                print(f"✅ Deleted task {task_id}")
            else:
                print(f"⚠️ Failed to delete task {task_id}: {response.status_code}")
    
    def run_all_tests(self):
        """Run all task status fix tests"""
        print("🚀 Starting CaseDesk AI v1.1.2 Task Status Fix Testing")
        print("=" * 60)
        
        # Test results tracking
        test_results = {
            "login": False,
            "create_open_task": False,
            "create_pending_task": False,
            "create_todo_task": False,
            "get_tasks": False,
            "status_normalization": False
        }
        
        # 1. Login
        if not self.login():
            print("\n❌ CRITICAL: Login failed - cannot proceed with tests")
            return test_results
        test_results["login"] = True
        
        # 2. Test creating task with legacy 'open' status
        success, _ = self.test_create_task_with_legacy_open_status()
        test_results["create_open_task"] = success
        
        # 3. Test creating task with 'pending' status
        success, _ = self.test_create_task_with_pending_status()
        test_results["create_pending_task"] = success
        
        # 4. Test creating task with normal 'todo' status
        success, _ = self.test_create_task_with_todo_status()
        test_results["create_todo_task"] = success
        
        # 5. Test GET /api/tasks with status normalization
        get_success, norm_success = self.test_get_tasks_status_normalization()
        test_results["get_tasks"] = get_success
        test_results["status_normalization"] = norm_success
        
        # Cleanup
        self.cleanup_test_tasks()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TASK STATUS FIX TEST RESULTS")
        print("=" * 60)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if test_results["create_open_task"] and test_results["create_pending_task"] and test_results["status_normalization"]:
            print("\n🎉 TASK STATUS FIX VERIFICATION: SUCCESS")
            print("✅ Legacy 'open' status accepted without validation error")
            print("✅ 'pending' status accepted without validation error") 
            print("✅ Status normalization working correctly")
        else:
            print("\n⚠️ TASK STATUS FIX VERIFICATION: ISSUES FOUND")
            if not test_results["create_open_task"]:
                print("❌ Legacy 'open' status still causing validation errors")
            if not test_results["create_pending_task"]:
                print("❌ 'pending' status causing validation errors")
            if not test_results["status_normalization"]:
                print("❌ Status normalization not working correctly")
        
        return test_results

def main():
    """Main test execution"""
    tester = TaskStatusTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()