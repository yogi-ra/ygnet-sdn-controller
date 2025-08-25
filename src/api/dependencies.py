from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import PyJWTError

from .. import crud, models
from ..database import get_db
from ..config import settings
from .utils import get_handler_from_device_id

# The tokenUrl will point to the authentication endpoint, which we will create at /api/auth/token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """
    Decodes the JWT token to get the current user. This is the base dependency.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
    except PyJWTError:
        raise credentials_exception

    user = crud.crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


def require_read_privileges(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Ensures the user is at least a 'user' (can be 'user' or 'admin').
    For GET operations.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return current_user


def require_write_privileges(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Ensures the user is an 'admin'.
    For POST, PUT, DELETE operations.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write privileges required (admin role)",
        )
    return current_user


def get_method_compatible_handler(method_name: str):
    """
    Dependency that provides a connected and compatible device handler.
    It ensures that the device connection is properly closed after the request.
    """

    def _get_handler(device_id: int, db: Session = Depends(get_db)):
        handler = get_handler_from_device_id(device_id, db)
        if not hasattr(handler, method_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Method '{method_name}' not supported for device with ID {device_id} ({handler.__class__.__name__}).",
            )
        
        try:
            handler.connect()
            yield handler
        finally:
            handler.disconnect()

    return _get_handler
