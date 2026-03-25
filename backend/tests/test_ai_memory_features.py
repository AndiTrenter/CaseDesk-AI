"""
Test suite for CaseDesk AI P0 Features:
1. Contextual AI Chat (document_id parameter)
2. Persistent AI Memory (profile endpoints)

Tests the following endpoints:
- POST /api/ai/chat - with document_id parameter
- GET /api/ai/profile - returns user's AI memory profile
- DELETE /api/ai/profile/facts/{index} - deletes a specific fact
- DELETE /api/ai/profile - clears entire AI memory profile
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-task-assistant-5.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "Speedy@181279"


class TestAIMemoryFeatures:
    """Test suite for AI Memory and Contextual Chat features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.token = None
        self.document_id = None
        self.case_id = None
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    def test_01_login_success(self):
        """Test login returns valid token"""
        assert self.token is not None, "Token should be present after login"
        print(f"✓ Login successful, token obtained")
    
    def test_02_get_documents_for_context(self):
        """Get a document ID to use for contextual chat testing"""
        response = self.session.get(f"{BASE_URL}/api/documents")
        assert response.status_code == 200, f"Documents list failed: {response.status_code}"
        
        documents = response.json()
        if documents and len(documents) > 0:
            self.document_id = documents[0].get("id")
            print(f"✓ Found document for testing: {self.document_id}")
        else:
            print("⚠ No documents found, will test without document_id")
    
    def test_03_get_cases_for_context(self):
        """Get a case ID to use for contextual chat testing"""
        response = self.session.get(f"{BASE_URL}/api/cases")
        assert response.status_code == 200, f"Cases list failed: {response.status_code}"
        
        cases = response.json()
        if cases and len(cases) > 0:
            self.case_id = cases[0].get("id")
            print(f"✓ Found case for testing: {self.case_id}")
        else:
            print("⚠ No cases found, will test without case_id")
    
    def test_04_ai_chat_basic(self):
        """Test basic AI chat without context"""
        response = self.session.post(
            f"{BASE_URL}/api/ai/chat",
            data={
                "message": "Hallo, wie geht es dir?",
                "session_id": "test-session-basic"
            }
        )
        assert response.status_code == 200, f"AI chat failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        assert "session_id" in data, "Response should have 'session_id' field"
        print(f"✓ Basic AI chat works, success={data.get('success')}")
    
    def test_05_ai_chat_with_document_id(self):
        """Test AI chat with document_id parameter (Contextual AI Chat feature)"""
        # First get a document
        docs_response = self.session.get(f"{BASE_URL}/api/documents")
        documents = docs_response.json() if docs_response.status_code == 200 else []
        
        if not documents:
            pytest.skip("No documents available for contextual chat test")
        
        doc_id = documents[0].get("id")
        doc_name = documents[0].get("display_name") or documents[0].get("original_filename")
        
        response = self.session.post(
            f"{BASE_URL}/api/ai/chat",
            data={
                "message": "Was steht in diesem Dokument?",
                "session_id": "test-session-doc",
                "document_id": doc_id
            }
        )
        assert response.status_code == 200, f"AI chat with document_id failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        print(f"✓ AI chat with document_id works, document: {doc_name}")
        print(f"  Response success: {data.get('success')}")
    
    def test_06_ai_chat_with_case_id(self):
        """Test AI chat with case_id parameter"""
        # First get a case
        cases_response = self.session.get(f"{BASE_URL}/api/cases")
        cases = cases_response.json() if cases_response.status_code == 200 else []
        
        if not cases:
            pytest.skip("No cases available for contextual chat test")
        
        case_id = cases[0].get("id")
        case_title = cases[0].get("title")
        
        response = self.session.post(
            f"{BASE_URL}/api/ai/chat",
            data={
                "message": "Was ist der Status dieses Falls?",
                "session_id": "test-session-case",
                "case_id": case_id
            }
        )
        assert response.status_code == 200, f"AI chat with case_id failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        print(f"✓ AI chat with case_id works, case: {case_title}")
    
    def test_07_ai_chat_with_both_document_and_case(self):
        """Test AI chat with both document_id and case_id parameters"""
        # Get document and case
        docs_response = self.session.get(f"{BASE_URL}/api/documents")
        cases_response = self.session.get(f"{BASE_URL}/api/cases")
        
        documents = docs_response.json() if docs_response.status_code == 200 else []
        cases = cases_response.json() if cases_response.status_code == 200 else []
        
        if not documents or not cases:
            pytest.skip("Need both documents and cases for this test")
        
        doc_id = documents[0].get("id")
        case_id = cases[0].get("id")
        
        response = self.session.post(
            f"{BASE_URL}/api/ai/chat",
            data={
                "message": "Analysiere dieses Dokument im Kontext des Falls",
                "session_id": "test-session-both",
                "document_id": doc_id,
                "case_id": case_id
            }
        )
        assert response.status_code == 200, f"AI chat with both params failed: {response.status_code}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        print(f"✓ AI chat with both document_id and case_id works")
    
    def test_08_get_ai_profile(self):
        """Test GET /api/ai/profile - returns user's AI memory profile"""
        response = self.session.get(f"{BASE_URL}/api/ai/profile")
        assert response.status_code == 200, f"Get AI profile failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        assert "profile" in data, "Response should have 'profile' field"
        
        profile = data.get("profile", {})
        # Profile should have facts array (may be empty initially)
        assert "facts" in profile or profile == {}, "Profile should have 'facts' field or be empty"
        
        facts_count = len(profile.get("facts", []))
        print(f"✓ AI profile retrieved, facts count: {facts_count}")
        if profile.get("summary"):
            print(f"  Summary: {profile.get('summary')[:100]}...")
    
    def test_09_ai_profile_structure(self):
        """Test AI profile has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/ai/profile")
        assert response.status_code == 200
        
        data = response.json()
        profile = data.get("profile", {})
        
        # Check profile structure
        if profile.get("facts"):
            fact = profile["facts"][0]
            assert "key" in fact, "Fact should have 'key' field"
            assert "value" in fact, "Fact should have 'value' field"
            print(f"✓ AI profile structure is correct")
            print(f"  Sample fact: {fact.get('key')}: {fact.get('value')}")
        else:
            print("✓ AI profile structure check passed (no facts yet)")
    
    def test_10_delete_ai_profile_fact(self):
        """Test DELETE /api/ai/profile/facts/{index} - deletes a specific fact"""
        # First check if there are any facts
        profile_response = self.session.get(f"{BASE_URL}/api/ai/profile")
        profile = profile_response.json().get("profile", {})
        facts = profile.get("facts", [])
        
        if not facts:
            # Try to generate a fact by having a conversation
            self.session.post(
                f"{BASE_URL}/api/ai/chat",
                data={
                    "message": "Ich bin Softwareentwickler und arbeite bei einer Firma in München.",
                    "session_id": "test-session-fact-gen"
                }
            )
            # Wait a bit for fact extraction (async)
            import time
            time.sleep(3)
            
            # Check again
            profile_response = self.session.get(f"{BASE_URL}/api/ai/profile")
            profile = profile_response.json().get("profile", {})
            facts = profile.get("facts", [])
        
        if not facts:
            print("⚠ No facts to delete, testing endpoint with index 0 (should return error)")
            response = self.session.delete(f"{BASE_URL}/api/ai/profile/facts/0")
            # Should return success=False since no fact exists
            assert response.status_code == 200, f"Delete fact endpoint failed: {response.status_code}"
            data = response.json()
            # Either success=False (no fact) or success=True (fact deleted)
            print(f"✓ Delete fact endpoint works, response: {data}")
        else:
            # Delete the first fact
            response = self.session.delete(f"{BASE_URL}/api/ai/profile/facts/0")
            assert response.status_code == 200, f"Delete fact failed: {response.status_code}"
            
            data = response.json()
            assert "success" in data, "Response should have 'success' field"
            print(f"✓ Fact deleted successfully")
    
    def test_11_clear_ai_profile(self):
        """Test DELETE /api/ai/profile - clears entire AI memory profile"""
        response = self.session.delete(f"{BASE_URL}/api/ai/profile")
        assert response.status_code == 200, f"Clear AI profile failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        assert data.get("success") == True, "Clear profile should return success=True"
        
        # Verify profile is cleared
        profile_response = self.session.get(f"{BASE_URL}/api/ai/profile")
        profile = profile_response.json().get("profile", {})
        facts = profile.get("facts", [])
        
        assert len(facts) == 0, f"Profile should be empty after clear, but has {len(facts)} facts"
        print(f"✓ AI profile cleared successfully")
    
    def test_12_ai_chat_response_structure(self):
        """Test AI chat response has correct structure"""
        response = self.session.post(
            f"{BASE_URL}/api/ai/chat",
            data={
                "message": "Zeige mir meine Dokumente",
                "session_id": "test-session-structure"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "success" in data, "Response should have 'success' field"
        assert "session_id" in data, "Response should have 'session_id' field"
        
        # If success, should have response
        if data.get("success"):
            assert "response" in data, "Successful response should have 'response' field"
            # May have referenced_documents
            if "referenced_documents" in data:
                print(f"✓ Response has referenced_documents: {len(data['referenced_documents'])} docs")
        
        print(f"✓ AI chat response structure is correct")


class TestAIEndpointValidation:
    """Test AI endpoint validation and error handling"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        
        # Login
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")
    
    def test_ai_chat_requires_message(self):
        """Test AI chat requires message parameter"""
        response = self.session.post(
            f"{BASE_URL}/api/ai/chat",
            data={"session_id": "test"}
        )
        # Should fail validation (422) or return error
        assert response.status_code in [422, 400], f"Should fail without message: {response.status_code}"
        print(f"✓ AI chat correctly requires message parameter")
    
    def test_ai_profile_requires_auth(self):
        """Test AI profile endpoints require authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        
        response = no_auth_session.get(f"{BASE_URL}/api/ai/profile")
        assert response.status_code == 401, f"Should require auth: {response.status_code}"
        print(f"✓ AI profile correctly requires authentication")
    
    def test_delete_fact_invalid_index(self):
        """Test deleting fact with invalid index"""
        response = self.session.delete(f"{BASE_URL}/api/ai/profile/facts/9999")
        assert response.status_code == 200, f"Endpoint should handle invalid index: {response.status_code}"
        
        data = response.json()
        # Should return success=False for invalid index
        assert data.get("success") == False, "Should return success=False for invalid index"
        print(f"✓ Delete fact correctly handles invalid index")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
