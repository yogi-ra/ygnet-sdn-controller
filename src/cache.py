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


def clear_device_cache(device_id: int):
    """
    Clears all cache entries associated with a specific device.
    """
    redis_client = get_redis_client()
    deleted_count = 0

    # This pattern is used in several places
    pattern = f"device:{device_id}:*"
    keys_to_delete = [key for key in redis_client.scan_iter(pattern)]
    if keys_to_delete:
        deleted_count += redis_client.delete(*keys_to_delete)

    # Invalidate specific cache entries by prefix
    cache_prefixes = [
        "device_detail",
        "device_system_version",
        "device_system_hostname",
        "device_system_uptime",
        "device_system_clock",
        "device_interfaces_brief",
        "device_interfaces_status",
        "device_vlans_brief",
        "device_arp_table",
        "device_cdp_neighbors",
        "device_lldp_neighbors",
    ]
    for prefix in cache_prefixes:
        cache_key = f"{prefix}:{device_id}"
        if redis_client.exists(cache_key):
            deleted_count += redis_client.delete(cache_key)
    
    if deleted_count > 0:
        print(f"Invalidated {deleted_count} cache entries for device ID {device_id}.")

def clear_devices_list_cache():
    """
    Invalidates the main device list cache.
    """
    redis_client = get_redis_client()
    list_pattern = "devices_list:*"
    keys_to_delete = [key for key in redis_client.scan_iter(list_pattern)]
    if keys_to_delete:
        deleted_keys_count = redis_client.delete(*keys_to_delete)
        if deleted_keys_count > 0:
            print(f"Invalidated {deleted_keys_count} devices_list cache(s).")