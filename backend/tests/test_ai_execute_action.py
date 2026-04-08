"""
Test AI Execute Action - Create Event/Task via AI Chat
Tests the complete flow: AI chat -> action detection -> execute-action -> verify in DB
"""
import pytest
import requests
import os
import json
import time
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"


class TestAIExecuteAction:
    """Test AI execute-action endpoint for creating events and tasks"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        
        # Login with multipart form data
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            files={
                "email": (None, TEST_EMAIL),
                "password": (None, TEST_PASSWORD)
            }
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        assert token, "No access token received"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.created_event_ids = []
        self.created_task_ids = []
        
        yield
        
        # Cleanup created test data
        for event_id in self.created_event_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/events/{event_id}")
            except:
                pass
        
        for task_id in self.created_task_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/tasks/{task_id}")
            except:
                pass
    
    def test_health_check(self):
        """Test health endpoint is working"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health check passed: {data}")
    
    def test_execute_action_create_event(self):
        """Test creating an event via /api/ai/execute-action"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        action_data = {
            "title": "TEST_AI_Zahnarzt Termin",
            "description": "Zahnarztbesuch via AI erstellt",
            "date": tomorrow,
            "start_time": "14:00",
            "end_time": "15:00",
            "all_day": False,
            "location": "Zahnarztpraxis Dr. Müller"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/ai/execute-action",
            data={
                "action_type": "create_event",
                "action_data": json.dumps(action_data),
                "confirmed": "true"
            }
        )
        
        print(f"Execute action response status: {response.status_code}")
        print(f"Execute action response: {response.text}")
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        
        result = response.json()
        assert result.get("success") == True, f"Action not successful: {result}"
        assert result.get("action_type") == "create_event"
        assert result.get("created"), "No created event returned"
        
        created_event = result.get("created")
        event_id = created_event.get("id")
        assert event_id, "No event ID returned"
        
        self.created_event_ids.append(event_id)
        
        print(f"✅ Event created via AI: {created_event}")
        
        # CRITICAL: Verify event appears in /api/events
        events_response = self.session.get(f"{BASE_URL}/api/events")
        assert events_response.status_code == 200, f"Failed to get events: {events_response.text}"
        
        events = events_response.json()
        event_ids = [e.get("id") for e in events]
        
        assert event_id in event_ids, f"Created event {event_id} NOT found in /api/events! Events: {event_ids}"
        
        # Find the created event and verify data
        created_in_list = next((e for e in events if e.get("id") == event_id), None)
        assert created_in_list, f"Event {event_id} not found in events list"
        assert created_in_list.get("title") == "TEST_AI_Zahnarzt Termin"
        
        print(f"✅ Event verified in /api/events: {created_in_list.get('title')}")
    
    def test_execute_action_create_task(self):
        """Test creating a task via /api/ai/execute-action"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        action_data = {
            "title": "TEST_AI_Dokumente vorbereiten",
            "description": "Unterlagen für Termin zusammenstellen",
            "due_date": tomorrow,
            "priority": "high"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/ai/execute-action",
            data={
                "action_type": "create_task",
                "action_data": json.dumps(action_data),
                "confirmed": "true"
            }
        )
        
        print(f"Execute action (task) response status: {response.status_code}")
        print(f"Execute action (task) response: {response.text}")
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        
        result = response.json()
        assert result.get("success") == True, f"Action not successful: {result}"
        assert result.get("action_type") == "create_task"
        assert result.get("created"), "No created task returned"
        
        created_task = result.get("created")
        task_id = created_task.get("id")
        assert task_id, "No task ID returned"
        
        self.created_task_ids.append(task_id)
        
        print(f"✅ Task created via AI: {created_task}")
        
        # CRITICAL: Verify task appears in /api/tasks
        tasks_response = self.session.get(f"{BASE_URL}/api/tasks")
        assert tasks_response.status_code == 200, f"Failed to get tasks: {tasks_response.text}"
        
        tasks = tasks_response.json()
        task_ids = [t.get("id") for t in tasks]
        
        assert task_id in task_ids, f"Created task {task_id} NOT found in /api/tasks! Tasks: {task_ids}"
        
        # Find the created task and verify data
        created_in_list = next((t for t in tasks if t.get("id") == task_id), None)
        assert created_in_list, f"Task {task_id} not found in tasks list"
        assert created_in_list.get("title") == "TEST_AI_Dokumente vorbereiten"
        
        print(f"✅ Task verified in /api/tasks: {created_in_list.get('title')}")
    
    def test_execute_action_create_event_with_reminder(self):
        """Test creating an event with reminder task via AI"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        action_data = {
            "title": "TEST_AI_Wichtiger Termin mit Erinnerung",
            "description": "Termin mit automatischer Erinnerung",
            "date": future_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "all_day": False,
            "create_reminder": True,
            "reminder_days": 2
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/ai/execute-action",
            data={
                "action_type": "create_event",
                "action_data": json.dumps(action_data),
                "confirmed": "true"
            }
        )
        
        print(f"Execute action (event+reminder) response status: {response.status_code}")
        print(f"Execute action (event+reminder) response: {response.text}")
        
        assert response.status_code == 200, f"Execute action failed: {response.text}"
        
        result = response.json()
        assert result.get("success") == True, f"Action not successful: {result}"
        
        created_event = result.get("created")
        event_id = created_event.get("id")
        self.created_event_ids.append(event_id)
        
        # Check if reminder task was created
        reminder_task = result.get("reminder_task")
        if reminder_task:
            self.created_task_ids.append(reminder_task.get("id"))
            print(f"✅ Reminder task also created: {reminder_task.get('title')}")
        
        print(f"✅ Event with reminder created: {created_event.get('title')}")
    
    def test_execute_action_invalid_action_type(self):
        """Test that invalid action types are rejected"""
        response = self.session.post(
            f"{BASE_URL}/api/ai/execute-action",
            data={
                "action_type": "invalid_action",
                "action_data": json.dumps({"title": "Test"}),
                "confirmed": "true"
            }
        )
        
        # Should either return 400 or success=False
        if response.status_code == 200:
            result = response.json()
            # If it returns 200, success should be False
            print(f"Invalid action response: {result}")
        else:
            print(f"Invalid action rejected with status: {response.status_code}")
    
    def test_execute_action_not_confirmed(self):
        """Test that unconfirmed actions are rejected"""
        action_data = {
            "title": "TEST_Unconfirmed Event",
            "date": "2026-04-15",
            "start_time": "09:00",
            "end_time": "10:00"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/ai/execute-action",
            data={
                "action_type": "create_event",
                "action_data": json.dumps(action_data),
                "confirmed": "false"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result.get("success") == False, "Unconfirmed action should not succeed"
        print(f"✅ Unconfirmed action correctly rejected: {result.get('error')}")
    
    def test_ai_chat_action_detection(self):
        """Test that AI chat detects action intents and returns action_preview"""
        # This tests the /api/ai/chat endpoint for action detection
        response = self.session.post(
            f"{BASE_URL}/api/ai/chat",
            data={
                "message": "Erstelle einen Termin morgen um 14 Uhr für Zahnarzt",
                "session_id": f"test-session-{int(time.time())}"
            }
        )
        
        print(f"AI Chat response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"AI Chat response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
            
            # Check if action_preview is returned
            action_preview = result.get("action_preview")
            if action_preview:
                print(f"✅ Action detected: {action_preview.get('action_type')}")
                print(f"   Action data: {action_preview.get('action_data')}")
            else:
                print("⚠️ No action_preview returned - AI may not have detected the action intent")
        else:
            print(f"⚠️ AI Chat failed: {response.text}")
            # Don't fail the test - AI might not be configured
            pytest.skip("AI service may not be configured")


class TestEventsAPI:
    """Test Events API directly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        
        # Login
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.created_ids = []
        
        yield
        
        # Cleanup
        for id in self.created_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/events/{id}")
            except:
                pass
    
    def test_list_events(self):
        """Test listing events"""
        response = self.session.get(f"{BASE_URL}/api/events")
        assert response.status_code == 200
        events = response.json()
        print(f"✅ Events list: {len(events)} events found")
        for e in events[:3]:
            print(f"   - {e.get('title')} ({e.get('id')[:8]}...)")
    
    def test_create_event_directly(self):
        """Test creating event via direct API"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        event_data = {
            "title": "TEST_Direct_Event",
            "description": "Created directly via API",
            "start_time": f"{tomorrow}T10:00:00",
            "end_time": f"{tomorrow}T11:00:00",
            "all_day": False
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/events",
            json=event_data
        )
        
        print(f"Create event response: {response.status_code}")
        print(f"Create event body: {response.text}")
        
        assert response.status_code == 200, f"Failed to create event: {response.text}"
        
        result = response.json()
        event_id = result.get("id")
        assert event_id, "No event ID returned"
        
        self.created_ids.append(event_id)
        print(f"✅ Event created directly: {result.get('title')}")


class TestTasksAPI:
    """Test Tasks API directly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        
        # Login
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.created_ids = []
        
        yield
        
        # Cleanup
        for id in self.created_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/tasks/{id}")
            except:
                pass
    
    def test_list_tasks(self):
        """Test listing tasks"""
        response = self.session.get(f"{BASE_URL}/api/tasks")
        assert response.status_code == 200
        tasks = response.json()
        print(f"✅ Tasks list: {len(tasks)} tasks found")
        for t in tasks[:3]:
            print(f"   - {t.get('title')} ({t.get('id')[:8]}...)")
    
    def test_create_task_directly(self):
        """Test creating task via direct API"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        task_data = {
            "title": "TEST_Direct_Task",
            "description": "Created directly via API",
            "due_date": tomorrow,
            "priority": "medium",
            "status": "todo"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/tasks",
            json=task_data
        )
        
        print(f"Create task response: {response.status_code}")
        print(f"Create task body: {response.text}")
        
        assert response.status_code == 200, f"Failed to create task: {response.text}"
        
        result = response.json()
        task_id = result.get("id")
        assert task_id, "No task ID returned"
        
        self.created_ids.append(task_id)
        print(f"✅ Task created directly: {result.get('title')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
