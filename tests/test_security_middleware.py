import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.security_middleware import setup_middleware, RequestLoggingMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

@pytest.fixture
def app():
    """Create a test FastAPI app."""
    app = FastAPI()
    # Add middleware in the same order as main.py
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        rate_limit=settings.RATE_LIMIT_PER_MINUTE,
        time_window=60
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GZipMiddleware)
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)

@pytest.mark.asyncio
async def test_security_headers(app, client):
    """Test security headers are set correctly."""
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    response = client.get("/test")
    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Strict-Transport-Security" in response.headers

@pytest.mark.asyncio
async def test_rate_limiting(app, client):
    """Test rate limiting functionality."""
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Make requests up to the rate limit
    for _ in range(settings.RATE_LIMIT_PER_MINUTE):
        response = client.get("/test")
        assert response.status_code == 200

    # Next request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too Many Requests"

@pytest.mark.asyncio
async def test_rate_limit_excluded_paths(app, client):
    """Test rate limit excluded paths."""
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    # Make multiple requests to excluded path
    for _ in range(10):
        response = client.get("/health")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_request_logging(app, client):
    """Test request logging middleware."""
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    response = client.get("/test")
    assert response.status_code == 200
    # Verify logs were created (this would require a mock logger)

@pytest.mark.asyncio
async def test_error_logging(app, client):
    """Test error logging middleware."""
    @app.get("/test-error")
    async def test_error_endpoint():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        client.get("/test-error")

@pytest.mark.asyncio
async def test_middleware_order(app):
    """Test middleware order is correct."""
    middleware_classes = [m.__class__ for m in app.user_middleware]
    # Check that RequestLoggingMiddleware is first
    assert middleware_classes[0] == RequestLoggingMiddleware
    # Check that SecurityHeadersMiddleware is second
    assert middleware_classes[1] == SecurityHeadersMiddleware
    # Check that RateLimitMiddleware is last
    assert middleware_classes[-1] == RateLimitMiddleware

@pytest.mark.asyncio
async def test_cors_headers(app, client):
    """Test CORS headers are set correctly."""
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    response = client.options(
        "/test",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000" 