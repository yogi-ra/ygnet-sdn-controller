from fastapi import APIRouter, Depends, Request
from ....controllers.cisco_ios.cisco_ios_handler import CiscoIosDeviceHandler
from ...decorators import cache_response
from ...dependencies import require_read_privileges

router = APIRouter(tags=["Device Types"])

# Map device type keys to display names
DEVICE_TYPE_DISPLAY_NAMES = {
    "cisco_ios_router": "Cisco IOS Router",
    "cisco_ios_switch": "Cisco IOS Switch",
}

@router.get("/device-types", dependencies=[Depends(require_read_privileges)])
@cache_response("device_types", ttl=300)
def get_device_types(request: Request):
    """
    Returns a list of supported device types with their display names.
    """
    device_types = []
    # List of handler classes to check for supported features
    handler_classes = [
        CiscoIosDeviceHandler,
    ]

    for device_type in DEVICE_TYPE_DISPLAY_NAMES.keys():
        device_types.append(
            {
                "key": device_type,
                "display_name": DEVICE_TYPE_DISPLAY_NAMES.get(device_type, device_type),
            }
        )

    return device_types


@router.get("/supported-features", dependencies=[Depends(require_read_privileges)])
@cache_response("supported_features", ttl=300)
def get_supported_features(request: Request):
    """
    Returns a dictionary mapping device types to their supported features.
    This endpoint helps frontend developers understand what features are available for each device type.
    """
    supported_features = {}

    # Map device types to their handler classes
    device_handler_map = {
        "cisco_ios_router": CiscoIosDeviceHandler,
        "cisco_ios_switch": CiscoIosDeviceHandler,
    }

    # For each device type in our handler map
    for device_type, handler_class in device_handler_map.items():
        try:
            # Get the supported features from the handler class
            if hasattr(handler_class, "get_supported_features"):
                features = handler_class.get_supported_features()
                # Handle the case where get_supported_features returns a tuple (view_features, action_features)
                if isinstance(features, tuple):
                    view_features, action_features = features
                    supported_features[device_type] = {
                        "view_features": view_features,
                        "action_features": action_features,
                    }
                else:
                    # For handlers that return a simple list
                    supported_features[device_type] = {"features": features}
            else:
                supported_features[device_type] = {"features": []}
        except Exception as e:
            # If there's an error getting features for a device type, log it and continue
            print(f"Error getting features for {device_type}: {e}")
            supported_features[device_type] = {"features": [], "error": str(e)}

    return supported_features

