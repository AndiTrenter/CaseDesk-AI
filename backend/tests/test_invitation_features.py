"""
CaseDesk AI - Invitation System and New Features Tests
Tests for: Theme toggle, User invitation system, AI assistant context
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://ai-task-assistant-5.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "admin@casedesk.app"
ADMIN_PASSWORD = "admin123"

class TestAuthAndSession:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"

    def test_get_current_user(self, auth_token):
        """Test getting current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", 
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL


class TestUserInvitationSystem:
    """Tests for user invitation workflow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_list_invitations(self, auth_token):
        """Test listing pending invitations"""
        response = requests.get(f"{BASE_URL}/api/users/invitations",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # There should be at least the testuser@example.com invitation
        print(f"Found {len(data)} pending invitations")
    
    def test_validate_existing_invitation(self):
        """Test validating the existing test invitation token"""
        test_token = "c35a6985a808ef75f4a0ef8d10800314b480518e88f11f2a23562328ecaec0d4"
        response = requests.get(f"{BASE_URL}/api/auth/invitation/{test_token}")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["email"] == "testuser@example.com"
        assert data["role"] == "user"
        assert data["invited_by"] == "admin@casedesk.app"
    
    def test_validate_invalid_invitation(self):
        """Test validating an invalid invitation token"""
        invalid_token = "invalid-token-12345"
        response = requests.get(f"{BASE_URL}/api/auth/invitation/{invalid_token}")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "error" in data
    
    def test_create_new_invitation(self, auth_token):
        """Test creating a new invitation"""
        unique_email = f"test_invite_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/users/invite",
            data={"email": unique_email, "role": "user"},
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "invitation_id" in data
        assert "invitation_url" in data
        assert "expires_at" in data
        # Email sent will be false if SMTP not configured (expected)
        print(f"Created invitation for {unique_email}, email_sent: {data.get('email_sent', False)}")
        return data["invitation_id"]
    
    def test_duplicate_invitation_rejected(self, auth_token):
        """Test that duplicate invitations are rejected"""
        # Try to invite an email that already has a pending invitation
        response = requests.post(f"{BASE_URL}/api/users/invite",
            data={"email": "testuser@example.com", "role": "user"},
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 400
        assert "existiert bereits" in response.json().get("detail", "").lower() or "already" in response.json().get("detail", "").lower()
    
    def test_list_users(self, auth_token):
        """Test listing all users (admin only)"""
        response = requests.get(f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least admin user
        # Verify admin user exists
        admin_user = next((u for u in data if u["email"] == ADMIN_EMAIL), None)
        assert admin_user is not None
        assert admin_user["role"] == "admin"
        print(f"Found {len(data)} users")


class TestUserSettings:
    """Tests for user settings including theme"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_user_settings(self, auth_token):
        """Test getting user settings"""
        response = requests.get(f"{BASE_URL}/api/settings/user",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        # Check expected fields
        assert "language" in data or "theme" in data or "user_id" in data
    
    def test_update_user_settings_theme(self, auth_token):
        """Test updating theme setting"""
        response = requests.put(f"{BASE_URL}/api/settings/user",
            data={"theme": "light"},
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Verify the change persisted
        get_response = requests.get(f"{BASE_URL}/api/settings/user",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert get_response.status_code == 200
        settings = get_response.json()
        assert settings.get("theme") == "light"
        
        # Reset to dark
        requests.put(f"{BASE_URL}/api/settings/user",
            data={"theme": "dark"},
            headers={"Authorization": f"Bearer {auth_token}"})
    
    def test_update_user_settings_language(self, auth_token):
        """Test updating language setting"""
        response = requests.put(f"{BASE_URL}/api/settings/user",
            data={"language": "de"},
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        assert response.json()["success"] == True


class TestAIChatWithContext:
    """Tests for AI chat with document context"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_ai_chat_endpoint(self, auth_token):
        """Test AI chat endpoint responds"""
        response = requests.post(f"{BASE_URL}/api/ai/chat",
            data={"message": "Hallo, was kannst du?"},
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should return success and response fields
        assert "success" in data
        assert "session_id" in data
        # Note: AI response depends on Ollama being available
        print(f"AI response success: {data.get('success')}")
        if data.get("response"):
            print(f"AI response (first 200 chars): {data['response'][:200]}")
    
    def test_ai_status(self, auth_token):
        """Test AI status endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai/status",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "configured_provider" in data
        assert "ollama" in data
        print(f"AI configured provider: {data.get('configured_provider')}")
        print(f"Ollama available: {data.get('ollama', {}).get('available')}")


class TestSystemSettings:
    """Tests for system settings (admin only)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_system_settings(self, auth_token):
        """Test getting system settings"""
        response = requests.get(f"{BASE_URL}/api/settings/system",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        # Should have AI provider and internet access settings
        assert "ai_provider" in data or "internet_access" in data or "setup_completed" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
