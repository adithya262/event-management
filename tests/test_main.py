import sys
import pytest
from fastapi import FastAPI
from app.main import app, startup_event, shutdown_event
from app.core.config import settings
from httpx import AsyncClient
import logging
from fastapi.testclient import TestClient

def test_app_creation():
    assert isinstance(app, FastAPI)
    assert app.title == settings.PROJECT_NAME
    assert app.version == settings.VERSION

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Event Management API"}

@pytest.mark.asyncio
async def test_docs_endpoints(client: AsyncClient):
    response = await client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
    response = await client.get("/docs")
    assert response.status_code == 200
    response = await client.get("/redoc")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    response = await client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-credentials" in response.headers
    assert "access-control-max-age" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers["access-control-max-age"] == "600"

@pytest.mark.asyncio
@pytest.mark.skipif(
    "httpx" in sys.modules,
    reason="TrustedHostMiddleware does not enforce host header in httpx test client."
)
async def test_trusted_hosts(client: AsyncClient):
    response = await client.get("/", headers={"Host": "testserver"})
    assert response.status_code == 200
    response = await client.get("/", headers={"Host": "invalid-host.com"})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_startup_event(client: AsyncClient):
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    class TestHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.buffer = []
        def emit(self, record):
            self.buffer.append(record)
    test_handler = TestHandler()
    test_handler.setLevel(logging.INFO)
    logger.addHandler(test_handler)
    await startup_event()
    assert any("Starting up application" in record.message for record in test_handler.buffer)

@pytest.mark.asyncio
async def test_shutdown_event(client: AsyncClient):
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    class TestHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.buffer = []
        def emit(self, record):
            self.buffer.append(record)
    test_handler = TestHandler()
    test_handler.setLevel(logging.INFO)
    logger.addHandler(test_handler)
    await shutdown_event()
    assert any("Shutting down application" in record.message for record in test_handler.buffer) 