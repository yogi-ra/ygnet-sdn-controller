from sqlalchemy.orm import Session
from . import models, schemas, security
from .cache import get_redis_client
import json

redis_client = get_redis_client()

# --- Cache Keys (v2 for port update) ---
DEVICE_DETAIL_KEY = "device:v2:{device_id}"
DEVICE_LIST_KEY = "devices:v2:all:{skip}:{limit}"


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


# --- Network Device CRUD with Caching ---
def get_device(db: Session, device_id: int):
    cache_key = DEVICE_DETAIL_KEY.format(device_id=device_id)
    cached_device = redis_client.get(cache_key)

    if cached_device:
        # If cached, it's a schema.Device, so we need to convert it back to NetworkDevice if needed
        # For now, let's just bypass cache for this specific fix
        pass  # We will handle caching later if needed

    db_device = (
        db.query(models.NetworkDevice)
        .filter(models.NetworkDevice.id == device_id)
        .first()
    )
    if db_device:
        # Cache the schema.Device, but return the models.NetworkDevice
        device_schema = schemas.Device.from_orm(db_device)
        redis_client.set(
            cache_key, device_schema.model_dump_json(), ex=3600
        )  # Cache for 1 hour
        return db_device  # Return the SQLAlchemy model instance
    return None


def get_device_by_name(db: Session, name: str):
    cache_key = f"device:v2:name:{name}"
    cached_device = redis_client.get(cache_key)

    if cached_device:
        pass  # Bypass cache for now

    db_device = (
        db.query(models.NetworkDevice).filter(models.NetworkDevice.name == name).first()
    )
    if db_device:
        device_schema = schemas.Device.from_orm(db_device)
        redis_client.set(cache_key, device_schema.model_dump_json(), ex=3600)
        return db_device  # Return the SQLAlchemy model instance
    return None


def get_devices(db: Session, skip: int = 0, limit: int = 100):
    cache_key = DEVICE_LIST_KEY.format(skip=skip, limit=limit)
    cached_devices = redis_client.get(cache_key)

    if cached_devices:
        devices_list = json.loads(cached_devices)
        return [schemas.Device(**device) for device in devices_list]

    db_devices = db.query(models.NetworkDevice).offset(skip).limit(limit).all()
    if db_devices:
        devices_schema = [schemas.Device.from_orm(d).model_dump() for d in db_devices]
        redis_client.set(cache_key, json.dumps(devices_schema), ex=3600)
    return db_devices


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

    # Invalidate cache
    redis_client.delete(
        DEVICE_LIST_KEY.format(skip=0, limit=100)
    )  # A simple invalidation
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

        # Invalidate caches
        redis_client.delete(DEVICE_DETAIL_KEY.format(device_id=device_id))
        redis_client.delete(DEVICE_LIST_KEY.format(skip=0, limit=100))

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
