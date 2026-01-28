"""
Tests for authentication endpoints.
SCRUM-11: JWT Authentication
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestLogin:
    """Tests for login endpoint - SCRUM-11"""
    
    def test_login_success(self):
        """Given valid credentials, when logging in, then return tokens."""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["expires_in"] == 900
    
    def test_login_invalid_password(self):
        """Given invalid password, when logging in, then return 401."""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestRefreshToken:
    """Tests for token refresh - SCRUM-11"""
    
    def test_refresh_success(self):
        """Given valid refresh token, when refreshing, then return new tokens."""
        # First login
        login = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        refresh_token = login.json()["refresh_token"]
        
        # Refresh
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_refresh_invalidates_old_token(self):
        """After refresh, old refresh token should be invalid - SCRUM-11"""
        # Login
        login = client.post("/api/auth/login", json={
            "email": "test@example.com", 
            "password": "password123"
        })
        old_refresh = login.json()["refresh_token"]
        
        # Refresh once
        client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
        
        # Try using old token again
        response = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
        assert response.status_code == 401  # Should be rejected
