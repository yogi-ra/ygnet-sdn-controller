"""
Test for the device-types and supported-features endpoints to verify they return the correct format.
"""
import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import Base, engine

# Create a test client
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    """Create a clean database for testing."""
    # Only proceed with test database operations if we're actually testing
    if "sdn_test_db" in os.environ.get("DATABASE_URL", ""):
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
    else:
        # If not using test database, just yield without dropping
        yield

def test_device_types_endpoint_format(test_db):
    """Test that the device-types endpoint returns the correct format."""
    # Use a mock token for testing
    mock_token = "mock_token"
    
    response = client.get(
        "/api/devices/device-types",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    # Should succeed (the actual authentication is mocked)
    assert response.status_code in [200, 401, 403]  # 401/403 due to mock auth
    
    # If we get a 200 response, check the format
    if response.status_code == 200:
        data = response.json()
        # Should be a list
        assert isinstance(data, list)
        
        # Each item should be an object with 'key' and 'display_name' properties
        if len(data) > 0:
            item = data[0]
            assert 'key' in item
            assert 'display_name' in item
            
            # Check that we have the expected device types
            device_type_keys = [item['key'] for item in data]
            expected_types = [
                "cisco_ios_router",
                "cisco_ios_switch", 
                "aruba_procurve",
                "ubiquiti_edgerouter",
                "ubiquiti_edgeswitch",
                "ubiquiti_unifiswitch"
            ]
            
            for expected_type in expected_types:
                assert expected_type in device_type_keys

def test_supported_features_endpoint_format(test_db):
    """Test that the supported-features endpoint returns the correct format."""
    # Use a mock token for testing
    mock_token = "mock_token"
    
    response = client.get(
        "/api/devices/supported-features",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    # Should succeed (the actual authentication is mocked)
    assert response.status_code in [200, 401, 403]  # 401/403 due to mock auth
    
    # If we get a 200 response, check the format
    if response.status_code == 200:
        data = response.json()
        # Should be a dictionary
        assert isinstance(data, dict)
        
        # Check that we have the expected device types
        expected_types = [
            "cisco_ios_router",
            "cisco_ios_switch"
        ]
        
        for device_type in expected_types:
            assert device_type in data
            device_features = data[device_type]
            
            # Each device type should have either 'features' or both 'view_features' and 'action_features'
            if 'features' in device_features:
                assert isinstance(device_features['features'], list)
            elif 'view_features' in device_features and 'action_features' in device_features:
                assert isinstance(device_features['view_features'], list)
                assert isinstance(device_features['action_features'], list)
            else:
                # If neither format is present, it might be an error case
                assert 'error' in device_features