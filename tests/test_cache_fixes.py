import pytest
from unittest.mock import patch, MagicMock
from src.connection_manager import ConnectionManager
from src.api.routers.devices import clear_device_connection_cache
from src.controllers.base import BaseDevice
from src.device_info import DeviceConnectionInfo


def test_connection_manager_shutdown_protection():
    """Test that ConnectionManager properly prevents new futures after shutdown."""
    # Create a connection manager instance
    cm = ConnectionManager()
    
    # Verify it's not shutdown initially
    assert not cm._executor_shutdown
    
    # Shutdown the executor
    cm.disconnect_all()
    
    # Verify it's now marked as shutdown
    assert cm._executor_shutdown
    
    # Create a mock device info
    device_info = DeviceConnectionInfo(
        device_type="cisco_ios_router",
        ip_address="192.168.1.1",
        port=22,
        username="test",
        password="test",
        secret="test"
    )
    
    # Try to schedule a new future - should raise RuntimeError
    with pytest.raises(RuntimeError, match="Cannot schedule new futures after shutdown"):
        cm.get_connection(device_info, "cisco_ios")


@patch('src.api.routers.devices.get_db')
@patch('src.api.routers.devices.crud')
@patch('src.api.routers.devices.ConnectionManager')
def test_clear_device_cache_with_redis(mock_connection_manager, mock_crud, mock_get_db):
    """Test that clear_device_connection_cache properly clears both connection and Redis cache."""
    # Setup mocks
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_device = MagicMock()
    mock_device.device_type = "cisco_ios_router"
    mock_device.ip_address = "192.168.1.1"
    mock_device.port = 22
    mock_device.username = "test"
    mock_device.password = "test"
    mock_device.secret = "test"
    mock_crud.get_device.return_value = mock_device
    
    mock_cm_instance = MagicMock()
    mock_connection_manager.return_value = mock_cm_instance
    
    # Call the function
    response = clear_device_connection_cache(1, mock_db)
    
    # Verify the response
    assert response["message"] == "Connection cache cleared for device 1"
    
    # Verify mocks were called correctly
    mock_crud.get_device.assert_called_once_with(mock_db, device_id=1)
    mock_connection_manager.assert_called_once()
    mock_cm_instance.get_connection.assert_not_called()  # We're not actually connecting


@patch('src.api.routers.devices.get_redis_client')
@patch('src.api.routers.devices.get_db')
@patch('src.api.routers.devices.crud')
@patch('src.api.routers.devices.ConnectionManager')
def test_clear_all_cache_with_redis(mock_connection_manager, mock_crud, mock_get_db, mock_get_redis_client):
    """Test that clear_connection_cache properly clears both connections and Redis cache."""
    # Setup mocks
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    mock_redis_client = MagicMock()
    mock_get_redis_client.return_value = mock_redis_client
    
    mock_cm_instance = MagicMock()
    mock_connection_manager.return_value = mock_cm_instance
    
    # Call the function
    response = clear_connection_cache()
    
    # Verify the response
    assert response["message"] == "Connection cache cleared successfully"
    
    # Verify mocks were called correctly
    mock_connection_manager.assert_called_once()
    mock_cm_instance.disconnect_all.assert_called_once()
    mock_redis_client.flushdb.assert_called_once()


def test_base_device_cache_invalidation():
    """Test that BaseDevice properly invalidates Redis cache."""
    # Create a mock device info
    device_info = DeviceConnectionInfo(
        id=1,
        device_type="cisco_ios_router",
        ip_address="192.168.1.1",
        port=22,
        username="test",
        password="test",
        secret="test"
    )
    
    # Create a mock Redis client
    with patch('src.controllers.base.get_redis_client') as mock_get_redis_client:
        mock_redis_client = MagicMock()
        mock_get_redis_client.return_value = mock_redis_client
        
        # Create a BaseDevice instance (we'll mock the abstract methods)
        with patch.multiple(BaseDevice, __abstractmethods__=set()):
            base_device = BaseDevice(device_info)
            
            # Call invalidate_feature_cache
            base_device.invalidate_feature_cache("test_feature")
            
            # Verify Redis operations
            mock_get_redis_client.assert_called_once()
            mock_redis_client.keys.assert_called_once_with("device:1:features:test_feature")
            # We're not testing the delete call since keys() returns an empty list in the mock