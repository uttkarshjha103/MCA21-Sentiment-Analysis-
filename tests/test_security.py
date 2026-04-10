"""
Unit tests for security middleware and policies.
Tests password validation, account lockout, and audit logging.
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.core.security import validate_password_strength
from app.models.audit import AuditAction
from app.services.audit import AuditLogger


class TestPasswordStrengthValidation:
    """Test password strength validation requirements."""
    
    def test_valid_strong_password(self):
        """Test that a strong password passes validation."""
        password = "StrongP@ss123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True
        assert message == "Password is valid"
    
    def test_password_too_short(self):
        """Test that passwords shorter than 8 characters are rejected."""
        password = "Short1!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "at least 8 characters" in message
    
    def test_password_no_uppercase(self):
        """Test that passwords without uppercase letters are rejected."""
        password = "lowercase123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "uppercase letter" in message
    
    def test_password_no_lowercase(self):
        """Test that passwords without lowercase letters are rejected."""
        password = "UPPERCASE123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "lowercase letter" in message
    
    def test_password_no_digit(self):
        """Test that passwords without digits are rejected."""
        password = "NoDigits!@#"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "digit" in message
    
    def test_password_no_special_char(self):
        """Test that passwords without special characters are rejected."""
        password = "NoSpecial123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "special character" in message
    
    def test_various_special_characters(self):
        """Test that various special characters are accepted."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for char in special_chars:
            password = f"Valid1{char}pass"
            is_valid, message = validate_password_strength(password)
            assert is_valid is True, f"Failed for special char: {char}"


@pytest.mark.asyncio
class TestAccountLockout:
    """Test account lockout mechanisms."""
    
    async def test_account_locks_after_max_failed_attempts(self, async_client: AsyncClient, test_db):
        """Test that account locks after 5 failed login attempts."""
        # Register a user
        register_data = {
            "name": "Test User",
            "email": "lockout@test.com",
            "password": "ValidP@ss123",
            "role": "analyst"
        }
        response = await async_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        
        # Attempt 5 failed logins
        for i in range(5):
            login_data = {
                "email": "lockout@test.com",
                "password": "WrongPassword123!"
            }
            response = await async_client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 401
        
        # 6th attempt should indicate account is locked
        login_data = {
            "email": "lockout@test.com",
            "password": "WrongPassword123!"
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 400
        assert "locked" in response.json()["message"].lower()
    
    async def test_successful_login_resets_failed_attempts(self, async_client: AsyncClient, test_db):
        """Test that successful login resets failed attempt counter."""
        # Register a user
        register_data = {
            "name": "Test User",
            "email": "reset@test.com",
            "password": "ValidP@ss123",
            "role": "analyst"
        }
        response = await async_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        
        # Attempt 3 failed logins
        for i in range(3):
            login_data = {
                "email": "reset@test.com",
                "password": "WrongPassword123!"
            }
            response = await async_client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 401
        
        # Successful login
        login_data = {
            "email": "reset@test.com",
            "password": "ValidP@ss123"
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        # Verify user document has reset failed attempts
        user = await test_db.users.find_one({"email": "reset@test.com"})
        assert user["failed_login_attempts"] == 0
        assert user["locked_until"] is None
    
    async def test_weak_password_rejected_on_registration(self, async_client: AsyncClient):
        """Test that weak passwords are rejected during registration."""
        register_data = {
            "name": "Test User",
            "email": "weak@test.com",
            "password": "weakpass",  # No uppercase, no special char
            "role": "analyst"
        }
        response = await async_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 400
        assert "security requirements" in response.json()["message"].lower()


@pytest.mark.asyncio
class TestAuditLogging:
    """Test audit logging functionality."""
    
    async def test_successful_login_creates_audit_log(self, async_client: AsyncClient, test_db):
        """Test that successful login creates an audit log entry."""
        # Register a user
        register_data = {
            "name": "Audit Test",
            "email": "audit@test.com",
            "password": "ValidP@ss123",
            "role": "analyst"
        }
        await async_client.post("/api/v1/auth/register", json=register_data)
        
        # Clear audit logs
        await test_db.audit_logs.delete_many({})
        
        # Login
        login_data = {
            "email": "audit@test.com",
            "password": "ValidP@ss123"
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        # Check audit log
        audit_log = await test_db.audit_logs.find_one({"action": AuditAction.LOGIN_SUCCESS.value})
        assert audit_log is not None
        assert audit_log["user_email"] == "audit@test.com"
        assert audit_log["success"] is True
    
    async def test_failed_login_creates_audit_log(self, async_client: AsyncClient, test_db):
        """Test that failed login creates an audit log entry."""
        # Register a user
        register_data = {
            "name": "Audit Test",
            "email": "auditfail@test.com",
            "password": "ValidP@ss123",
            "role": "analyst"
        }
        await async_client.post("/api/v1/auth/register", json=register_data)
        
        # Clear audit logs
        await test_db.audit_logs.delete_many({})
        
        # Failed login
        login_data = {
            "email": "auditfail@test.com",
            "password": "WrongPassword123!"
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        
        # Check audit log
        audit_log = await test_db.audit_logs.find_one({"action": AuditAction.LOGIN_FAILED.value})
        assert audit_log is not None
        assert audit_log["user_email"] == "auditfail@test.com"
        assert audit_log["success"] is False
        assert "invalid_password" in audit_log["details"]["reason"]
    
    async def test_registration_creates_audit_log(self, async_client: AsyncClient, test_db):
        """Test that user registration creates an audit log entry."""
        # Clear audit logs
        await test_db.audit_logs.delete_many({})
        
        # Register a user
        register_data = {
            "name": "Audit Register",
            "email": "auditreg@test.com",
            "password": "ValidP@ss123",
            "role": "analyst"
        }
        response = await async_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        
        # Check audit log
        audit_log = await test_db.audit_logs.find_one({"action": AuditAction.REGISTER.value})
        assert audit_log is not None
        assert audit_log["user_email"] == "auditreg@test.com"
        assert audit_log["success"] is True
        assert audit_log["details"]["role"] == "analyst"
    
    async def test_account_lockout_creates_audit_log(self, async_client: AsyncClient, test_db):
        """Test that account lockout creates an audit log entry."""
        # Register a user
        register_data = {
            "name": "Lockout Audit",
            "email": "lockaudit@test.com",
            "password": "ValidP@ss123",
            "role": "analyst"
        }
        await async_client.post("/api/v1/auth/register", json=register_data)
        
        # Clear audit logs
        await test_db.audit_logs.delete_many({})
        
        # Attempt 5 failed logins to trigger lockout
        for i in range(5):
            login_data = {
                "email": "lockaudit@test.com",
                "password": "WrongPassword123!"
            }
            await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Check for account locked audit log
        audit_log = await test_db.audit_logs.find_one({"action": AuditAction.ACCOUNT_LOCKED.value})
        assert audit_log is not None
        assert audit_log["user_email"] == "lockaudit@test.com"
        assert audit_log["details"]["failed_attempts"] == 5
        assert "locked_until" in audit_log["details"]


@pytest.mark.asyncio
class TestAuditLogRetrieval:
    """Test audit log retrieval endpoints."""
    
    async def test_admin_can_retrieve_audit_logs(self, async_client: AsyncClient, test_db):
        """Test that admin users can retrieve audit logs."""
        # Register admin user
        admin_data = {
            "name": "Admin User",
            "email": "admin@test.com",
            "password": "AdminP@ss123",
            "role": "admin"
        }
        response = await async_client.post("/api/v1/auth/register", json=admin_data)
        assert response.status_code == 201
        admin_token = response.json()["access_token"]
        
        # Get audit logs
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await async_client.get("/api/v1/audit/logs", headers=headers)
        assert response.status_code == 200
        assert "total" in response.json()
        assert "logs" in response.json()
    
    async def test_analyst_cannot_retrieve_all_audit_logs(self, async_client: AsyncClient, test_db):
        """Test that analyst users cannot retrieve all audit logs."""
        # Register analyst user
        analyst_data = {
            "name": "Analyst User",
            "email": "analyst@test.com",
            "password": "AnalystP@ss123",
            "role": "analyst"
        }
        response = await async_client.post("/api/v1/auth/register", json=analyst_data)
        assert response.status_code == 201
        analyst_token = response.json()["access_token"]
        
        # Try to get all audit logs (should fail)
        headers = {"Authorization": f"Bearer {analyst_token}"}
        response = await async_client.get("/api/v1/audit/logs", headers=headers)
        assert response.status_code == 403
    
    async def test_user_can_retrieve_own_activity(self, async_client: AsyncClient, test_db):
        """Test that users can retrieve their own activity logs."""
        # Register user
        user_data = {
            "name": "Regular User",
            "email": "user@test.com",
            "password": "UserP@ss123",
            "role": "analyst"
        }
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        user_token = response.json()["access_token"]
        
        # Get own activity
        headers = {"Authorization": f"Bearer {user_token}"}
        response = await async_client.get("/api/v1/audit/logs/me", headers=headers)
        assert response.status_code == 200
        assert "logs" in response.json()
        
        # Verify logs are for this user
        logs = response.json()["logs"]
        for log in logs:
            assert log["user_email"] == "user@test.com"
