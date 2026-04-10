#!/usr/bin/env python3
"""
Manual API test script to verify authentication endpoints work correctly.
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_authentication_flow():
    """Test the complete authentication flow."""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing MCA21 Sentiment Analysis Authentication API")
        print("=" * 60)
        
        # Test 1: Register a new user
        print("\n1. Testing user registration...")
        register_data = {
            "name": "Test Admin User",
            "email": "admin@test.com",
            "password": "AdminPassword123!",
            "role": "admin"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
            if response.status_code == 201:
                print("✅ User registration successful")
                data = response.json()
                admin_token = data["access_token"]
                print(f"   Token: {admin_token[:50]}...")
                print(f"   User: {data['user']['name']} ({data['user']['role']})")
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return
        
        # Test 2: Register an analyst user
        print("\n2. Testing analyst user registration...")
        analyst_data = {
            "name": "Test Analyst User",
            "email": "analyst@test.com",
            "password": "AnalystPassword123!",
            "role": "analyst"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/register", json=analyst_data)
            if response.status_code == 201:
                print("✅ Analyst registration successful")
                data = response.json()
                print(f"   User: {data['user']['name']} ({data['user']['role']})")
            else:
                print(f"❌ Analyst registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Analyst registration error: {e}")
        
        # Test 3: Login with admin user
        print("\n3. Testing user login...")
        login_data = {
            "email": "admin@test.com",
            "password": "AdminPassword123!"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                print("✅ Login successful")
                data = response.json()
                login_token = data["access_token"]
                print(f"   New token: {login_token[:50]}...")
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return
        
        # Test 4: Get current user info
        print("\n4. Testing get current user...")
        headers = {"Authorization": f"Bearer {login_token}"}
        
        try:
            response = await client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
            if response.status_code == 200:
                print("✅ Get current user successful")
                data = response.json()
                print(f"   User: {data['name']} ({data['email']}) - Role: {data['role']}")
            else:
                print(f"❌ Get current user failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Get current user error: {e}")
        
        # Test 5: Refresh token
        print("\n5. Testing token refresh...")
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/refresh", headers=headers)
            if response.status_code == 200:
                print("✅ Token refresh successful")
                data = response.json()
                new_token = data["access_token"]
                print(f"   Refreshed token: {new_token[:50]}...")
                print(f"   Tokens are different: {new_token != login_token}")
            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
        
        # Test 6: Test duplicate registration
        print("\n6. Testing duplicate email registration...")
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
            if response.status_code == 400:
                print("✅ Duplicate email properly rejected")
                data = response.json()
                print(f"   Error: {data['message']}")
            else:
                print(f"❌ Duplicate email not properly handled: {response.status_code}")
        except Exception as e:
            print(f"❌ Duplicate email test error: {e}")
        
        # Test 7: Test weak password
        print("\n7. Testing weak password validation...")
        weak_password_data = {
            "name": "Weak Password User",
            "email": "weak@test.com",
            "password": "weak",
            "role": "analyst"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/register", json=weak_password_data)
            if response.status_code in [400, 422]:
                print("✅ Weak password properly rejected")
                data = response.json()
                print(f"   Error: {data['message']}")
            else:
                print(f"❌ Weak password not properly handled: {response.status_code}")
        except Exception as e:
            print(f"❌ Weak password test error: {e}")
        
        # Test 8: Test invalid login
        print("\n8. Testing invalid login...")
        invalid_login = {
            "email": "admin@test.com",
            "password": "WrongPassword123!"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/login", json=invalid_login)
            if response.status_code == 401:
                print("✅ Invalid login properly rejected")
                data = response.json()
                print(f"   Error: {data['detail']}")
            else:
                print(f"❌ Invalid login not properly handled: {response.status_code}")
        except Exception as e:
            print(f"❌ Invalid login test error: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 Authentication API testing completed!")

if __name__ == "__main__":
    print("Starting authentication API tests...")
    print("Make sure the server is running on http://localhost:8000")
    print("You can start it with: python -m uvicorn app.main:app --reload")
    print()
    
    try:
        asyncio.run(test_authentication_flow())
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")