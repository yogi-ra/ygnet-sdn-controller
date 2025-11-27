"""
Module for checking device reachability.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
import socket
from contextlib import closing

from .crud import crud
from .schemas import DeviceUpdate
from .device_info import DeviceConnectionInfo


async def check_device_reachability(device_id: int, db: Session):
    """
    Asynchronously checks if a device is reachable using a fast TCP check.
    This function does a direct TCP check without using the connection manager
    to avoid any blocking or resource contention.
    """
    is_reachable = False
    try:
        db_device = crud.get_device(db, device_id=device_id)
        if not db_device:
            raise Exception("Device not found")

        # Perform the TCP port check directly in a separate thread to avoid blocking
        is_reachable = await _async_tcp_check(db_device.ip_address, db_device.port)

    except Exception as e:
        print(f"An unexpected error occurred during quick reachability check for device {device_id}: {str(e)}")
        is_reachable = False

    try:
        db_device = crud.get_device(db, device_id=device_id)  # Re-fetch to ensure fresh object
        if db_device and db_device.is_reachable != is_reachable:
            # Create a DeviceUpdate object to update the reachability status
            device_update = DeviceUpdate(is_reachable=is_reachable)
            updated_device = crud.update_device(db, device_id, device_update)
            print(f"Updated reachability for device {device_id} to {is_reachable}")

            # Return the updated status directly from the database
            return updated_device.is_reachable if updated_device else is_reachable

    except Exception as e:
        print(f"Failed to update reachability status for device {device_id}: {str(e)}")

    return is_reachable


async def _async_tcp_check(ip_address: str, port: int, timeout: float = 2.0) -> bool:
    """Asynchronously perform TCP port check using thread pool to avoid blocking."""

    def sync_tcp_check():
        try:
            with closing(socket.create_connection((ip_address, port), timeout=timeout)) as sock:
                return True
        except socket.timeout:
            print(f"TCP port {port} on {ip_address} is CLOSED: connection timed out")
            return False
        except ConnectionRefusedError:
            print(f"TCP port {port} on {ip_address} is CLOSED: connection refused")
            return False
        except OSError as e:
            print(f"TCP port {port} on {ip_address} is CLOSED: OS error - {e}")
            return False
        except Exception as e:
            print(f"TCP port {port} on {ip_address} is CLOSED: unexpected error - {e}")
            return False

    # Run the potentially blocking operation in a thread pool
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_tcp_check)
        return result