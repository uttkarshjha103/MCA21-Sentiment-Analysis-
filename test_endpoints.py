"""
Test authentication endpoints manually.
"""
import asyncio
import json
import aiohttp
import subprocess
import time
import signal
import os


async def test_endpoints():
    """Test authentication endpoints."""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("Testing health endpoint...")
        async with session.get(f"{base_url}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ Health check: {data['status']}")
            else:
                print(f"✗ Health check failed: {response.status}")
                return
        
        # Test user registration
        print("\nTesting user registration...")
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "role": "analyst"
        }
        
        async with session.post(f"{base_url}/api/v1/auth/register", json=user_data) as response:
            if response.status == 201:
                data = await response.json()
                print("✓ User registration successful")
                print(f"  - User: {data['user']['name']} ({data['user']['role']})")
                print(f"  - Token type: {data['token_type']}")
                token = data['access_token']
            else:
                error_data = await response.json()
                print(f"✗ Registration failed: {response.status}")
                print(f"  Error: {error_data}")
                return
        
        # Test user login
        print("\nTesting user login...")
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        async with session.post(f"{base_url}/api/v1/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                print("✓ User login successful")
                print(f"  - User: {data['user']['name']}")
                login_token = data['access_token']
            else:
                error_data = await response.json()
                print(f"✗ Login failed: {response.status}")
                print(f"  Error: {error_data}")
                return
        
        # Test getting current user
        print("\nTesting current user endpoint...")
        headers = {"Authorization": f"Bearer {login_token}"}
        
        async with session.get(f"{base_url}/api/v1/auth/me", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print("✓ Current user endpoint successful")
                print(f"  - User: {data['name']} ({data['email']})")
            else:
                error_data = await response.json()
                print(f"✗ Current user failed: {response.status}")
                print(f"  Error: {error_data}")
                return
        
        # Test token refresh
        print("\nTesting token refresh...")
        async with session.post(f"{base_url}/api/v1/auth/refresh", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print("✓ Token refresh successful")
                print(f"  - New token type: {data['token_type']}")
            else:
                error_data = await response.json()
                print(f"✗ Token refresh failed: {response.status}")
                print(f"  Error: {error_data}")
                return
        
        # Test invalid credentials
        print("\nTesting invalid login...")
        invalid_login = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        
        async with session.post(f"{base_url}/api/v1/auth/login", json=invalid_login) as response:
            if response.status == 401:
                print("✓ Invalid login correctly rejected")
            else:
                print(f"✗ Invalid login should have been rejected: {response.status}")
        
        print("\n✅ All endpoint tests completed successfully!")


def start_server():
    """Start the FastAPI server."""
    return subprocess.Popen([
        "python", "-m", "uvicorn", "app.main:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ], cwd=".")


async def main():
    """Main test function."""
    print("Starting FastAPI server...")
    server_process = start_server()
    
    try:
        # Wait for server to start
        print("Waiting for server to start...")
        await asyncio.sleep(5)
        
        # Run tests
        await test_endpoints()
        
    finally:
        # Stop server
        print("\nStopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()


if __name__ == "__main__":
    asyncio.run(main())