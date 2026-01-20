"""
Pytest configuration and shared fixtures for Blog AI tests.
"""

import os
import sys

# Ensure test environment variables are set before any imports
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def reset_db():
    """Reset the database before each test."""
    from app.db.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function")
def test_client(reset_db):
    """Create a test client with fresh database."""
    from server import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def authenticated_client(test_client):
    """Create a test client with an authenticated user."""
    # Register a test user
    test_client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123",
        },
    )

    # Login to get tokens
    login_response = test_client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPass123",
        },
    )
    tokens = login_response.json()
    access_token = tokens["access_token"]

    # Create a wrapper that adds auth header
    class AuthenticatedClient:
        def __init__(self, client, token):
            self._client = client
            self._token = token
            self._headers = {"Authorization": f"Bearer {token}"}

        def get(self, url, **kwargs):
            headers = kwargs.pop("headers", {})
            headers.update(self._headers)
            return self._client.get(url, headers=headers, **kwargs)

        def post(self, url, **kwargs):
            headers = kwargs.pop("headers", {})
            headers.update(self._headers)
            return self._client.post(url, headers=headers, **kwargs)

        def put(self, url, **kwargs):
            headers = kwargs.pop("headers", {})
            headers.update(self._headers)
            return self._client.put(url, headers=headers, **kwargs)

        def delete(self, url, **kwargs):
            headers = kwargs.pop("headers", {})
            headers.update(self._headers)
            return self._client.delete(url, headers=headers, **kwargs)

        @property
        def token(self):
            return self._token

    return AuthenticatedClient(test_client, access_token)


@pytest.fixture(scope="function")
def sample_blog_request():
    """Sample valid blog generation request."""
    return {
        "topic": "Introduction to Machine Learning",
        "keywords": ["AI", "ML", "neural networks"],
        "tone": "professional",
        "conversation_id": "test-conv-123",
        "research": False,
        "proofread": False,
        "humanize": False,
    }


@pytest.fixture(scope="function")
def sample_book_request():
    """Sample valid book generation request."""
    return {
        "title": "The Complete Guide to Python",
        "num_chapters": 5,
        "sections_per_chapter": 3,
        "conversation_id": "test-conv-456",
        "research": False,
    }
