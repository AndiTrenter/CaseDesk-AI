"""
CaseDesk AI Backend API Testing
Comprehensive test suite for all backend endpoints
"""
import requests
import json
import sys
from datetime import datetime
import tempfile
import os

class CaseDeskAPITester:
    def __init__(self, base_url="https://case-response-pkg.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user = None
        self.created_items = {
            'cases': [],
            'tasks': [],
            'events': [],
            'documents': []
        }

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, form_data=None):
        """Run a single API test"""
        url = f"{self.base_url}/api{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if form_data:
                # Use form data for multipart requests
                response = getattr(requests, method.lower())(url, data=form_data, headers=headers, files=files)
            elif data:
                headers['Content-Type'] = 'application/json'
                response = getattr(requests, method.lower())(url, json=data, headers=headers)
            else:
                response = getattr(requests, method.lower())(url, headers=headers)

            success = response.status_code == expected_status
            result_data = {}
            
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    result_data = response.json()
                except:
                    pass

            if success:
                self.log_test(name, True)
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                if result_data and 'detail' in result_data:
                    error_msg += f" - {result_data['detail']}"
                self.log_test(name, False, error_msg)

            return success, result_data

        except Exception as e:
            self.log_test(name, False, f"Request error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, data = self.run_test("Health Check", "GET", "/health", 200)
        return success and data.get("status") == "healthy"

    def test_setup_status(self):
        """Test setup status endpoint"""
        success, data = self.run_test("Setup Status", "GET", "/setup/status", 200)
        return success and "setup_completed" in data

    def test_setup_initialization(self):
        """Test setup initialization or skip if already completed"""
        success, data = self.run_test("Setup Status Check", "GET", "/setup/status", 200)
        
        if success and data.get('setup_completed'):
            # Setup already completed, skip initialization
            self.log_test("Setup Already Completed", True)
            return True
        else:
            # Try to initialize setup
            setup_data = {
                'language': 'en',
                'admin_email': f'admin_{datetime.now().strftime("%H%M%S")}@test.com',
                'admin_username': f'admin_{datetime.now().strftime("%H%M%S")}',
                'admin_password': 'TestAdmin123!',
                'admin_full_name': 'Test Administrator',
                'ai_provider': 'disabled',
                'internet_access': 'denied'
            }
            
            success, data = self.run_test("Setup Initialization", "POST", "/setup/init", 200, form_data=setup_data)
            
            if success and data.get('success'):
                self.token = data.get('access_token')
                self.admin_user = data.get('user')
                return True
            return False

    def test_authentication(self):
        """Test login with existing admin credentials"""        
        login_data = {
            'email': 'admin@casedesk.app',
            'password': 'admin123'
        }
        
        success, data = self.run_test("User Login", "POST", "/auth/login", 200, form_data=login_data)
        
        if success and data.get('access_token'):
            self.token = data['access_token']
            self.admin_user = data.get('user')
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        success, data = self.run_test("Get Current User", "GET", "/auth/me", 200)
        return success and data.get('email')

    def test_cases_crud(self):
        """Test Cases CRUD operations"""
        all_passed = True
        
        # Create case
        case_data = {
            "title": "Test Case 001",
            "description": "Test case for API testing",
            "reference_number": "CASE-TEST-001",
            "status": "open"
        }
        success, data = self.run_test("Create Case", "POST", "/cases", 200, case_data)
        if success and data.get('id'):
            case_id = data['id']
            self.created_items['cases'].append(case_id)
            
            # Get case
            success, _ = self.run_test("Get Case", "GET", f"/cases/{case_id}", 200)
            all_passed = all_passed and success
            
            # List cases
            success, data = self.run_test("List Cases", "GET", "/cases", 200)
            all_passed = all_passed and success and len(data) > 0
            
            # Update case
            update_data = {**case_data, "status": "in_progress"}
            success, _ = self.run_test("Update Case", "PUT", f"/cases/{case_id}", 200, update_data)
            all_passed = all_passed and success
            
        else:
            all_passed = False
            
        return all_passed

    def test_tasks_crud(self):
        """Test Tasks CRUD operations"""
        all_passed = True
        
        # Create task
        task_data = {
            "title": "Test Task 001",
            "description": "Test task for API testing",
            "priority": "high",
            "status": "todo",
            "due_date": "2024-12-31T23:59:59Z"
        }
        success, data = self.run_test("Create Task", "POST", "/tasks", 200, task_data)
        if success and data.get('id'):
            task_id = data['id']
            self.created_items['tasks'].append(task_id)
            
            # List tasks
            success, data = self.run_test("List Tasks", "GET", "/tasks", 200)
            all_passed = all_passed and success and len(data) > 0
            
            # Update task
            update_data = {**task_data, "status": "done"}
            success, _ = self.run_test("Update Task", "PUT", f"/tasks/{task_id}", 200, update_data)
            all_passed = all_passed and success
            
        else:
            all_passed = False
            
        return all_passed

    def test_events_crud(self):
        """Test Events CRUD operations"""
        all_passed = True
        
        # Create event
        event_data = {
            "title": "Test Meeting",
            "description": "Test meeting for API testing",
            "start_time": "2024-12-01T10:00:00Z",
            "end_time": "2024-12-01T11:00:00Z",
            "all_day": False,
            "location": "Conference Room A"
        }
        success, data = self.run_test("Create Event", "POST", "/events", 200, event_data)
        if success and data.get('id'):
            event_id = data['id']
            self.created_items['events'].append(event_id)
            
            # List events
            success, data = self.run_test("List Events", "GET", "/events", 200)
            all_passed = all_passed and success and len(data) > 0
            
            # Update event
            update_data = {**event_data, "location": "Conference Room B"}
            success, _ = self.run_test("Update Event", "PUT", f"/events/{event_id}", 200, update_data)
            all_passed = all_passed and success
            
        else:
            all_passed = False
            
        return all_passed

    def test_document_upload(self):
        """Test Document upload functionality"""
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content for API testing")
            temp_file_path = f.name

        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                form_data = {
                    'document_type': 'other'
                }
                
                success, data = self.run_test("Upload Document", "POST", "/documents/upload", 200, 
                                            files=files, form_data=form_data)
                
                if success and data.get('success') and data.get('document'):
                    doc_id = data['document']['id']
                    self.created_items['documents'].append(doc_id)
                    
                    # List documents
                    success, _ = self.run_test("List Documents", "GET", "/documents", 200)
                    return success
                    
        finally:
            os.unlink(temp_file_path)
        
        return False

    def test_ai_chat(self):
        """Test AI chat functionality"""
        chat_data = {
            'message': 'Hello, this is a test message'
        }
        success, data = self.run_test("AI Chat", "POST", "/ai/chat", 200, form_data=chat_data)
        return success  # AI may be disabled, so just check endpoint works

    def test_settings_crud(self):
        """Test Settings operations"""
        all_passed = True
        
        # Get system settings (admin only)
        success, _ = self.run_test("Get System Settings", "GET", "/settings/system", 200)
        all_passed = all_passed and success
        
        # Get user settings
        success, _ = self.run_test("Get User Settings", "GET", "/settings/user", 200)
        all_passed = all_passed and success
        
        # Update user settings
        user_settings = {
            'language': 'de',
            'theme': 'dark',
            'notifications_enabled': True
        }
        success, _ = self.run_test("Update User Settings", "PUT", "/settings/user", 200, form_data=user_settings)
        all_passed = all_passed and success
        
        return all_passed

    def test_dashboard_stats(self):
        """Test Dashboard statistics"""
        success, data = self.run_test("Get Dashboard Stats", "GET", "/dashboard/stats", 200)
        return success and 'cases' in data and 'documents' in data and 'tasks' in data

    def cleanup_test_data(self):
        """Clean up created test data"""
        print(f"\n🧹 Cleaning up test data...")
        
        # Delete created items
        for doc_id in self.created_items['documents']:
            self.run_test(f"Delete Document {doc_id}", "DELETE", f"/documents/{doc_id}", 200)
            
        for event_id in self.created_items['events']:
            self.run_test(f"Delete Event {event_id}", "DELETE", f"/events/{event_id}", 200)
            
        for task_id in self.created_items['tasks']:
            self.run_test(f"Delete Task {task_id}", "DELETE", f"/tasks/{task_id}", 200)
            
        for case_id in self.created_items['cases']:
            self.run_test(f"Delete Case {case_id}", "DELETE", f"/cases/{case_id}", 200)

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting CaseDesk AI Backend API Tests")
        print("=" * 50)
        
        # Core functionality tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Setup Status", self.test_setup_status),
            ("Setup Initialization", self.test_setup_initialization),
            ("Authentication", self.test_authentication),
            ("Get Current User", self.test_get_current_user),
            ("Cases CRUD", self.test_cases_crud),
            ("Tasks CRUD", self.test_tasks_crud),
            ("Events CRUD", self.test_events_crud),
            ("Document Upload", self.test_document_upload),
            ("Settings Operations", self.test_settings_crud),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("AI Chat", self.test_ai_chat),
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                if not test_func():
                    failed_tests.append(test_name)
            except Exception as e:
                print(f"❌ {test_name} - Exception: {str(e)}")
                failed_tests.append(test_name)
        
        # Cleanup
        self.cleanup_test_data()
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if failed_tests:
            print(f"❌ Failed tests: {', '.join(failed_tests)}")
            return False
        else:
            print("✅ All tests passed!")
            return True


def main():
    """Main test execution"""
    tester = CaseDeskAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())