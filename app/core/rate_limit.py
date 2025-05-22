from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis
import time
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_timeout=5,  # Add timeout
                socket_connect_timeout=5  # Add connection timeout
            )
            # Test connection
            self.redis_client.ping()
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis: {str(e)}")
            self.redis_client = None
            
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
        self.window_size = 60  # 1 minute in seconds

    async def dispatch(self, request: Request, call_next):
        # Disable rate limiting in test environment
        if settings.ENVIRONMENT in ["test", "testing"]:
            return await call_next(request)
            
        # Skip rate limiting for certain paths
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/metrics"]:
            return await call_next(request)

        # If Redis is not available, proceed without rate limiting
        if not self.redis_client:
            logger.warning("Redis not available, proceeding without rate limiting")
            return await call_next(request)

        try:
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}"

            # Get current count
            current = self.redis_client.get(key)
            if current is None:
                # First request in the window
                self.redis_client.setex(key, self.window_size, 1)
            elif int(current) >= self.rate_limit:
                # Rate limit exceeded
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail="Too Many Requests",
                    headers={"Retry-After": str(self.window_size)}
                )
            else:
                # Increment counter
                self.redis_client.incr(key)

            # Process request
            response = await call_next(request)
            return response
            
        except redis.RedisError as e:
            logger.error(f"Redis error during rate limiting: {str(e)}")
            # On Redis error, proceed without rate limiting
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unexpected error during rate limiting: {str(e)}")
            # On unexpected error, proceed without rate limiting
            return await call_next(request) 