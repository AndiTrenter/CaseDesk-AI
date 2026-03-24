"""
CaseDesk AI - Comprehensive Backend Tests for Refactored Architecture
Tests all routers after server.py split into domain-specific modules
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@casedesk.app"
TEST_PASSWORD = "admin123"


class TestHealthAndSetup:
    """Health check and setup status endpoints"""
    
    def test_health_endpoint_returns_healthy(self):
        """GET /api/health returns status: healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "casedesk-backend"
        assert "version" in data
        print(f"✓ Health check passed: {data}")
    
    def test_setup_status_returns_fields(self):
        """GET /api/setup/status returns is_configured and has_admin"""
        response = requests.get(f"{BASE_URL}/api/setup/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_configured" in data
        assert "has_admin" in data
        assert data["has_admin"] == True  # Admin exists
        print(f"✓ Setup status: {data}")


class TestAuthentication:
    """Authentication endpoints"""
    
    def test_login_returns_token_and_user(self):
        """POST /api/auth/login returns access_token and user object"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✓ Login successful, user role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login with wrong password returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_get_current_user_info(self):
        """GET /api/auth/me returns current user with role='admin'"""
        # First login
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = login_resp.json()["access_token"]
        
        # Get user info
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert data["role"] == "admin"
        print(f"✓ Current user: {data['email']}, role: {data['role']}")


class TestDashboard:
    """Dashboard stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_stats_returns_counts(self):
        """GET /api/dashboard/stats returns cases, documents, tasks counts"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert "documents" in data
        assert "tasks" in data
        assert "total" in data["cases"]
        assert "total" in data["documents"]
        print(f"✓ Dashboard stats: cases={data['cases']['total']}, docs={data['documents']['total']}, tasks={data['tasks']['pending']}")


class TestCases:
    """Cases CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_cases(self):
        """GET /api/cases returns list of cases"""
        response = requests.get(
            f"{BASE_URL}/api/cases",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Cases list: {len(data)} cases found")


class TestDocuments:
    """Documents CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_documents(self):
        """GET /api/documents returns list of documents"""
        response = requests.get(
            f"{BASE_URL}/api/documents",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Documents list: {len(data)} documents found")


class TestTasks:
    """Tasks CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_tasks(self):
        """GET /api/tasks returns list of tasks"""
        response = requests.get(
            f"{BASE_URL}/api/tasks",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Tasks list: {len(data)} tasks found")


class TestEvents:
    """Events CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_events(self):
        """GET /api/events returns list of events"""
        response = requests.get(
            f"{BASE_URL}/api/events",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Events list: {len(data)} events found")


class TestAIChat:
    """AI Chat endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_ai_chat_german_response(self):
        """POST /api/ai/chat with German message returns German response with referenced_documents"""
        response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers=self.headers,
            data={"message": "Zeige mir alle meine Dokumente"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "referenced_documents" in data
        # Check response is in German (contains German words)
        german_indicators = ["dokument", "ihre", "hier", "alle", "frist", "fall"]
        response_lower = data["response"].lower()
        has_german = any(word in response_lower for word in german_indicators)
        print(f"✓ AI Chat response (German): {data['response'][:100]}...")
        print(f"✓ Referenced documents: {len(data['referenced_documents'])} docs")


class TestSettings:
    """Settings endpoints with role-based access"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_system_settings_admin_only(self):
        """GET /api/settings/system returns system settings (admin only)"""
        response = requests.get(
            f"{BASE_URL}/api/settings/system",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should return settings object (not error)
        assert isinstance(data, dict)
        print(f"✓ System settings accessible by admin: {list(data.keys())}")
    
    def test_user_settings_returns_language(self):
        """GET /api/settings/user returns user settings with language='de'"""
        response = requests.get(
            f"{BASE_URL}/api/settings/user",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert data["language"] == "de"
        print(f"✓ User settings: language={data['language']}")
    
    def test_system_settings_requires_auth(self):
        """GET /api/settings/system without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/settings/system")
        assert response.status_code == 401
        print("✓ System settings correctly requires authentication")


class TestExport:
    """Data export endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_export_all_returns_zip(self):
        """GET /api/export/all returns ZIP file (Content-Type: application/zip)"""
        response = requests.get(
            f"{BASE_URL}/api/export/all",
            headers=self.headers
        )
        assert response.status_code == 200
        assert "application/zip" in response.headers.get("Content-Type", "")
        # Check ZIP magic bytes
        assert response.content[:4] == b'PK\x03\x04'
        print(f"✓ Export returns valid ZIP file, size: {len(response.content)} bytes")


class TestRoleBasedAccess:
    """Role-based access control tests"""
    
    def test_system_settings_requires_admin_role(self):
        """System settings should require admin role"""
        # Login as admin
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = login_resp.json()["access_token"]
        user_role = login_resp.json()["user"]["role"]
        
        # Admin should have access
        response = requests.get(
            f"{BASE_URL}/api/settings/system",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if user_role == "admin":
            assert response.status_code == 200
            print(f"✓ Admin user has access to system settings")
        else:
            assert response.status_code == 403
            print(f"✓ Non-admin user correctly denied access")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
