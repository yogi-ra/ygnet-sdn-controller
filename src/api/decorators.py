import json
from functools import wraps
from typing import Any, Callable, Dict, List, Union

from fastapi import Depends, HTTPException, status
from redis import Redis

from ..cache import get_redis_client

def cache_response(
    cache_key_prefix: str,
    ttl: int = 300,  # Default TTL of 5 minutes
    response_model: Any = None,  # Optional: Pydantic model for response validation
) -> Callable[..., Callable[..., Any]]:
    """
    A decorator to cache API responses in Redis.

    Args:
        cache_key_prefix: The prefix for the Redis cache key (e.g., "device").
        ttl: Time-to-live for the cache entry in seconds.
        response_model: Optional Pydantic model to validate the response before caching.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(
            *args: Any,
            redis_client: Redis = Depends(get_redis_client),
            **kwargs: Any,
        ) -> Any:
            device_id = kwargs.get("device_id")
            if not device_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="device_id not found in function arguments for caching.",
                )

            # Construct cache key dynamically based on function arguments
            cache_key_parts = [cache_key_prefix, str(device_id)]
            # Add other relevant kwargs to the cache key if they are part of the URL path
            for k, v in kwargs.items():
                if k not in ["device_id", "handler", "db", "redis_client"] and not k.startswith("_"):
                    cache_key_parts.append(str(v))
            cache_key = ":".join(cache_key_parts)

            cached_data = redis_client.get(cache_key)
            if cached_data:
                try:
                    # If a response_model is provided, validate against it
                    if response_model:
                        return response_model.model_validate_json(cached_data)
                    return json.loads(cached_data)
                except (json.JSONDecodeError, ValueError) as e:
                    # Log error and delete corrupted cache entry
                    print(f"Error decoding cached data for {cache_key}: {e}")
                    redis_client.delete(cache_key)

            # Execute the original function to get the response
            response = await func(*args, redis_client=redis_client, **kwargs)

            # Validate response against response_model if provided
            if response_model:
                try:
                    response = response_model.model_validate(response)
                except ValueError as e:
                    print(f"Response validation failed for {cache_key}: {e}")
                    # Optionally, raise an HTTPException or return unvalidated response
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Response validation failed: {e}",
                    )

            # Cache the response
            try:
                # Handle datetime objects in response if present
                if isinstance(response, datetime):
                    data_to_cache = json.dumps(response.isoformat())
                elif isinstance(response, (dict, list)):
                    data_to_cache = json.dumps(response)
                else:
                    data_to_cache = json.dumps(str(response))

                redis_client.setex(cache_key, ttl, data_to_cache)
            except TypeError as e:
                print(f"Error serializing response for {cache_key}: {e}")
                # If serialization fails, don't cache but still return the response

            return response

        return wrapper

    return decorator
