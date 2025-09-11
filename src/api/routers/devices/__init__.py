from fastapi import APIRouter
from .device_management import router as device_management_router
from .device_routes import router as device_routes_router
from .device_types import router as device_types_router
from .device_vlans import router as device_vlans_router
from .device_system import router as device_system_router
from .device_interfaces import router as device_interfaces_router
from .device_discovery import router as device_discovery_router

# Create the main devices router
router = APIRouter(prefix="/devices", tags=["Devices"])

# Include all sub-routers
# Include device_types router first to avoid conflicts with device_id route
router.include_router(device_types_router)
router.include_router(device_management_router)
router.include_router(device_routes_router)
router.include_router(device_vlans_router)
router.include_router(device_system_router)
router.include_router(device_interfaces_router)
router.include_router(device_discovery_router)