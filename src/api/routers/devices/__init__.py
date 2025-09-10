from fastapi import APIRouter
from .device_management import router as device_management_router
from .device_features import router as device_features_router
from .device_types import router as device_types_router
from .device_vlans import router as device_vlans_router
from .device_system import router as device_system_router

# Create the main devices router
router = APIRouter(prefix="/devices", tags=["Devices"])

# Include all sub-routers
# Include device_types router first to avoid conflicts with device_id route
router.include_router(device_types_router)
router.include_router(device_management_router)
router.include_router(device_features_router)
router.include_router(device_vlans_router)
router.include_router(device_system_router)