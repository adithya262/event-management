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
    app = FastAPI()
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
    return TestClient(app)

@pytest.mark.asyncio
async def test_security_headers(app, client):
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
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    for _ in range(settings.RATE_LIMIT_PER_MINUTE):
        response = client.get("/test")
        assert response.status_code == 200

    response = client.get("/test")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too Many Requests"

@pytest.mark.asyncio
async def test_rate_limit_excluded_paths(app, client):
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    for _ in range(10):
        response = client.get("/health")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_request_logging(app, client):
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    response = client.get("/test")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_error_logging(app, client):
    @app.get("/test-error")
    async def test_error_endpoint():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        client.get("/test-error")

@pytest.mark.asyncio
async def test_middleware_order(app):
    middleware_classes = [m.__class__ for m in app.user_middleware]
    assert middleware_classes[0] == RequestLoggingMiddleware
    assert middleware_classes[1] == SecurityHeadersMiddleware
    assert middleware_classes[-1] == RateLimitMiddleware

@pytest.mark.asyncio
async def test_cors_headers(app, client):
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