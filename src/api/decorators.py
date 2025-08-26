import json
import inspect
import asyncio
from functools import wraps
from typing import Any, Callable
from fastapi import HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from ..cache import get_redis_client


def cache_response(cache_key_prefix: str, ttl: int = 300, response_model: Any = None):
    """
    Caches the response of an endpoint in Redis.
    Ensures type consistency whether fresh or cached.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(request: Request, *args, **kwargs):
            return await _handle_cache(
                func, request, args, kwargs, cache_key_prefix, ttl, response_model, is_async=True
            )

        @wraps(func)
        def sync_wrapper(request: Request, *args, **kwargs):
            return asyncio.run(
                _handle_cache(
                    func,
                    request,
                    args,
                    kwargs,
                    cache_key_prefix,
                    ttl,
                    response_model,
                    is_async=False,
                )
            )

        return async_wrapper if is_async else sync_wrapper

    return decorator


async def _handle_cache(
    func, request: Request, args, kwargs, prefix, ttl, response_model, is_async: bool
):
    redis_client = kwargs.get("redis_client") or get_redis_client()

    # Build a more specific cache key
    device_id = kwargs.get("device_id")
    if device_id:
        interface_name = kwargs.get("interface_name")
        if interface_name:
            cache_key = f"{prefix}:{device_id}:{interface_name}"
        else:
            cache_key = f"{prefix}:{device_id}"
    else:
        # Fallback for endpoints without device_id, though most have it
        cache_key = f"{prefix}:{request.url.path}"


    # try cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        try:
            if isinstance(cached_data, bytes):
                cached_data = cached_data.decode("utf-8")
            return json.loads(cached_data)
        except Exception as e:
            print(f"[CacheError] Could not deserialize {cache_key}: {e}")
            redis_client.delete(cache_key)

    # Compute fresh response
    response = await func(request, *args, **kwargs) if is_async else func(request, *args, **kwargs)

    # Validate response
    if response_model:
        try:
            if getattr(response_model, "__origin__", None) is list:
                item_model = response_model.__args__[0]
                response = [item_model.model_validate(v) for v in response]
            else:
                response = response_model.model_validate(response)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Response validation failed: {e}",
            )

    # Serialize & cache
    try:
        data_to_cache = json.dumps(jsonable_encoder(response))
        redis_client.setex(cache_key, ttl, data_to_cache)
    except Exception as e:
        print(f"[CacheError] Could not serialize {cache_key}: {e}")

    return response
