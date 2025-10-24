from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .... import schemas
from ....config import settings
from ....crud import crud
from ....database import get_db
from ....tasks import backup_devices_task

router = APIRouter(tags=["Device Backup"])


@router.post("/backup")
def backup_devices(
    device_ids: list[int],
    db: Session = Depends(get_db)
):
    """
    Backup configurations for multiple devices to FTP server.
    
    Args:
        device_ids: List of device IDs to backup
        db: Database session
    
    Returns:
        Dict with task_id for tracking the backup job
    """
    # Validate that devices exist
    for device_id in device_ids:
        db_device = crud.get_device(db, device_id=device_id)
        if not db_device:
            raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
    
    # Get FTP configuration from settings
    ftp_config = {
        'host': settings.FTP_HOST,
        'username': settings.FTP_USERNAME,
        'password': settings.FTP_PASSWORD,
        'port': settings.FTP_PORT if hasattr(settings, 'FTP_PORT') else 21,
        'dest_dir': settings.FTP_DEST_DIR if hasattr(settings, 'FTP_DEST_DIR') else '/'
    }
    
    # Validate FTP configuration exists
    if not all([ftp_config['host'], ftp_config['username'], ftp_config['password']]):
        raise HTTPException(
            status_code=500, 
            detail="FTP configuration not properly set in environment variables"
        )
    
    # Dispatch the backup task to Celery queue
    task = backup_devices_task.delay(device_ids)
    
    # Return task_id for tracking the job
    return {"task_id": task.id}