"""
CaseDesk AI Backend Tests - Iteration 7
Testing: Calendar, Tasks, Documents, and core API functionality
Test credentials: andi.trenter@gmail.com / admin123
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Health check and authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print(f"✓ Health check passed - version: {data.get('version')}")
    
    def test_login_with_test_credentials(self):
        """Test login with andi.trenter@gmail.com / admin123"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "andi.trenter@gmail.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "andi.trenter@gmail.com"
        assert data["user"]["role"] == "admin"
        print(f"✓ Login successful - user: {data['user']['email']}, role: {data['user']['role']}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")


class TestEventsAPI:
    """Calendar/Events API tests - Critical for 'Failed to load events' bug"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "andi.trenter@gmail.com", "password": "admin123"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_events_returns_200(self):
        """Test GET /api/events returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/events", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Events list returned {len(data)} events")
    
    def test_list_events_returns_valid_structure(self):
        """Test events have required fields"""
        response = requests.get(f"{BASE_URL}/api/events", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            event = data[0]
            assert "id" in event
            assert "title" in event
            assert "start_time" in event
            print(f"✓ Event structure valid - first event: {event.get('title')}")
        else:
            print("✓ Events list empty but valid")
    
    def test_get_reminder_options(self):
        """Test GET /api/events/reminder-options returns options"""
        response = requests.get(f"{BASE_URL}/api/events/reminder-options", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "options" in data
        assert len(data["options"]) > 0
        print(f"✓ Reminder options returned {len(data['options'])} options")
    
    def test_create_and_delete_event(self):
        """Test event CRUD - create and delete"""
        # Create event
        event_data = {
            "title": "TEST_Event_Iteration7",
            "description": "Test event for iteration 7",
            "start_time": "2026-04-15T10:00:00",
            "end_time": "2026-04-15T11:00:00",
            "all_day": False
        }
        create_response = requests.post(
            f"{BASE_URL}/api/events",
            json=event_data,
            headers=self.headers
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["title"] == event_data["title"]
        event_id = created["id"]
        print(f"✓ Event created with ID: {event_id}")
        
        # Verify event exists in list
        list_response = requests.get(f"{BASE_URL}/api/events", headers=self.headers)
        events = list_response.json()
        event_ids = [e["id"] for e in events]
        assert event_id in event_ids
        print("✓ Event found in list")
        
        # Delete event
        delete_response = requests.delete(f"{BASE_URL}/api/events/{event_id}", headers=self.headers)
        assert delete_response.status_code == 200
        print("✓ Event deleted successfully")


class TestTasksAPI:
    """Tasks API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "andi.trenter@gmail.com", "password": "admin123"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_tasks_returns_200(self):
        """Test GET /api/tasks returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/tasks", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Tasks list returned {len(data)} tasks")
    
    def test_list_tasks_returns_valid_structure(self):
        """Test tasks have required fields"""
        response = requests.get(f"{BASE_URL}/api/tasks", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            task = data[0]
            assert "id" in task
            assert "title" in task
            assert "status" in task
            assert task["status"] in ["todo", "in_progress", "done"]
            print(f"✓ Task structure valid - first task: {task.get('title')}, status: {task.get('status')}")
        else:
            print("✓ Tasks list empty but valid")
    
    def test_create_and_delete_task(self):
        """Test task CRUD - create and delete"""
        # Create task
        task_data = {
            "title": "TEST_Task_Iteration7",
            "description": "Test task for iteration 7",
            "priority": "high",
            "status": "todo"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/tasks",
            json=task_data,
            headers=self.headers
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["title"] == task_data["title"]
        task_id = created["id"]
        print(f"✓ Task created with ID: {task_id}")
        
        # Delete task
        delete_response = requests.delete(f"{BASE_URL}/api/tasks/{task_id}", headers=self.headers)
        assert delete_response.status_code == 200
        print("✓ Task deleted successfully")


class TestDocumentsAPI:
    """Documents API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "andi.trenter@gmail.com", "password": "admin123"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_documents_returns_200(self):
        """Test GET /api/documents returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/documents", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Documents list returned {len(data)} documents")
    
    def test_list_documents_returns_valid_structure(self):
        """Test documents have required fields"""
        response = requests.get(f"{BASE_URL}/api/documents", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            doc = data[0]
            assert "id" in doc
            assert "original_filename" in doc
            assert "mime_type" in doc
            print(f"✓ Document structure valid - first doc: {doc.get('original_filename')}")
        else:
            print("✓ Documents list empty but valid")
    
    def test_get_document_by_id(self):
        """Test GET /api/documents/{id} returns document details"""
        # First get list to find a document ID
        list_response = requests.get(f"{BASE_URL}/api/documents", headers=self.headers)
        docs = list_response.json()
        if len(docs) > 0:
            doc_id = docs[0]["id"]
            response = requests.get(f"{BASE_URL}/api/documents/{doc_id}", headers=self.headers)
            assert response.status_code == 200
            doc = response.json()
            assert doc["id"] == doc_id
            print(f"✓ Document retrieved by ID: {doc.get('original_filename')}")
        else:
            pytest.skip("No documents available to test")


class TestDashboardAPI:
    """Dashboard API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "andi.trenter@gmail.com", "password": "admin123"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_stats(self):
        """Test GET /api/dashboard/stats returns stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Check for expected fields
        assert "cases" in data or "total_cases" in data or "open_cases" in data
        print(f"✓ Dashboard stats returned: {data}")


class TestCasesAPI:
    """Cases API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "andi.trenter@gmail.com", "password": "admin123"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_cases_returns_200(self):
        """Test GET /api/cases returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/cases", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Cases list returned {len(data)} cases")


class TestNoOldAPIEndpoints:
    """Test that old /api/v1/* endpoints are not being used"""
    
    def test_no_v1_events_endpoint(self):
        """Test /api/v1/events returns 404 (old API)"""
        response = requests.get(f"{BASE_URL}/api/v1/events")
        # Should return 404 because v1 API doesn't exist
        assert response.status_code == 404
        print("✓ Old /api/v1/events endpoint correctly returns 404")
    
    def test_no_v1_tasks_endpoint(self):
        """Test /api/v1/tasks returns 404 (old API)"""
        response = requests.get(f"{BASE_URL}/api/v1/tasks")
        assert response.status_code == 404
        print("✓ Old /api/v1/tasks endpoint correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
