import os
import sys
import logging
import app.models  # Ensure all models are registered

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import engine, get_db, init_db
from app.services.background_service import BackgroundService
from app.api.api import api_router
from sqlalchemy import text
from app.core.rate_limit import RateLimitMiddleware
from app.core.logging import logger
from app.core.metrics import setup_metrics
from app.core.exceptions import (
    BaseAppException,
    handle_exception,
    DatabaseException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ConflictException,
    RateLimitException
)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from app.api.auth import router as auth_router
from app.core.security_middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware, setup_middleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        environment=settings.ENVIRONMENT
    )

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    version="1.0.0",
)

# Add middleware in the correct order
app.add_middleware(RequestLoggingMiddleware)  # First to log all requests
app.add_middleware(SecurityHeadersMiddleware)  # Second to add security headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    max_age=600,
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)
app.add_middleware(RateLimitMiddleware)  # Add rate limiting middleware

# Setup metrics
setup_metrics(app)

# Global exception handlers
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle application-specific exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=handle_exception(exc).detail
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )

@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    """Handle authentication exceptions."""
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    """Handle authorization exceptions."""
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)},
    )

@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    """Handle conflict exceptions."""
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )

@app.exception_handler(RateLimitException)
async def rate_limit_exception_handler(request: Request, exc: RateLimitException):
    """Handle rate limit exceptions."""
    return JSONResponse(
        status_code=429,
        content={"detail": str(exc)},
        headers={"Retry-After": str(exc.retry_after)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

def get_background_service(background_tasks: BackgroundTasks) -> BackgroundService:
    return BackgroundService(background_tasks)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    try:
        # Initialize database with optimized settings
        await init_db()
        
        # Check if tables exist
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            logger.info(f"Existing tables: {tables}")
            
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    # Cleanup tasks here

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Event Management API"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Add background service dependency
app.dependency_overrides[BackgroundService] = get_background_service

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 