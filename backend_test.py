#!/usr/bin/env python3
"""
CaseDesk AI v1.5.0 Backend Testing
Tests the calendar loading error fix and AI event creation functionality
"""

import requests
import json
import sys
from datetime import datetime, timezone
import os

# Backend URL from environment
BACKEND_URL = "https://ai-email-parser.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class CaseDeskTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "error": error
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def authenticate(self):
        """Authenticate with test credentials"""
        print("🔐 Authenticating with test credentials...")
        
        try:
            # Login with form data (as per previous tests)
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                data=login_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    self.log_test("Authentication", True, f"Logged in as {TEST_EMAIL}")
                    return True
                else:
                    self.log_test("Authentication", False, error="No access token in response")
                    return False
            else:
                self.log_test("Authentication", False, error=f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, error=str(e))
            return False
    
    def test_health_endpoint_version(self):
        """Test GET /api/health returns version 1.5.0"""
        print("🏥 Testing Health Endpoint Version...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/api/health", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                version = data.get("version")
                service = data.get("service")
                status = data.get("status")
                
                if version == "1.5.0":
                    self.log_test("Health Endpoint Version", True, 
                                f"Version: {version}, Service: {service}, Status: {status}")
                else:
                    self.log_test("Health Endpoint Version", False, 
                                f"Expected version 1.5.0, got {version}")
            else:
                self.log_test("Health Endpoint Version", False, 
                            error=f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Health Endpoint Version", False, error=str(e))
    
    def test_system_version_endpoint(self):
        """Test GET /api/system/version returns version 1.5.0"""
        print("🔧 Testing System Version Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/api/system/version", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                version = data.get("version")
                build_date = data.get("build_date")
                release_notes = data.get("release_notes")
                
                if version == "1.5.0":
                    self.log_test("System Version Endpoint", True, 
                                f"Version: {version}, Build: {build_date}")
                else:
                    self.log_test("System Version Endpoint", False, 
                                f"Expected version 1.5.0, got {version}")
            else:
                self.log_test("System Version Endpoint", False, 
                            error=f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("System Version Endpoint", False, error=str(e))
    
    def test_events_api_calendar_load(self):
        """Test GET /api/events - Calendar Load Fix v1.5.0"""
        print("📅 Testing Events API - Calendar Load Fix...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/api/events", timeout=30)
            
            if response.status_code == 200:
                events = response.json()
                
                # Should return an array (even if empty)
                if isinstance(events, list):
                    # Check if datetime fields are properly serialized as ISO strings
                    datetime_fields_ok = True
                    malformed_events = 0
                    
                    for event in events:
                        for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
                            if field in event and event[field] is not None:
                                # Check if it's a valid ISO string
                                try:
                                    datetime.fromisoformat(event[field].replace('Z', '+00:00'))
                                except (ValueError, AttributeError):
                                    datetime_fields_ok = False
                                    malformed_events += 1
                                    break
                    
                    if datetime_fields_ok:
                        self.log_test("Events API - Calendar Load", True, 
                                    f"Returned {len(events)} events, all datetime fields properly serialized")
                    else:
                        self.log_test("Events API - Calendar Load", False, 
                                    f"Found {malformed_events} events with malformed datetime fields")
                else:
                    self.log_test("Events API - Calendar Load", False, 
                                error="Response is not an array")
            else:
                self.log_test("Events API - Calendar Load", False, 
                            error=f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Events API - Calendar Load", False, error=str(e))
    
    def test_ai_execute_action_create_event(self):
        """Test POST /api/ai/execute-action with action_type=create_event"""
        print("🤖 Testing AI Execute Action - Create Event...")
        
        try:
            # Test data as specified in the review request
            action_data = {
                "title": "Test Termin",
                "date": "2026-05-20",
                "start_time": "10:00",
                "end_time": "11:00"
            }
            
            form_data = {
                "action_type": "create_event",
                "action_data": json.dumps(action_data),
                "confirmed": "true"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/ai/execute-action",
                data=form_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                
                if success:
                    created_event = data.get("created")
                    if created_event:
                        event_id = created_event.get("id")
                        event_title = created_event.get("title")
                        
                        # Verify event appears in GET /api/events
                        events_response = self.session.get(f"{BACKEND_URL}/api/events", timeout=30)
                        if events_response.status_code == 200:
                            events = events_response.json()
                            event_found = any(e.get("id") == event_id for e in events)
                            
                            if event_found:
                                self.log_test("AI Execute Action - Create Event", True, 
                                            f"Event '{event_title}' created and appears in calendar")
                                
                                # Clean up - delete the test event
                                try:
                                    self.session.delete(f"{BACKEND_URL}/api/events/{event_id}", timeout=30)
                                except:
                                    pass  # Cleanup failure is not critical
                            else:
                                self.log_test("AI Execute Action - Create Event", False, 
                                            "Event created but not found in calendar list")
                        else:
                            self.log_test("AI Execute Action - Create Event", False, 
                                        "Event created but could not verify in calendar")
                    else:
                        self.log_test("AI Execute Action - Create Event", False, 
                                    "Success=true but no created event data")
                else:
                    error_msg = data.get("error", "Unknown error")
                    self.log_test("AI Execute Action - Create Event", False, 
                                error=f"API returned success=false: {error_msg}")
            else:
                self.log_test("AI Execute Action - Create Event", False, 
                            error=f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("AI Execute Action - Create Event", False, error=str(e))
    
    def test_ai_execute_action_create_task(self):
        """Test POST /api/ai/execute-action with action_type=create_task"""
        print("📋 Testing AI Execute Action - Create Task...")
        
        try:
            # Test data as specified in the review request
            action_data = {
                "title": "Test Aufgabe",
                "due_date": "2026-05-25",
                "priority": "high"
            }
            
            form_data = {
                "action_type": "create_task",
                "action_data": json.dumps(action_data),
                "confirmed": "true"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/ai/execute-action",
                data=form_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                
                if success:
                    created_task = data.get("created")
                    if created_task:
                        task_id = created_task.get("id")
                        task_title = created_task.get("title")
                        
                        # Verify task appears in GET /api/tasks
                        tasks_response = self.session.get(f"{BACKEND_URL}/api/tasks", timeout=30)
                        if tasks_response.status_code == 200:
                            tasks = tasks_response.json()
                            task_found = any(t.get("id") == task_id for t in tasks)
                            
                            if task_found:
                                self.log_test("AI Execute Action - Create Task", True, 
                                            f"Task '{task_title}' created successfully")
                                
                                # Clean up - delete the test task
                                try:
                                    self.session.delete(f"{BACKEND_URL}/api/tasks/{task_id}", timeout=30)
                                except:
                                    pass  # Cleanup failure is not critical
                            else:
                                self.log_test("AI Execute Action - Create Task", False, 
                                            "Task created but not found in tasks list")
                        else:
                            self.log_test("AI Execute Action - Create Task", False, 
                                        "Task created but could not verify in tasks list")
                    else:
                        self.log_test("AI Execute Action - Create Task", False, 
                                    "Success=true but no created task data")
                else:
                    error_msg = data.get("error", "Unknown error")
                    self.log_test("AI Execute Action - Create Task", False, 
                                error=f"API returned success=false: {error_msg}")
            else:
                self.log_test("AI Execute Action - Create Task", False, 
                            error=f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("AI Execute Action - Create Task", False, error=str(e))
    
    def run_all_tests(self):
        """Run all v1.5.0 tests"""
        print("🚀 Starting CaseDesk AI v1.5.0 Backend Testing")
        print("=" * 60)
        print()
        
        # Authentication is required for most endpoints
        if not self.authenticate():
            print("❌ Authentication failed - cannot continue with tests")
            return False
        
        # Test all v1.5.0 features
        self.test_health_endpoint_version()
        self.test_system_version_endpoint()
        self.test_events_api_calendar_load()
        self.test_ai_execute_action_create_event()
        self.test_ai_execute_action_create_task()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['error']}")
            print()
        
        print("✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"  - {result['test']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = CaseDeskTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)