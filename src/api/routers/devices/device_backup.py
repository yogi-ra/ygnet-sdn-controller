import asyncio
import ftplib
from datetime import datetime
from typing import List, Dict, Any
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from .... import schemas
from ....config import settings
from ....crud import crud
from ....database import get_db
from ...utils import get_handler_from_device_id
from ....exceptions import DeviceConnectionError

router = APIRouter(tags=["Device Backup"])

def connect_and_backup_device(device_info, db):
    """
    Connect to a device and backup its running configuration.

    Args:
        device_info (dict): Dictionary containing device information
        db: Database session

    Returns:
        str: Running configuration if successful, None otherwise
    """
    try:
        device_id = device_info.get('id')
        handler = get_handler_from_device_id(device_id, db)

        with handler:
            # Get the running configuration
            config = handler.system.get_running_config()
            return config
    except Exception as e:
        print(f"Error backing up device {device_info.get('name', 'Unknown')}: {str(e)}")
        return None


def upload_to_ftp(ftp_config, device_name, filename, file_content):
    """
    Upload a file to FTP server, creating a device-specific directory if needed.

    Args:
        ftp_config (dict): FTP server configuration
        device_name (str): Name of the device (used for directory creation)
        filename (str): Name of the file to upload
        file_content (str): Content of the file to upload

    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        # Connect to FTP server
        ftp = ftplib.FTP()
        ftp.connect(ftp_config['host'], ftp_config.get('port', 21))
        ftp.login(ftp_config['username'], ftp_config['password'])

        # Change to destination directory if specified
        if 'dest_dir' in ftp_config:
            try:
                ftp.cwd(ftp_config['dest_dir'])
            except:
                ftp.mkd(ftp_config['dest_dir'])
                ftp.cwd(ftp_config['dest_dir'])

        # Create device-specific directory if it doesn't exist
        try:
            ftp.cwd(device_name)
        except ftplib.error_perm:
            # Directory doesn't exist, create it
            print(f"Creating directory {device_name} on FTP server")
            ftp.mkd(device_name)
            ftp.cwd(device_name)

        file_data = BytesIO(file_content.encode())
        ftp.storbinary(f'STOR {filename}', file_data)

        # Close FTP connection
        ftp.quit()

        print(f"Successfully uploaded {filename} to FTP server in directory {device_name}")
        return True
    except Exception as e:
        print(f"Failed to upload {filename} to FTP server: {str(e)}")
        return False


async def async_connect_and_backup_device(device_info, device_name, ftp_config, db):
    """
    Async wrapper for connecting and backing up a device, including FTP upload.

    Args:
        device_info (dict): Dictionary containing device information
        device_name (str): Name of the device
        ftp_config (dict): FTP configuration

    Returns:
        tuple: (device_name, success_status, error_message)
    """
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            loop = asyncio.get_event_loop()

            # Run the blocking backup operation in a thread pool
            with ThreadPoolExecutor() as executor:
                config_content = await loop.run_in_executor(executor, connect_and_backup_device, device_info, db)

            if config_content:
                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{device_name}_config_{timestamp}.cfg"

                # Run the blocking FTP upload in a thread pool
                with ThreadPoolExecutor() as executor:
                    success = await loop.run_in_executor(executor, upload_to_ftp, ftp_config, device_name, filename, config_content)

                if success:
                    print(f"Successfully backed up {device_name} configuration to FTP as {filename}")
                    return device_name, True, None
                else:
                    error_msg = f"Failed to upload {device_name} configuration to FTP"
                    print(error_msg)
            else:
                error_msg = f"Failed to retrieve configuration from {device_name}"
                print(error_msg)

        except Exception as e:
            error_msg = f"Error during backup of {device_name}: {str(e)}"
            print(error_msg)

        retry_count += 1
        if retry_count < max_retries:
            print(f"Retrying backup for {device_name} (attempt {retry_count + 1}/{max_retries})...")
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff

    # If we reach here, all retries have failed
    error_msg = f"Failed to backup {device_name} after {max_retries} retries"
    print(error_msg)
    return device_name, False, error_msg


@router.post("/backup")
async def backup_devices(
    device_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Backup configurations for multiple devices to FTP server.
    
    Args:
        device_ids: List of device IDs to backup
        background_tasks: FastAPI background tasks handler
        db: Database session
    
    Returns:
        Dict with task information
    """
    # Get device information from database
    devices = []
    for device_id in device_ids:
        db_device = crud.get_device(db, device_id=device_id)
        if not db_device:
            raise HTTPException(status_code=404, detail=f"Device with ID {device_id} not found")
        devices.append(db_device)
    
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
    
    # Create tasks for all devices to run in parallel
    tasks = []
    for device in devices:
        device_info = {
            'id': device.id,
            'name': device.name,
            'ip': device.ip_address,
            'device_type': device.device_type,
            'username': device.username,
            'password': device.password,
            'secret': device.secret,
            'port': device.port
        }
        task = async_connect_and_backup_device(device_info, device.name, ftp_config, db)
        tasks.append(task)
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful_backups = 0
    failed_backups = 0
    backup_results = []

    for result in results:
        if isinstance(result, Exception):
            print(f"Task failed with exception: {result}")
            failed_backups += 1
            backup_results.append({
                "status": "error",
                "message": str(result)
            })
        else:
            device_name, success, error_msg = result
            if success:
                successful_backups += 1
                backup_results.append({
                    "device": device_name,
                    "status": "success"
                })
            else:
                failed_backups += 1
                backup_results.append({
                    "device": device_name,
                    "status": "failed",
                    "message": error_msg
                })

    return {
        "message": f"Backup process completed. Successful: {successful_backups}, Failed: {failed_backups}",
        "results": backup_results
    }