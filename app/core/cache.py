from typing import Any, Optional
import json
import redis
from app.core.config import settings

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.default_ttl = 300  # 5 minutes in seconds

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        value = self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache."""
        ttl = ttl or self.default_ttl
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(value)
        )

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        self.redis_client.delete(key)

    async def clear_pattern(self, pattern: str) -> None:
        """Clear all keys matching a pattern."""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)

    def get_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return ":".join(key_parts)

# Create a singleton instance
cache = RedisCache() 

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

class TokenBlocklistManager:
    @classmethod
    async def add_to_blocklist(cls, jti: str, expires_in: int):
        """Add a token's jti to the blocklist with an expiration time."""
        # Use setex to set the key with an expiration time in seconds
        redis_client.setex(f"blocklist:{jti}", expires_in, "blocked")

    @classmethod
    async def is_blocked(cls, jti: str) -> bool:
        """Check if a token's jti is in the blocklist."""
        return redis_client.exists(f"blocklist:{jti}") 