#!/usr/bin/env python3
"""
CaseDesk AI Backend Testing - v1.0.4 Features
Testing the new health-check endpoint, system version, and settings system
"""
import requests
import json
import sys
import os

# Backend URL from frontend .env
BACKEND_URL = "https://kai-organizer.preview.emergentagent.com/api"

# Test credentials (admin user)
ADMIN_EMAIL = "andi.trenter@gmail.com"
ADMIN_PASSWORD = "admin123"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        
    def setup_admin_if_needed(self):
        """Check if setup is needed and create admin user"""
        print("🔧 Checking setup status...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/setup/status")
            if response.status_code == 200:
                status = response.json()
                print(f"   Setup configured: {status.get('is_configured')}")
                print(f"   Has admin: {status.get('has_admin')}")
                
                if not status.get('has_admin'):
                    print("🔧 No admin user found, initializing setup...")
                    
                    setup_data = {
                        "admin_email": ADMIN_EMAIL,
                        "admin_username": "admin",
                        "admin_password": ADMIN_PASSWORD,
                        "admin_full_name": "Admin User",
                        "language": "de",
                        "ai_provider": "ollama",
                        "internet_access": "allowed",
                        "organization_name": "CaseDesk Test"
                    }
                    
                    setup_response = self.session.post(f"{BACKEND_URL}/setup/init", data=setup_data)
                    print(f"Setup response status: {setup_response.status_code}")
                    
                    if setup_response.status_code == 200:
                        setup_result = setup_response.json()
                        print("✅ Setup completed successfully")
                        
                        # Extract token from setup response
                        self.auth_token = setup_result.get("access_token")
                        self.user_data = setup_result.get("user")
                        
                        if self.auth_token:
                            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                            print(f"✅ Admin user created and authenticated: {self.user_data.get('email')}")
                            return True
                        else:
                            print("❌ Setup completed but no token received")
                            return False
                    else:
                        print(f"❌ Setup failed: {setup_response.status_code}")
                        print(f"   Response: {setup_response.text}")
                        return False
                else:
                    print("✅ Admin user already exists")
                    return True
            else:
                print(f"❌ Could not check setup status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Setup check error: {e}")
            return False
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        print("🔐 Authenticating with admin credentials...")
        
        # First check if we need to setup
        if not self.setup_admin_if_needed():
            return False
        
        # If we already got a token from setup, we're done
        if self.auth_token:
            return True
        
        # Try to login (using form data, not JSON)
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", data=login_data)
            print(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_data = data.get("user")
                
                if self.auth_token:
                    # Set authorization header for future requests
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print(f"✅ Authentication successful for user: {self.user_data.get('email')}")
                    print(f"   User role: {self.user_data.get('role')}")
                    return True
                else:
                    print("❌ No access token received")
                    return False
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_health_endpoint(self):
        """Test the new health-check endpoint (GET /api/admin/health)"""
        print("\n🏥 Testing Health-Check Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/health")
            print(f"Health endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Health endpoint accessible")
                
                # Check required structure
                required_fields = ["timestamp", "services"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
                
                services = data.get("services", {})
                print(f"   Found {len(services)} services")
                
                # Check OpenAI service
                if "openai" in services:
                    openai_service = services["openai"]
                    print(f"   OpenAI: status={openai_service.get('status')}, active={openai_service.get('active')}")
                    
                    required_openai_fields = ["status", "active"]
                    missing_openai = [field for field in required_openai_fields if field not in openai_service]
                    if missing_openai:
                        print(f"❌ OpenAI service missing fields: {missing_openai}")
                        return False
                else:
                    print("❌ OpenAI service not found in health response")
                    return False
                
                # Check Ollama service
                if "ollama" in services:
                    ollama_service = services["ollama"]
                    print(f"   Ollama: status={ollama_service.get('status')}, url={ollama_service.get('url')}, active={ollama_service.get('active')}")
                    print(f"   Ollama models: {ollama_service.get('models', [])}")
                    
                    required_ollama_fields = ["status", "url", "models", "active"]
                    missing_ollama = [field for field in required_ollama_fields if field not in ollama_service]
                    if missing_ollama:
                        print(f"❌ Ollama service missing fields: {missing_ollama}")
                        return False
                else:
                    print("❌ Ollama service not found in health response")
                    return False
                
                # Check AI config
                if "ai_config" in services:
                    ai_config = services["ai_config"]
                    print(f"   AI Config: active_provider={ai_config.get('active_provider')}, fallback_available={ai_config.get('fallback_available')}")
                    
                    required_ai_config_fields = ["active_provider", "fallback_available"]
                    missing_ai_config = [field for field in required_ai_config_fields if field not in ai_config]
                    if missing_ai_config:
                        print(f"❌ AI config missing fields: {missing_ai_config}")
                        return False
                else:
                    print("❌ AI config not found in health response")
                    return False
                
                print("✅ Health endpoint structure is correct")
                return True
                
            elif response.status_code == 401:
                print("❌ Health endpoint requires authentication (401)")
                return False
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
    
    def test_system_version(self):
        """Test system version endpoint (GET /api/system/version)"""
        print("\n📋 Testing System Version Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/system/version")
            print(f"Version endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                version = data.get("version")
                print(f"   Current version: {version}")
                print(f"   Build date: {data.get('build_date')}")
                print(f"   Release notes: {data.get('release_notes')}")
                
                if version == "1.0.4":
                    print("✅ Version endpoint returns correct v1.0.4")
                    return True
                else:
                    print(f"❌ Expected version 1.0.4, got {version}")
                    return False
                    
            else:
                print(f"❌ Version endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Version endpoint error: {e}")
            return False
    
    def test_system_settings_get(self):
        """Test GET /api/settings/system"""
        print("\n⚙️ Testing System Settings GET...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/settings/system")
            print(f"Settings GET status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ System settings GET successful")
                print(f"   AI Provider: {data.get('ai_provider')}")
                print(f"   OpenAI API Key: {data.get('openai_api_key')}")
                print(f"   Settings keys: {list(data.keys())}")
                return True
                
            elif response.status_code == 401:
                print("❌ System settings GET requires authentication (401)")
                return False
            else:
                print(f"❌ System settings GET failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ System settings GET error: {e}")
            return False
    
    def test_system_settings_put(self):
        """Test PUT /api/settings/system"""
        print("\n⚙️ Testing System Settings PUT...")
        
        try:
            # Test updating AI provider and API key
            test_data = {
                "ai_provider": "openai",
                "openai_api_key": "sk-test-key-for-testing-purposes"
            }
            
            response = self.session.put(f"{BACKEND_URL}/settings/system", data=test_data)
            print(f"Settings PUT status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ System settings PUT successful")
                print(f"   Response: {data}")
                
                # Verify the settings were saved by getting them again
                get_response = self.session.get(f"{BACKEND_URL}/settings/system")
                if get_response.status_code == 200:
                    saved_data = get_response.json()
                    saved_provider = saved_data.get("ai_provider")
                    saved_key = saved_data.get("openai_api_key")
                    
                    print(f"   Verified AI Provider: {saved_provider}")
                    print(f"   Verified API Key: {saved_key}")
                    
                    if saved_provider == "openai" and saved_key == "***configured***":
                        print("✅ Settings correctly saved and masked")
                        return True
                    else:
                        print("❌ Settings not saved correctly")
                        return False
                else:
                    print("❌ Could not verify saved settings")
                    return False
                
            elif response.status_code == 401:
                print("❌ System settings PUT requires authentication (401)")
                return False
            else:
                print(f"❌ System settings PUT failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ System settings PUT error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all v1.0.4 tests"""
        print("🚀 Starting CaseDesk AI v1.0.4 Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("\n❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run tests
        tests = [
            ("Health-Check Endpoint", self.test_health_endpoint),
            ("System Version", self.test_system_version),
            ("System Settings GET", self.test_system_settings_get),
            ("System Settings PUT", self.test_system_settings_put),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"\n❌ {test_name} crashed: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️ Some tests failed")
            return False


if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)