from sqlalchemy.orm import Session
from . import models, schemas, security

# --- User CRUD ---
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, hashed_password=hashed_password, role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- Network Device CRUD ---
def get_device(db: Session, device_id: int):
    return (
        db.query(models.NetworkDevice)
        .filter(models.NetworkDevice.id == device_id)
        .first()
    )


def get_device_by_name(db: Session, name: str):
    return (
        db.query(models.NetworkDevice).filter(models.NetworkDevice.name == name).first()
    )


def get_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.NetworkDevice).offset(skip).limit(limit).all()


def create_device(db: Session, device: schemas.DeviceCreate):
    encrypted_password = security.encrypt_data(device.password)
    encrypted_secret = security.encrypt_data(device.secret) if device.secret else None

    db_device = models.NetworkDevice(
        name=device.name,
        ip_address=device.ip_address,
        port=device.port,
        device_type=device.device_type,
        username=device.username,
        encrypted_password=encrypted_password,
        secret=encrypted_secret,
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(db: Session, device_id: int, device_update: schemas.DeviceUpdate):
    db_device = (
        db.query(models.NetworkDevice)
        .filter(models.NetworkDevice.id == device_id)
        .first()
    )
    if db_device:
        update_data = device_update.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["encrypted_password"] = security.encrypt_data(
                update_data.pop("password")
            )
        if "secret" in update_data:
            update_data["secret"] = security.encrypt_data(update_data.pop("secret"))

        for key, value in update_data.items():
            setattr(db_device, key, value)

        db.add(db_device)
        db.commit()
        db.refresh(db_device)

    return db_device


def delete_device(db: Session, device_id: int):
    db_device = (
        db.query(models.NetworkDevice)
        .filter(models.NetworkDevice.id == device_id)
        .first()
    )
    if db_device:
        db.delete(db_device)
        db.commit()

    return db_device
