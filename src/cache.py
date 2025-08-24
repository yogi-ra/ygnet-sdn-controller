import redis
from .config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
)


def get_redis_client():
    """
    Dependency injector for the Redis client.
    """
    return redis_client
