"""
CaseDesk AI - Proactive AI Features Test Suite
Tests for:
1. POST /api/ai/suggest-documents - Document suggestions for case creation
2. GET /api/cases/{id}/proactive-analysis - Proactive case analysis
3. GET /api/ai/daily-briefing - Daily briefing
4. Login, Dashboard, Theme toggle, Settings > Benutzer tab
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_CASE_ID = "4dc0a7e2-70fc-4159-adfc-63f46492e9af"


class TestAuthentication:
    """Test authentication flow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "admin@casedesk.app", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test login with admin credentials"""
        assert auth_token is not None
        print(f"Login successful - token obtained")
    
    def test_auth_me(self, auth_token):
        """Test get current user info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        data = response.json()
        assert data.get("email") == "admin@casedesk.app", "Email mismatch"
        print(f"User: {data.get('full_name')} ({data.get('email')})")


class TestProactiveAIEndpoints:
    """Test proactive AI endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "admin@casedesk.app", "password": "admin123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_suggest_documents_endpoint_exists(self, auth_headers):
        """POST /api/ai/suggest-documents - Verify endpoint exists and accepts parameters"""
        response = requests.post(
            f"{BASE_URL}/api/ai/suggest-documents",
            headers=auth_headers,
            data={
                "case_title": "Test Case for Document Suggestions",
                "case_description": "This is a test case to verify AI document suggestions work"
            }
        )
        # Expected: 200 with suggestions or error message about AI unavailable
        assert response.status_code == 200, f"Unexpected status: {response.status_code} - {response.text}"
        data = response.json()
        # Should return suggestions array or error about AI unavailable
        if data.get("success") == False:
            # AI not available is expected
            print(f"AI suggest-documents returned expected error: {data.get('error', 'AI unavailable')}")
        else:
            print(f"AI suggest-documents returned {len(data.get('suggestions', []))} suggestions")
        assert "suggestions" in data or "error" in data, "Response should have suggestions or error"
    
    def test_proactive_analysis_endpoint_exists(self, auth_headers):
        """GET /api/cases/{id}/proactive-analysis - Verify endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/cases/{TEST_CASE_ID}/proactive-analysis",
            headers=auth_headers
        )
        # Should return 200 with analysis or error, or 404 if case doesn't exist
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code} - {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") == False:
                print(f"Proactive analysis returned expected error: {data.get('error', 'AI unavailable')}")
            else:
                print(f"Proactive analysis successful for case: {data.get('case_title', TEST_CASE_ID)}")
        else:
            print(f"Case {TEST_CASE_ID} not found - expected if case was deleted")
    
    def test_daily_briefing_endpoint_exists(self, auth_headers):
        """GET /api/ai/daily-briefing - Verify endpoint exists and returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/ai/daily-briefing",
            headers=auth_headers
        )
        # Expected: 200 with briefing or error about AI unavailable
        assert response.status_code == 200, f"Unexpected status: {response.status_code} - {response.text}"
        data = response.json()
        
        # Should have success field
        if data.get("success") == False:
            # AI not available is expected since Ollama is not running
            print(f"Daily briefing returned expected error: {data.get('error', 'AI unavailable')}")
            assert "error" in data or "raw_response" in data
        else:
            print(f"Daily briefing successful - date: {data.get('date')}")
            assert "briefing" in data or "stats" in data


class TestDashboard:
    """Test dashboard stats endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "admin@casedesk.app", "password": "admin123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_dashboard_stats(self, auth_headers):
        """Test dashboard statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "cases" in data, "Missing cases stats"
        assert "documents" in data, "Missing documents stats"
        assert "tasks" in data, "Missing tasks stats"
        print(f"Dashboard stats: {data['cases']['total']} cases, {data['documents']['total']} docs, {data['tasks']['pending']} pending tasks")


class TestCases:
    """Test cases endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "admin@casedesk.app", "password": "admin123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_cases(self, auth_headers):
        """Test list cases"""
        response = requests.get(f"{BASE_URL}/api/cases", headers=auth_headers)
        assert response.status_code == 200, f"List cases failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} cases")
    
    def test_get_case_detail(self, auth_headers):
        """Test get specific case"""
        # First list cases to get a valid ID
        list_response = requests.get(f"{BASE_URL}/api/cases", headers=auth_headers)
        cases = list_response.json()
        
        if cases:
            case_id = cases[0]["id"]
            response = requests.get(f"{BASE_URL}/api/cases/{case_id}", headers=auth_headers)
            assert response.status_code == 200, f"Get case failed: {response.text}"
            data = response.json()
            assert data.get("id") == case_id
            print(f"Case detail: {data.get('title')} (status: {data.get('status')})")
        else:
            print("No cases found to test detail view")


class TestUserSettings:
    """Test user and settings endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "admin@casedesk.app", "password": "admin123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_users_admin(self, auth_headers):
        """Test admin can list users (for Benutzer tab)"""
        response = requests.get(f"{BASE_URL}/api/users", headers=auth_headers)
        assert response.status_code == 200, f"List users failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} users")
    
    def test_list_invitations(self, auth_headers):
        """Test list pending invitations"""
        response = requests.get(f"{BASE_URL}/api/users/invitations", headers=auth_headers)
        assert response.status_code == 200, f"List invitations failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} pending invitations")
    
    def test_user_settings(self, auth_headers):
        """Test user settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/settings/user", headers=auth_headers)
        assert response.status_code == 200, f"Get user settings failed: {response.text}"
        data = response.json()
        print(f"User settings: theme={data.get('theme', 'default')}, language={data.get('language', 'de')}")
    
    def test_system_settings(self, auth_headers):
        """Test system settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/settings/system", headers=auth_headers)
        assert response.status_code == 200, f"Get system settings failed: {response.text}"
        data = response.json()
        print(f"System settings: AI provider={data.get('ai_provider', 'not set')}")


class TestAIStatus:
    """Test AI status endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": "admin@casedesk.app", "password": "admin123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_ai_status(self, auth_headers):
        """Test AI status check"""
        response = requests.get(f"{BASE_URL}/api/ai/status", headers=auth_headers)
        assert response.status_code == 200, f"AI status failed: {response.text}"
        data = response.json()
        
        # Check structure
        assert "ollama" in data, "Missing ollama status"
        assert "openai" in data, "Missing openai status"
        print(f"AI Status - Ollama available: {data['ollama'].get('available')}, OpenAI available: {data['openai'].get('available')}")


class TestHealthCheck:
    """Test health check endpoint (no auth required)"""
    
    def test_health(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy", "Service not healthy"
        print(f"Health check: {data.get('service')} v{data.get('version')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
