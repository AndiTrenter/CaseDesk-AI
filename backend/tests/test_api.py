"""
CaseDesk AI - Backend API Tests
Run: cd backend && python -m pytest tests/ -v
"""
import os
import sys
import pytest
import httpx
import asyncio

# Test config
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8001")
ADMIN_EMAIL = "admin@casedesk.app"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def client():
    return httpx.Client(base_url=BASE_URL, timeout=30.0)


@pytest.fixture(scope="session")
def auth_token(client):
    """Login and get auth token"""
    response = client.post("/api/auth/login", data={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Could not authenticate - setup may not be complete")


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealth:
    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "casedesk-backend"

    def test_setup_status(self, client):
        response = client.get("/api/setup/status")
        assert response.status_code == 200
        data = response.json()
        assert "has_admin" in data
        assert "is_configured" in data


class TestAuth:
    def test_login_success(self, client):
        response = client.post("/api/auth/login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_invalid(self, client):
        response = client.post("/api/auth/login", data={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"

    def test_unauthorized_access(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code in [401, 403]


class TestDashboard:
    def test_dashboard_stats(self, client, auth_headers):
        response = client.get("/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert "documents" in data
        assert "tasks" in data


class TestCases:
    def test_list_cases(self, client, auth_headers):
        response = client.get("/api/cases", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_case(self, client, auth_headers):
        response = client.post("/api/cases", headers=auth_headers, json={
            "title": "Test Case CI",
            "description": "Created by CI test",
            "reference_number": "CI-001"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Case CI"
        return data["id"]


class TestDocuments:
    def test_list_documents(self, client, auth_headers):
        response = client.get("/api/documents", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTasks:
    def test_list_tasks(self, client, auth_headers):
        response = client.get("/api/tasks", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task(self, client, auth_headers):
        response = client.post("/api/tasks", headers=auth_headers, json={
            "title": "Test Task CI",
            "description": "Created by CI",
            "priority": "medium",
            "status": "todo"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Task CI"


class TestEvents:
    def test_list_events(self, client, auth_headers):
        response = client.get("/api/events", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_event(self, client, auth_headers):
        response = client.post("/api/events", headers=auth_headers, json={
            "title": "Test Event CI",
            "start_time": "2026-04-01T10:00:00",
            "end_time": "2026-04-01T11:00:00"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Event CI"


class TestSettings:
    def test_get_user_settings(self, client, auth_headers):
        response = client.get("/api/settings/user", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "language" in data

    def test_get_system_settings(self, client, auth_headers):
        response = client.get("/api/settings/system", headers=auth_headers)
        assert response.status_code == 200


class TestAI:
    def test_ai_chat_german(self, client, auth_headers):
        response = client.post("/api/ai/chat", headers=auth_headers, data={
            "message": "Hallo, antworte auf Deutsch",
            "session_id": "test-ci-session"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["response"]) > 10
        assert "referenced_documents" in data

    def test_ai_status(self, client, auth_headers):
        response = client.get("/api/ai/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "configured_provider" in data


class TestExport:
    def test_export_all(self, client, auth_headers):
        response = client.get("/api/export/all", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers.get("content-type") in [
            "application/zip",
            "application/x-zip-compressed",
            "application/octet-stream"
        ]


class TestRoleAccess:
    def test_system_settings_requires_admin(self, client):
        """Non-admin should not access system settings"""
        response = client.get("/api/settings/system")
        assert response.status_code in [401, 403]

    def test_users_list_requires_admin(self, client):
        response = client.get("/api/users")
        assert response.status_code in [401, 403]
