# app/auth/redis.py
import aioredis
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

async def get_redis():
    if not hasattr(get_redis, "redis"):
        try:
            get_redis.redis = await aioredis.from_url(
                settings.REDIS_URL or "redis://localhost"
            )
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            return None
    return get_redis.redis

async def add_to_blacklist(jti: str, exp: int):
    """Add a token's JTI to the blacklist"""
    redis = await get_redis()
    if redis:
        try:
            await redis.set(f"blacklist:{jti}", "1", ex=exp)
        except Exception as e:
            logger.warning(f"Redis error in add_to_blacklist: {e}")

async def is_blacklisted(jti: str) -> bool:
    """Check if a token's JTI is blacklisted"""
    redis = await get_redis()
    if redis:
        try:
            return await redis.exists(f"blacklist:{jti}")
        except Exception as e:
            logger.warning(f"Redis error in is_blacklisted: {e}")
            return False
    return False
