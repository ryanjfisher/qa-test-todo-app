"""
Tests for comment system.
SCRUM-16: Threaded comments
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestCreateComment:
    """Tests for creating comments - SCRUM-16"""
    
    def test_create_top_level_comment(self, auth_headers, article_id):
        """Can create a top-level comment."""
        response = client.post("/api/comments/", 
            headers=auth_headers,
            json={
                "content": "Great article!",
                "article_id": article_id
            }
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Great article!"
    
    def test_create_reply(self, auth_headers, comment_id):
        """Can reply to an existing comment."""
        response = client.post("/api/comments/",
            headers=auth_headers,
            json={
                "content": "I agree!",
                "article_id": 1,
                "parent_id": comment_id
            }
        )
        assert response.status_code == 200
        assert response.json()["parent_id"] == comment_id


class TestThreadingDepth:
    """Tests for nesting limits - SCRUM-16"""
    
    def test_max_depth_3_levels(self, auth_headers):
        """Replies limited to 3 levels of nesting."""
        # Create level 1
        r1 = client.post("/api/comments/", headers=auth_headers, 
            json={"content": "Level 1", "article_id": 1})
        c1_id = r1.json()["id"]
        
        # Create level 2
        r2 = client.post("/api/comments/", headers=auth_headers,
            json={"content": "Level 2", "article_id": 1, "parent_id": c1_id})
        c2_id = r2.json()["id"]
        
        # Create level 3
        r3 = client.post("/api/comments/", headers=auth_headers,
            json={"content": "Level 3", "article_id": 1, "parent_id": c2_id})
        c3_id = r3.json()["id"]
        
        # Attempt level 4 - should fail
        r4 = client.post("/api/comments/", headers=auth_headers,
            json={"content": "Level 4", "article_id": 1, "parent_id": c3_id})
        assert r4.status_code == 400
        assert "depth" in r4.json()["detail"].lower()


class TestRateLimiting:
    """Tests for comment rate limiting - SCRUM-16"""
    
    def test_rate_limit_10_per_hour(self, auth_headers):
        """Users limited to 10 comments per hour."""
        for i in range(10):
            response = client.post("/api/comments/", headers=auth_headers,
                json={"content": f"Comment {i+1}", "article_id": 1})
            assert response.status_code == 200
        
        # 11th should fail
        response = client.post("/api/comments/", headers=auth_headers,
            json={"content": "One too many", "article_id": 1})
        assert response.status_code == 429
