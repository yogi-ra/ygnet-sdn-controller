# This file contains utility functions shared across the API layer.
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import crud
from ..controllers import get_device_handler, DeviceConnectionInfo
from ..security import decrypt_data


# Helper function to get a device handler from a device_id
def get_handler_from_device_id(device_id: int, db: Session):
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        device_info = DeviceConnectionInfo(
            ip_address=db_device.ip_address,
            port=db_device.port,
            device_type=db_device.device_type,
            username=db_device.username,
            password=decrypt_data(db_device.encrypted_password),
            secret=decrypt_data(db_device.secret) if db_device.secret else None,
            name=db_device.name,
        )
        return get_device_handler(device_info)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to prepare device handler: {e}"
        )

