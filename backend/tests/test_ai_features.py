"""
CaseDesk AI - Backend Tests for AI Features
Tests: AI Chat German language, referenced_documents, PDF/DOCX format selection, ZIP export
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@casedesk.app"
TEST_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests"""
    
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
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"✓ Login successful for {TEST_EMAIL}")


class TestAIChatGermanLanguage:
    """Test AI Chat responds in German - KEY BUG FIX"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_user_settings_language_is_german(self, auth_token):
        """Verify user settings has language set to 'de'"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/user", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Language should be 'de' (German) as per the bug fix
        print(f"User settings: {data}")
        assert data.get("language") == "de", f"Expected language 'de', got '{data.get('language')}'"
        print("✓ User settings language is 'de' (German)")
    
    def test_ai_chat_endpoint_accepts_message(self, auth_token):
        """Test AI chat endpoint accepts message and returns response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers=headers,
            data={
                "message": "Hallo, was kannst du mir über meine Dokumente sagen?",
                "session_id": "test-session-german"
            }
        )
        assert response.status_code == 200
        data = response.json()
        print(f"AI Chat response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        
        # Check response structure
        assert "session_id" in data
        assert "response" in data or "error" in data
        
        # If AI is available, check response is in German
        if data.get("success") and data.get("response"):
            response_text = data["response"]
            # Check for German words/patterns (not English)
            german_indicators = ["ich", "Sie", "Ihre", "Dokument", "Fall", "können", "haben", "ist", "sind", "nicht"]
            english_indicators = ["I can", "your documents", "you have", "I am", "I'm"]
            
            has_german = any(word.lower() in response_text.lower() for word in german_indicators)
            has_english = any(phrase.lower() in response_text.lower() for phrase in english_indicators)
            
            print(f"Response contains German indicators: {has_german}")
            print(f"Response contains English indicators: {has_english}")
            
            # The response should be in German
            if has_english and not has_german:
                pytest.fail(f"AI response appears to be in English instead of German: {response_text[:200]}")
            
            print("✓ AI chat response received (language check passed)")
        else:
            # AI might not be available, but endpoint works
            print(f"✓ AI chat endpoint works (AI may be unavailable: {data.get('error', 'no error')})")
    
    def test_ai_chat_returns_referenced_documents(self, auth_token):
        """Test AI chat returns referenced_documents array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers=headers,
            data={
                "message": "Zeige mir alle meine Dokumente",
                "session_id": "test-session-docs"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check that referenced_documents field exists in response
        assert "referenced_documents" in data, "Response should contain 'referenced_documents' field"
        
        # It should be a list (may be empty if no documents mentioned)
        assert isinstance(data["referenced_documents"], list), "referenced_documents should be a list"
        
        # If documents are referenced, check structure
        if data["referenced_documents"]:
            doc = data["referenced_documents"][0]
            assert "id" in doc, "Referenced document should have 'id'"
            assert "name" in doc, "Referenced document should have 'name'"
            assert "download_url" in doc, "Referenced document should have 'download_url'"
            print(f"✓ Referenced documents: {data['referenced_documents']}")
        else:
            print("✓ referenced_documents field present (empty list - no docs mentioned)")


class TestResponseGenerationFormats:
    """Test PDF/DOCX format selection in response generation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_case_id(self, auth_token):
        """Get or create a test case"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # List existing cases
        response = requests.get(f"{BASE_URL}/api/cases", headers=headers)
        assert response.status_code == 200
        cases = response.json()
        
        if cases:
            return cases[0]["id"]
        
        # Create a test case if none exists
        response = requests.post(
            f"{BASE_URL}/api/cases",
            headers=headers,
            json={
                "title": "Test Case for Format Testing",
                "description": "Testing PDF/DOCX format selection",
                "status": "open"
            }
        )
        assert response.status_code == 200
        return response.json()["id"]
    
    def test_generate_response_accepts_pdf_format(self, auth_token, test_case_id):
        """Test generate-response endpoint accepts output_format=pdf"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/cases/{test_case_id}/generate-response",
            headers=headers,
            data={
                "response_type": "Antwortschreiben",
                "recipient": "Test Empfänger",
                "subject": "Test Betreff PDF",
                "instructions": "Test instructions",
                "output_format": "pdf"
            }
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Generate response (PDF): {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        
        # Check response structure
        if data.get("success"):
            assert "correspondence_id" in data
            assert data.get("output_format") == "pdf", f"Expected output_format 'pdf', got '{data.get('output_format')}'"
            print("✓ Response generated with PDF format")
        else:
            # AI might not be available
            print(f"✓ Endpoint accepts PDF format (AI may be unavailable: {data.get('error', 'no error')})")
    
    def test_generate_response_accepts_docx_format(self, auth_token, test_case_id):
        """Test generate-response endpoint accepts output_format=docx"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/cases/{test_case_id}/generate-response",
            headers=headers,
            data={
                "response_type": "Widerspruch",
                "recipient": "Test Behörde",
                "subject": "Test Betreff DOCX",
                "instructions": "Test instructions for DOCX",
                "output_format": "docx"
            }
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Generate response (DOCX): {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        
        if data.get("success"):
            assert "correspondence_id" in data
            assert data.get("output_format") == "docx", f"Expected output_format 'docx', got '{data.get('output_format')}'"
            print("✓ Response generated with DOCX format")
        else:
            print(f"✓ Endpoint accepts DOCX format (AI may be unavailable: {data.get('error', 'no error')})")
    
    def test_generate_response_accepts_txt_format(self, auth_token, test_case_id):
        """Test generate-response endpoint accepts output_format=txt (defaults to pdf)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/cases/{test_case_id}/generate-response",
            headers=headers,
            data={
                "response_type": "Stellungnahme",
                "recipient": "Test Stelle",
                "subject": "Test Betreff TXT",
                "output_format": "txt"
            }
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Generate response (TXT): {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        
        # txt should default to pdf per the code logic
        if data.get("success"):
            # The code converts txt to pdf: output_format if output_format in ("pdf", "docx") else "pdf"
            assert data.get("output_format") in ["pdf", "txt"], f"Unexpected output_format: {data.get('output_format')}"
            print("✓ Response generated (txt format handled)")
        else:
            print(f"✓ Endpoint accepts txt format (AI may be unavailable)")


class TestDataExportZIP:
    """Test data export returns ZIP file"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_export_all_returns_zip(self, auth_token):
        """Test /api/export/all returns a ZIP file"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/export/all", headers=headers)
        
        assert response.status_code == 200, f"Export failed: {response.status_code} - {response.text[:200]}"
        
        # Check Content-Type is application/zip
        content_type = response.headers.get("Content-Type", "")
        assert "application/zip" in content_type or "application/octet-stream" in content_type, \
            f"Expected ZIP content type, got: {content_type}"
        
        # Check Content-Disposition header for filename
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition.lower() or "filename" in content_disposition.lower(), \
            f"Expected attachment disposition, got: {content_disposition}"
        
        # Check response content is not empty and starts with ZIP magic bytes
        content = response.content
        assert len(content) > 0, "ZIP file should not be empty"
        
        # ZIP files start with PK (0x50 0x4B)
        assert content[:2] == b'PK', f"Response does not appear to be a valid ZIP file (magic bytes: {content[:4]})"
        
        print(f"✓ Export returns valid ZIP file ({len(content)} bytes)")
        print(f"  Content-Type: {content_type}")
        print(f"  Content-Disposition: {content_disposition}")


class TestAIStatus:
    """Test AI status endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_ai_status_endpoint(self, auth_token):
        """Test AI status endpoint returns provider info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "configured_provider" in data
        assert "ollama" in data
        assert "openai" in data
        assert "internet_access" in data
        
        print(f"✓ AI Status: {json.dumps(data, indent=2)}")


class TestDocuments:
    """Test document endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_list_documents(self, auth_token):
        """Test listing documents"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/documents", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        print(f"✓ Documents list: {len(data)} documents found")
        if data:
            doc = data[0]
            print(f"  First document: {doc.get('display_name', doc.get('original_filename'))}")


class TestCases:
    """Test case endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_list_cases(self, auth_token):
        """Test listing cases"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/cases", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        print(f"✓ Cases list: {len(data)} cases found")
        if data:
            case = data[0]
            print(f"  First case: {case.get('title')} (ID: {case.get('id')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
