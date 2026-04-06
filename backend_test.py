#!/usr/bin/env python3
"""
CaseDesk AI v1.0.5 Backend Testing
Test new features: Events Reminders, Document Download Tokens, AI Combined Actions
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://task-portal-fix.preview.emergentagent.com/api"

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class CaseDeskTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    async def setup_system_if_needed(self) -> bool:
        """Setup system if not configured"""
        try:
            # Check setup status
            async with self.session.get(f"{BACKEND_URL}/setup/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("is_configured"):
                        return True  # Already configured
                    
                    # Need to setup
                    self.log_result("System Setup", True, "System needs initial setup")
                    
                    # Initialize setup
                    form_data = aiohttp.FormData()
                    form_data.add_field('admin_email', TEST_EMAIL)
                    form_data.add_field('admin_username', 'admin')
                    form_data.add_field('admin_password', TEST_PASSWORD)
                    form_data.add_field('admin_full_name', 'Test Admin')
                    form_data.add_field('language', 'de')
                    form_data.add_field('ai_provider', 'ollama')
                    form_data.add_field('internet_access', 'denied')
                    form_data.add_field('organization_name', 'CaseDesk Test')
                    
                    async with self.session.post(f"{BACKEND_URL}/setup/init", data=form_data) as setup_resp:
                        if setup_resp.status == 200:
                            setup_data = await setup_resp.json()
                            self.auth_token = setup_data.get("access_token")
                            self.user_id = setup_data.get("user", {}).get("id")
                            self.log_result("System Setup", True, "System initialized successfully")
                            return True
                        else:
                            error_text = await setup_resp.text()
                            self.log_result("System Setup", False, f"Setup failed: {setup_resp.status}", error_text)
                            return False
                else:
                    error_text = await resp.text()
                    self.log_result("System Setup", False, f"Status check failed: {resp.status}", error_text)
                    return False
        except Exception as e:
            self.log_result("System Setup", False, f"Setup error: {str(e)}")
            return False

    async def authenticate(self) -> bool:
        """Authenticate with test credentials"""
        try:
            # Use form data for login
            form_data = aiohttp.FormData()
            form_data.add_field('email', TEST_EMAIL)
            form_data.add_field('password', TEST_PASSWORD)
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", data=form_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get("access_token")
                    self.user_id = data.get("user", {}).get("id")
                    self.log_result("Authentication", True, f"Logged in as {TEST_EMAIL}")
                    return True
                else:
                    error_text = await resp.text()
                    self.log_result("Authentication", False, f"Login failed: {resp.status}", error_text)
                    return False
        except Exception as e:
            self.log_result("Authentication", False, f"Login error: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    async def test_events_reminder_options(self) -> bool:
        """Test GET /api/events/reminder-options"""
        try:
            async with self.session.get(f"{BACKEND_URL}/events/reminder-options", headers=self.get_headers()) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    options = data.get("options", [])
                    
                    # Check for expected reminder options
                    expected_values = ["none", "5_min", "15_min", "30_min", "1_hour", "1_day", "1_week", "2_weeks"]
                    found_values = [opt.get("value") for opt in options]
                    
                    missing = [val for val in expected_values if val not in found_values]
                    if missing:
                        self.log_result("Events Reminder Options", False, f"Missing options: {missing}", data)
                        return False
                    
                    self.log_result("Events Reminder Options", True, f"Found {len(options)} reminder options", options)
                    return True
                else:
                    error_text = await resp.text()
                    self.log_result("Events Reminder Options", False, f"HTTP {resp.status}", error_text)
                    return False
        except Exception as e:
            self.log_result("Events Reminder Options", False, f"Request error: {str(e)}")
            return False
    
    async def test_events_with_reminders(self) -> tuple[bool, Optional[str]]:
        """Test POST /api/events with reminder settings"""
        try:
            # Create event with reminder
            event_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            event_data = {
                "title": "Test Event with Reminder",
                "description": "Testing v1.0.5 reminder functionality",
                "start_time": f"{event_date}T14:00:00",
                "end_time": f"{event_date}T15:00:00",
                "all_day": False,
                "reminder_enabled": True,
                "reminder_type": "1_day",
                "reminder_channels": ["app"]
            }
            
            async with self.session.post(f"{BACKEND_URL}/events", json=event_data, headers=self.get_headers()) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    event_id = data.get("id")
                    
                    # Verify reminder settings in response
                    if not data.get("reminder_enabled"):
                        self.log_result("Events with Reminders", False, "reminder_enabled not set", data)
                        return False, None
                    
                    if data.get("reminder_type") != "1_day":
                        self.log_result("Events with Reminders", False, "reminder_type incorrect", data)
                        return False, None
                    
                    if data.get("reminder_minutes") != 1440:  # 1 day = 1440 minutes
                        self.log_result("Events with Reminders", False, "reminder_minutes incorrect", data)
                        return False, None
                    
                    self.log_result("Events with Reminders", True, f"Event created with reminder: {event_id}", {
                        "event_id": event_id,
                        "reminder_enabled": data.get("reminder_enabled"),
                        "reminder_type": data.get("reminder_type"),
                        "reminder_minutes": data.get("reminder_minutes")
                    })
                    return True, event_id
                else:
                    error_text = await resp.text()
                    self.log_result("Events with Reminders", False, f"HTTP {resp.status}", error_text)
                    return False, None
        except Exception as e:
            self.log_result("Events with Reminders", False, f"Request error: {str(e)}")
            return False, None
    
    async def test_document_upload_and_tokens(self) -> tuple[bool, Optional[str]]:
        """Test document upload and token-based access"""
        try:
            # Create a test document (simple text file)
            test_content = b"This is a test document for v1.0.5 token testing."
            
            # Upload document
            form_data = aiohttp.FormData()
            form_data.add_field('file', test_content, filename='test_v1.0.5.txt', content_type='text/plain')
            form_data.add_field('document_type', 'other')
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/documents/upload", data=form_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if not data.get("success"):
                        self.log_result("Document Upload", False, "Upload not successful", data)
                        return False, None
                    
                    document_id = data.get("document", {}).get("id")
                    if not document_id:
                        self.log_result("Document Upload", False, "No document ID returned", data)
                        return False, None
                    
                    self.log_result("Document Upload", True, f"Document uploaded: {document_id}")
                    return True, document_id
                else:
                    error_text = await resp.text()
                    self.log_result("Document Upload", False, f"HTTP {resp.status}", error_text)
                    return False, None
        except Exception as e:
            self.log_result("Document Upload", False, f"Request error: {str(e)}")
            return False, None
    
    async def test_document_download_token(self, document_id: str) -> tuple[bool, Optional[str]]:
        """Test GET /api/documents/{id}/download-token"""
        try:
            async with self.session.get(f"{BACKEND_URL}/documents/{document_id}/download-token", headers=self.get_headers()) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get("token")
                    expires_in = data.get("expires_in")
                    
                    if not token:
                        self.log_result("Document Download Token", False, "No token returned", data)
                        return False, None
                    
                    if expires_in != 300:  # 5 minutes = 300 seconds
                        self.log_result("Document Download Token", False, f"Unexpected expires_in: {expires_in}", data)
                        return False, None
                    
                    self.log_result("Document Download Token", True, f"Token generated, expires in {expires_in}s", {
                        "token_length": len(token),
                        "expires_in": expires_in
                    })
                    return True, token
                else:
                    error_text = await resp.text()
                    self.log_result("Document Download Token", False, f"HTTP {resp.status}", error_text)
                    return False, None
        except Exception as e:
            self.log_result("Document Download Token", False, f"Request error: {str(e)}")
            return False, None
    
    async def test_document_view_with_token(self, document_id: str, token: str) -> bool:
        """Test GET /api/documents/{id}/view?token={token}"""
        try:
            # Test without auth header (token should be sufficient)
            async with self.session.get(f"{BACKEND_URL}/documents/{document_id}/view?token={token}") as resp:
                if resp.status == 200:
                    content = await resp.read()
                    content_type = resp.headers.get('content-type', '')
                    
                    # Verify we got the document content
                    if b"This is a test document for v1.0.5 token testing." in content:
                        self.log_result("Document View with Token", True, f"Document accessed via token", {
                            "content_length": len(content),
                            "content_type": content_type
                        })
                        return True
                    else:
                        self.log_result("Document View with Token", False, "Unexpected content", {
                            "content_preview": content[:100].decode('utf-8', errors='ignore')
                        })
                        return False
                else:
                    error_text = await resp.text()
                    self.log_result("Document View with Token", False, f"HTTP {resp.status}", error_text)
                    return False
        except Exception as e:
            self.log_result("Document View with Token", False, f"Request error: {str(e)}")
            return False
    
    async def test_ai_parse_combined_action(self) -> tuple[bool, Optional[dict]]:
        """Test POST /api/ai/parse-action for combined event/task creation"""
        try:
            # German message requesting combined event + task + reminder
            message = "Erstelle mir am 26.4.2026 einen Kalendereintrag 'Luzia Geburtstag' mit einer Erinnerung 1 Woche vorher und trage gleichzeitig als Aufgabe 'Kuchen kaufen' ein"
            
            form_data = aiohttp.FormData()
            form_data.add_field('message', message)
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/ai/parse-action", data=form_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if not data.get("success"):
                        self.log_result("AI Parse Combined Action", False, "Parse not successful", data)
                        return False, None
                    
                    if not data.get("action_detected"):
                        self.log_result("AI Parse Combined Action", False, "No action detected", data)
                        return False, None
                    
                    action_type = data.get("action_type")
                    if action_type != "combined_event_task":
                        self.log_result("AI Parse Combined Action", False, f"Wrong action type: {action_type}", data)
                        return False, None
                    
                    action_data = data.get("action_data", {})
                    
                    # Verify structure contains event, tasks, and reminder
                    if "event" not in action_data:
                        self.log_result("AI Parse Combined Action", False, "Missing event data", data)
                        return False, None
                    
                    if "tasks" not in action_data:
                        self.log_result("AI Parse Combined Action", False, "Missing tasks data", data)
                        return False, None
                    
                    if "reminder" not in action_data:
                        self.log_result("AI Parse Combined Action", False, "Missing reminder data", data)
                        return False, None
                    
                    self.log_result("AI Parse Combined Action", True, f"Combined action parsed successfully", {
                        "action_type": action_type,
                        "event_title": action_data.get("event", {}).get("title"),
                        "tasks_count": len(action_data.get("tasks", [])),
                        "reminder_enabled": action_data.get("reminder", {}).get("enabled")
                    })
                    return True, action_data
                else:
                    error_text = await resp.text()
                    self.log_result("AI Parse Combined Action", False, f"HTTP {resp.status}", error_text)
                    return False, None
        except Exception as e:
            self.log_result("AI Parse Combined Action", False, f"Request error: {str(e)}")
            return False, None
    
    async def test_ai_execute_combined_action(self, action_data: dict) -> bool:
        """Test POST /api/ai/execute-action for combined event/task creation"""
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('action_type', 'combined_event_task')
            form_data.add_field('action_data', json.dumps(action_data))
            form_data.add_field('confirmed', 'true')
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/ai/execute-action", data=form_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if not data.get("success"):
                        self.log_result("AI Execute Combined Action", False, "Execution not successful", data)
                        return False
                    
                    if data.get("action_type") != "combined_event_task":
                        self.log_result("AI Execute Combined Action", False, "Wrong action type in response", data)
                        return False
                    
                    created = data.get("created", {})
                    
                    # Verify event was created
                    if not created.get("event"):
                        self.log_result("AI Execute Combined Action", False, "No event created", data)
                        return False
                    
                    # Verify tasks were created
                    if not created.get("tasks"):
                        self.log_result("AI Execute Combined Action", False, "No tasks created", data)
                        return False
                    
                    # Verify reminder was created (if enabled)
                    reminder_data = action_data.get("reminder", {})
                    if reminder_data.get("enabled") and not created.get("reminder"):
                        self.log_result("AI Execute Combined Action", False, "No reminder created despite being enabled", data)
                        return False
                    
                    self.log_result("AI Execute Combined Action", True, "Combined action executed successfully", {
                        "event_id": created.get("event", {}).get("id"),
                        "tasks_created": len(created.get("tasks", [])),
                        "reminder_created": bool(created.get("reminder")),
                        "message": data.get("message")
                    })
                    return True
                else:
                    error_text = await resp.text()
                    self.log_result("AI Execute Combined Action", False, f"HTTP {resp.status}", error_text)
                    return False
        except Exception as e:
            self.log_result("AI Execute Combined Action", False, f"Request error: {str(e)}")
            return False
    
    async def test_system_version(self) -> bool:
        """Test GET /api/system/version should return 1.0.5"""
        try:
            async with self.session.get(f"{BACKEND_URL}/system/version", headers=self.get_headers()) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    version = data.get("version")
                    
                    if version != "1.0.5":
                        self.log_result("System Version", False, f"Expected v1.0.5, got {version}", data)
                        return False
                    
                    self.log_result("System Version", True, f"Version {version} confirmed", data)
                    return True
                else:
                    error_text = await resp.text()
                    self.log_result("System Version", False, f"HTTP {resp.status}", error_text)
                    return False
        except Exception as e:
            self.log_result("System Version", False, f"Request error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all v1.0.5 tests"""
        print("🚀 Starting CaseDesk AI v1.0.5 Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_EMAIL}")
        print("-" * 60)
        
        # Setup system if needed, then authenticate
        if not await self.setup_system_if_needed():
            print("❌ System setup failed - cannot continue with tests")
            return
        
        if not self.auth_token:  # If not already authenticated from setup
            if not await self.authenticate():
                print("❌ Authentication failed - cannot continue with tests")
                return
        
        # Test 1: Events Reminder Options
        await self.test_events_reminder_options()
        
        # Test 2: Events with Reminders
        event_success, event_id = await self.test_events_with_reminders()
        
        # Test 3: Document Upload and Tokens
        doc_success, document_id = await self.test_document_upload_and_tokens()
        
        if doc_success and document_id:
            # Test 4: Document Download Token
            token_success, token = await self.test_document_download_token(document_id)
            
            if token_success and token:
                # Test 5: Document View with Token
                await self.test_document_view_with_token(document_id, token)
        
        # Test 6: AI Combined Action Parse
        parse_success, action_data = await self.test_ai_parse_combined_action()
        
        if parse_success and action_data:
            # Test 7: AI Combined Action Execute
            await self.test_ai_execute_combined_action(action_data)
        
        # Test 8: System Version
        await self.test_system_version()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

async def main():
    """Main test runner"""
    async with CaseDeskTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())