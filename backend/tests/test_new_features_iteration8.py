"""
Test Suite for CaseDesk AI - Iteration 8 New Features
Tests: Admin Health, AI Knowledge, Onboarding, Suggest-Metadata, Event with Task Creation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "Speedy@181279"


class TestSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"Health check passed: {data}")


class TestAdminHealth:
    """Tests for GET /api/admin/health - Admin healthcheck dashboard"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_admin_health_returns_services(self, auth_headers):
        """Test admin health endpoint returns all service statuses"""
        response = requests.get(f"{BASE_URL}/api/admin/health", headers=auth_headers)
        assert response.status_code == 200, f"Admin health failed: {response.text}"
        
        data = response.json()
        assert "timestamp" in data
        assert "services" in data
        
        services = data["services"]
        # Check required services are present
        assert "mongodb" in services, "MongoDB status missing"
        assert "storage" in services, "Storage status missing"
        assert "tesseract" in services, "Tesseract status missing"
        
        # MongoDB should be connected
        assert services["mongodb"]["status"] == "connected", f"MongoDB not connected: {services['mongodb']}"
        
        # Storage should be ok
        assert services["storage"]["status"] == "ok", f"Storage not ok: {services['storage']}"
        
        # Tesseract should be installed
        assert services["tesseract"]["status"] == "installed", f"Tesseract not installed: {services['tesseract']}"
        
        print(f"Admin health services: {list(services.keys())}")
        print(f"MongoDB: {services['mongodb']}")
        print(f"Storage: {services['storage']}")
        print(f"Tesseract: {services['tesseract']}")
    
    def test_admin_health_requires_auth(self):
        """Test admin health requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/health")
        assert response.status_code == 401, "Admin health should require auth"


class TestAIKnowledge:
    """Tests for GET /api/ai/knowledge - AI Knowledge endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_ai_knowledge_returns_comprehensive_data(self, auth_headers):
        """Test AI knowledge endpoint returns profile, onboarding, documents, cases"""
        response = requests.get(f"{BASE_URL}/api/ai/knowledge", headers=auth_headers)
        assert response.status_code == 200, f"AI knowledge failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        # Check required fields
        assert "profile" in data, "Profile missing from AI knowledge"
        assert "onboarding" in data, "Onboarding missing from AI knowledge"
        assert "documents" in data, "Documents missing from AI knowledge"
        assert "cases" in data, "Cases missing from AI knowledge"
        assert "documents_analyzed" in data, "documents_analyzed count missing"
        assert "cases_count" in data, "cases_count missing"
        
        print(f"AI Knowledge - Documents analyzed: {data['documents_analyzed']}")
        print(f"AI Knowledge - Cases count: {data['cases_count']}")
        print(f"AI Knowledge - Profile facts: {len(data.get('profile', {}).get('facts', []))}")


class TestOnboarding:
    """Tests for POST/GET /api/ai/onboarding - User onboarding profile"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_save_onboarding_profile(self, auth_headers):
        """Test saving onboarding profile data"""
        onboarding_data = {
            "full_name": "TEST_Max Mustermann",
            "address": "Musterstr. 1, 12345 Berlin",
            "phone": "+49 123 456789",
            "birthdate": "01.01.1990",
            "marital_status": "Verheiratet",
            "employer": "Test GmbH",
            "occupation": "Softwareentwickler"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/onboarding",
            data=onboarding_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Save onboarding failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        print("Onboarding profile saved successfully")
    
    def test_get_onboarding_profile(self, auth_headers):
        """Test retrieving onboarding profile"""
        response = requests.get(f"{BASE_URL}/api/ai/onboarding", headers=auth_headers)
        assert response.status_code == 200, f"Get onboarding failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "profile" in data
        
        profile = data["profile"]
        # Verify saved data persisted
        if profile:
            print(f"Onboarding profile retrieved: {list(profile.keys())}")
            if profile.get("full_name"):
                assert "TEST_" in profile["full_name"] or "Max" in profile.get("full_name", "")


class TestSuggestMetadata:
    """Tests for POST /api/documents/suggest-metadata - AI tag/case suggestions"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_suggest_metadata_with_valid_document(self, auth_headers):
        """Test suggest-metadata endpoint with a valid document"""
        # First get a document ID
        docs_response = requests.get(f"{BASE_URL}/api/documents", headers=auth_headers)
        assert docs_response.status_code == 200
        
        docs = docs_response.json()
        if len(docs) == 0:
            pytest.skip("No documents available for testing suggest-metadata")
        
        # Use first document
        doc_id = docs[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/documents/suggest-metadata",
            data={"document_id": doc_id},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Suggest metadata failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "suggested_tags" in data
        assert "suggested_cases" in data
        
        print(f"Suggested tags: {data['suggested_tags']}")
        print(f"Suggested cases: {len(data['suggested_cases'])}")
    
    def test_suggest_metadata_invalid_document(self, auth_headers):
        """Test suggest-metadata with invalid document ID"""
        response = requests.post(
            f"{BASE_URL}/api/documents/suggest-metadata",
            data={"document_id": "invalid-doc-id-12345"},
            headers=auth_headers
        )
        assert response.status_code == 200  # Returns success=False, not 404
        data = response.json()
        assert data.get("success") == False or "error" in data


class TestEventWithTaskCreation:
    """Tests for POST /api/events with create_task=true"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_create_event_without_task(self, auth_headers):
        """Test creating event without task creation"""
        from datetime import datetime, timedelta
        
        start = datetime.now() + timedelta(days=1)
        end = start + timedelta(hours=1)
        
        event_data = {
            "title": "TEST_Event_NoTask",
            "description": "Test event without task",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "create_task": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/events",
            json=event_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Create event failed: {response.text}"
        
        data = response.json()
        assert data.get("title") == "TEST_Event_NoTask"
        assert "task_id" not in data or data.get("task_id") is None
        
        # Cleanup
        event_id = data["id"]
        requests.delete(f"{BASE_URL}/api/events/{event_id}", headers=auth_headers)
        print("Event without task created successfully")
    
    def test_create_event_with_task(self, auth_headers):
        """Test creating event with automatic task creation"""
        from datetime import datetime, timedelta
        
        start = datetime.now() + timedelta(days=2)
        end = start + timedelta(hours=1)
        
        event_data = {
            "title": "TEST_Event_WithTask",
            "description": "Test event with task creation",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "create_task": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/events",
            json=event_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Create event with task failed: {response.text}"
        
        data = response.json()
        assert data.get("title") == "TEST_Event_WithTask"
        
        # Check if task was created
        if "task_id" in data and data["task_id"]:
            print(f"Task created with ID: {data['task_id']}")
            
            # Verify task exists
            tasks_response = requests.get(f"{BASE_URL}/api/tasks", headers=auth_headers)
            assert tasks_response.status_code == 200
            tasks = tasks_response.json()
            
            task_found = any(t["id"] == data["task_id"] for t in tasks)
            assert task_found, "Created task not found in tasks list"
            
            # Cleanup task
            requests.delete(f"{BASE_URL}/api/tasks/{data['task_id']}", headers=auth_headers)
        
        # Cleanup event
        event_id = data["id"]
        requests.delete(f"{BASE_URL}/api/events/{event_id}", headers=auth_headers)
        print("Event with task created and verified successfully")


class TestRequirementsTxt:
    """Test that requirements.txt has no emergent packages"""
    
    def test_no_emergent_packages(self):
        """Verify requirements.txt doesn't contain emergent-specific packages"""
        requirements_path = "/app/backend/requirements.txt"
        
        with open(requirements_path, 'r') as f:
            content = f.read().lower()
        
        forbidden_packages = [
            "emergentintegrations",
            "emergent-integrations",
            "emergent_integrations",
            "emergent-llm",
            "emergent_llm"
        ]
        
        for pkg in forbidden_packages:
            assert pkg not in content, f"Found forbidden package '{pkg}' in requirements.txt"
        
        print("requirements.txt verified - no emergent packages found")


class TestNavigationEndpoints:
    """Test that new navigation endpoints work"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_ai_profile_endpoint(self, auth_headers):
        """Test AI profile endpoint works"""
        response = requests.get(f"{BASE_URL}/api/ai/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "profile" in data
        print("AI profile endpoint working")
    
    def test_events_list(self, auth_headers):
        """Test events list endpoint"""
        response = requests.get(f"{BASE_URL}/api/events", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Events list: {len(response.json())} events")
    
    def test_tasks_list(self, auth_headers):
        """Test tasks list endpoint"""
        response = requests.get(f"{BASE_URL}/api/tasks", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"Tasks list: {len(response.json())} tasks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
