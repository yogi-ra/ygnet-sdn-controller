from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ...crud import crud
from ... import models, schemas, security
from ...database import get_db
from ...config import settings
from ...schemas import LoginRequest

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Logs in a user and returns an access token.
    """
    user = crud.get_user_by_username(db, username=data.username)
    if not user or not security.verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED
)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Creates a new user. Only accessible by admins.
    The first user ever created is automatically an admin.
    """
    if crud.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    # If no users exist in the DB, make the first one an admin.
    if db.query(models.User).count() == 0:
        user.role = "admin"
    else:
        # Ensure only admins can create other users, and they can't create admins directly this way.
        user.role = "user"

    return crud.create_user(db=db, user=user)
