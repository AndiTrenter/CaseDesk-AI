#!/usr/bin/env python3
"""
CaseDesk AI Backend Testing - Settings Persistence Fix
Testing the CRITICAL FIX for settings persistence where upsert=True was missing.
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://task-portal-fix.preview.emergentagent.com/api"

# Test credentials
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

class BackendTester:
    def __init__(self):
        self.auth_token = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        await self.client.aclose()
        
    async def login(self):
        """Login and get auth token"""
        print("🔐 Testing Login...")
        
        # Use form data for login
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = await self.client.post(
            f"{BACKEND_URL}/auth/login",
            data=login_data
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
            
        data = response.json()
        if not data.get("access_token"):
            print(f"❌ No access token in response: {data}")
            return False
            
        self.auth_token = data["access_token"]
        print(f"✅ Login successful - Token: {self.auth_token[:20]}...")
        return True
        
    def get_headers(self):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {self.auth_token}"}
        
    async def test_settings_persistence_fix(self):
        """Test the CRITICAL FIX for settings persistence"""
        print("\n🔧 Testing Settings Persistence Fix...")
        
        # Step 1: Clear any existing settings first (optional - just to test from clean state)
        print("📋 Step 1: Getting current settings...")
        response = await self.client.get(
            f"{BACKEND_URL}/settings/system",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get current settings: {response.status_code} - {response.text}")
            return False
            
        current_settings = response.json()
        print(f"✅ Current settings: {json.dumps(current_settings, indent=2)}")
        
        # Step 2: Update settings with test data
        print("\n📝 Step 2: Updating settings with test data...")
        
        # Test data as specified in the review request
        test_settings = {
            "ai_provider": "openai",
            "openai_api_key": "sk-test-key-12345",
            "internet_access": "allowed"
        }
        
        response = await self.client.put(
            f"{BACKEND_URL}/settings/system",
            headers=self.get_headers(),
            data=test_settings  # Use form data
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to update settings: {response.status_code} - {response.text}")
            return False
            
        update_result = response.json()
        print(f"✅ Settings update response: {json.dumps(update_result, indent=2)}")
        
        # Step 3: Verify settings were SAVED (not empty!)
        print("\n🔍 Step 3: Verifying settings were saved...")
        
        response = await self.client.get(
            f"{BACKEND_URL}/settings/system",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get updated settings: {response.status_code} - {response.text}")
            return False
            
        saved_settings = response.json()
        print(f"✅ Saved settings: {json.dumps(saved_settings, indent=2)}")
        
        # Verify the settings were actually saved
        if not saved_settings:
            print("❌ CRITICAL ISSUE: Settings are empty! The upsert fix may not be working.")
            return False
            
        # Check specific values
        if saved_settings.get("ai_provider") != "openai":
            print(f"❌ ai_provider not saved correctly. Expected: 'openai', Got: '{saved_settings.get('ai_provider')}'")
            return False
            
        # API key should be masked in response
        if saved_settings.get("openai_api_key") != "***configured***":
            print(f"❌ openai_api_key not masked correctly. Expected: '***configured***', Got: '{saved_settings.get('openai_api_key')}'")
            return False
            
        if saved_settings.get("internet_access") != "allowed":
            print(f"❌ internet_access not saved correctly. Expected: 'allowed', Got: '{saved_settings.get('internet_access')}'")
            return False
            
        print("✅ All settings saved correctly!")
        print("✅ API key properly masked in response!")
        print("✅ SETTINGS PERSISTENCE FIX WORKING!")
        
        return True
        
    async def test_ai_status(self):
        """Test AI status endpoint to check if OpenAI shows available=true"""
        print("\n🤖 Testing AI Status...")
        
        response = await self.client.get(
            f"{BACKEND_URL}/ai/status",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get AI status: {response.status_code} - {response.text}")
            return False
            
        ai_status = response.json()
        print(f"✅ AI Status: {json.dumps(ai_status, indent=2)}")
        
        # Check if OpenAI shows as available
        openai_status = ai_status.get("openai", {})
        if openai_status.get("available") == True:
            print("✅ OpenAI shows as available=true")
        else:
            print(f"⚠️  OpenAI available status: {openai_status.get('available')} (may be expected if no real API key)")
            
        # Check configured provider
        configured_provider = ai_status.get("configured_provider")
        if configured_provider == "openai":
            print("✅ Configured provider is 'openai'")
        else:
            print(f"⚠️  Configured provider: {configured_provider}")
            
        return True
        
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting CaseDesk AI Backend Testing - Settings Persistence Fix")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"👤 Test User: {TEST_EMAIL}")
        print("=" * 80)
        
        try:
            # Login first
            if not await self.login():
                return False
                
            # Test settings persistence fix
            if not await self.test_settings_persistence_fix():
                return False
                
            # Test AI status
            if not await self.test_ai_status():
                return False
                
            print("\n" + "=" * 80)
            print("🎉 ALL TESTS PASSED!")
            print("✅ Settings persistence fix is working correctly")
            print("✅ Settings are being saved to database with upsert=True")
            print("✅ API keys are properly masked in responses")
            return True
            
        except Exception as e:
            print(f"\n❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.close()

async def main():
    """Main test execution"""
    tester = BackendTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())