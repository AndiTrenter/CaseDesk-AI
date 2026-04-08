"""
Test suite for date parsing fix - Iteration 9
Tests the robust date parsing for malformed date strings in events and tasks.

Bug context: User reported 'calendarload.error' due to malformed date strings in MongoDB
like '2026-04-09T', '2026-04-09T:00' which caused Pydantic ValidationErrors.
Fix: safe_parse_datetime() function in utils/date_utils.py
"""
import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://task-portal-fix.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"


class TestDateParsingFix:
    """Test the robust date parsing fix for events and tasks"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_events_endpoint_returns_valid_dates(self):
        """Test GET /api/events returns properly formatted dates"""
        response = requests.get(f"{BASE_URL}/api/events", headers=self.headers)
        assert response.status_code == 200, f"Events endpoint failed: {response.text}"
        
        events = response.json()
        print(f"✓ Events endpoint returned {len(events)} events")
        
        for event in events:
            # Check date fields are either None or valid ISO format
            for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
                value = event.get(field)
                if value is not None:
                    # Should be parseable as ISO datetime
                    try:
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                        print(f"  ✓ Event '{event.get('title')}' {field}: {value}")
                    except ValueError as e:
                        pytest.fail(f"Invalid date format for {field}: {value} - {e}")
    
    def test_tasks_endpoint_returns_valid_dates(self):
        """Test GET /api/tasks returns properly formatted dates"""
        response = requests.get(f"{BASE_URL}/api/tasks", headers=self.headers)
        assert response.status_code == 200, f"Tasks endpoint failed: {response.text}"
        
        tasks = response.json()
        print(f"✓ Tasks endpoint returned {len(tasks)} tasks")
        
        for task in tasks:
            # Check date fields are either None or valid ISO format
            for field in ['due_date', 'created_at', 'updated_at']:
                value = task.get(field)
                if value is not None:
                    try:
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                        print(f"  ✓ Task '{task.get('title')}' {field}: {value}")
                    except ValueError as e:
                        pytest.fail(f"Invalid date format for {field}: {value} - {e}")
    
    def test_create_event_with_valid_dates(self):
        """Test creating an event with valid dates"""
        event_data = {
            "title": "TEST_DateParsing_Event",
            "description": "Test event for date parsing verification",
            "start_time": "2026-04-15T10:00:00",
            "end_time": "2026-04-15T11:00:00",
            "case_id": None
        }
        
        response = requests.post(
            f"{BASE_URL}/api/events",
            json=event_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"Create event failed: {response.text}"
        
        created_event = response.json()
        event_id = created_event["id"]
        print(f"✓ Created event: {created_event['title']} (ID: {event_id})")
        
        # Verify the event appears in the list with correct dates
        response = requests.get(f"{BASE_URL}/api/events", headers=self.headers)
        events = response.json()
        test_event = next((e for e in events if e["id"] == event_id), None)
        
        assert test_event is not None, "Created event not found in list"
        assert test_event["start_time"] == "2026-04-15T10:00:00"
        assert test_event["end_time"] == "2026-04-15T11:00:00"
        print(f"✓ Event dates verified: start={test_event['start_time']}, end={test_event['end_time']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/events/{event_id}", headers=self.headers)
        print(f"✓ Cleaned up test event")
    
    def test_create_task_with_due_date(self):
        """Test creating a task with a due date"""
        task_data = {
            "title": "TEST_DateParsing_Task",
            "description": "Test task for date parsing verification",
            "priority": "high",
            "status": "todo",
            "due_date": "2026-04-20T14:00:00",
            "case_id": None
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tasks",
            json=task_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"Create task failed: {response.text}"
        
        created_task = response.json()
        task_id = created_task["id"]
        print(f"✓ Created task: {created_task['title']} (ID: {task_id})")
        
        # Verify the task appears in the list with correct date
        response = requests.get(f"{BASE_URL}/api/tasks", headers=self.headers)
        tasks = response.json()
        test_task = next((t for t in tasks if t["id"] == task_id), None)
        
        assert test_task is not None, "Created task not found in list"
        assert test_task["due_date"] == "2026-04-20T14:00:00"
        print(f"✓ Task due_date verified: {test_task['due_date']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tasks/{task_id}", headers=self.headers)
        print(f"✓ Cleaned up test task")


class TestDateUtilsFunction:
    """Test the safe_parse_datetime function directly"""
    
    def test_safe_parse_datetime_with_datetime_object(self):
        """Test parsing datetime objects"""
        from utils.date_utils import safe_parse_datetime
        
        dt = datetime(2026, 4, 9, 10, 30, 0)
        result = safe_parse_datetime(dt)
        assert result == "2026-04-09T10:30:00"
        print(f"✓ datetime object: {dt} -> {result}")
    
    def test_safe_parse_datetime_with_valid_iso_string(self):
        """Test parsing valid ISO strings"""
        from utils.date_utils import safe_parse_datetime
        
        test_cases = [
            ("2026-04-09T10:30:00", "2026-04-09T10:30:00"),
            ("2026-04-09T10:30:00Z", "2026-04-09T10:30:00+00:00"),
        ]
        
        for input_str, expected in test_cases:
            result = safe_parse_datetime(input_str)
            assert result == expected, f"Expected {expected}, got {result}"
            print(f"✓ Valid ISO: '{input_str}' -> '{result}'")
    
    def test_safe_parse_datetime_with_malformed_strings(self):
        """Test parsing malformed date strings (the main bug fix)"""
        from utils.date_utils import safe_parse_datetime
        
        # These are the malformed formats that caused the original bug
        test_cases = [
            ("2026-04-09T", "2026-04-09T00:00:00"),  # Missing time
            ("2026-04-09T:00", "2026-04-09T00:00:00"),  # Malformed time
            ("2026-04-09", "2026-04-09T00:00:00"),  # Date only
        ]
        
        for input_str, expected in test_cases:
            result = safe_parse_datetime(input_str)
            assert result == expected, f"For '{input_str}': expected {expected}, got {result}"
            print(f"✓ Malformed: '{input_str}' -> '{result}'")
    
    def test_safe_parse_datetime_with_none(self):
        """Test parsing None returns None"""
        from utils.date_utils import safe_parse_datetime
        
        result = safe_parse_datetime(None)
        assert result is None
        print(f"✓ None -> None")
    
    def test_safe_parse_datetime_with_empty_string(self):
        """Test parsing empty string returns None"""
        from utils.date_utils import safe_parse_datetime
        
        result = safe_parse_datetime("")
        assert result is None
        print(f"✓ Empty string -> None")


class TestEmailSendingEndpoint:
    """Test email sending endpoint doesn't cause errors"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_mail_accounts_endpoint(self):
        """Test mail accounts endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/mail/accounts", headers=self.headers)
        assert response.status_code == 200, f"Mail accounts endpoint failed: {response.text}"
        accounts = response.json()
        print(f"✓ Mail accounts endpoint returned {len(accounts)} accounts")
    
    def test_emails_list_endpoint(self):
        """Test emails list endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/emails", headers=self.headers)
        assert response.status_code == 200, f"Emails endpoint failed: {response.text}"
        emails = response.json()
        print(f"✓ Emails endpoint returned {len(emails)} emails")


class TestDocumentsEndpoint:
    """Test documents endpoint for icon/preview functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_documents_list_endpoint(self):
        """Test documents list endpoint returns documents with mime_type for icons"""
        response = requests.get(f"{BASE_URL}/api/documents", headers=self.headers)
        assert response.status_code == 200, f"Documents endpoint failed: {response.text}"
        
        documents = response.json()
        print(f"✓ Documents endpoint returned {len(documents)} documents")
        
        for doc in documents:
            # Verify document has fields needed for icon display
            assert "id" in doc, "Document missing 'id'"
            assert "display_name" in doc or "original_filename" in doc, "Document missing name field"
            
            # mime_type is used for icon selection
            mime_type = doc.get("mime_type")
            if mime_type:
                print(f"  ✓ Document '{doc.get('display_name', doc.get('original_filename'))}' mime_type: {mime_type}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
