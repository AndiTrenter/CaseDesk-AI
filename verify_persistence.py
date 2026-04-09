#!/usr/bin/env python3
"""
Quick verification test to double-check settings persistence
"""

import asyncio
import httpx
import json

BACKEND_URL = "https://ai-calendar-debug.preview.emergentagent.com/api"
TEST_EMAIL = "andi.trenter@gmail.com"
TEST_PASSWORD = "admin123"

async def verify_persistence():
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        # Login
        login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        response = await client.post(f"{BACKEND_URL}/auth/login", data=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check settings again
        response = await client.get(f"{BACKEND_URL}/settings/system", headers=headers)
        settings = response.json()
        
        print("🔍 Final verification - Settings in database:")
        print(json.dumps(settings, indent=2))
        
        # Verify key fields
        assert settings.get("ai_provider") == "openai", f"ai_provider should be 'openai', got: {settings.get('ai_provider')}"
        assert settings.get("openai_api_key") == "***configured***", f"API key should be masked, got: {settings.get('openai_api_key')}"
        assert settings.get("internet_access") == "allowed", f"internet_access should be 'allowed', got: {settings.get('internet_access')}"
        
        print("✅ VERIFICATION PASSED: Settings are properly persisted!")
        
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(verify_persistence())