import logging
from sqlalchemy.orm import Session
from src.crud import crud
from src.device_info import DeviceConnectionInfo
from src.controllers import get_device_handler
from src.security import decrypt_data
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Helper function to get a device handler from a device_id
def get_handler_from_device_id(device_id: int, db: Session):
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        decrypted_password = decrypt_data(db_device.password)
        if decrypted_password is None:
            raise HTTPException(status_code=500, detail="Failed to decrypt device password. Check encryption key.")
        decrypted_secret = decrypt_data(db_device.secret) if db_device.secret else None

        device_info = DeviceConnectionInfo(
            ip_address=db_device.ip_address,
            port=db_device.port,
            device_type=db_device.device_type,
            username=db_device.username,
            password=decrypted_password,
            secret=decrypted_secret,
            name=db_device.name,
        )
        return get_device_handler(device_info)
    except Exception as e:
        logger.exception(f"Failed to prepare device handler for device ID {device_id}") # Log full traceback
        raise HTTPException(
            status_code=500, detail=f"Failed to prepare device handler: {e}"
        )

