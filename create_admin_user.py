from src.database import get_db
from src.crud import crud, schemas
from sqlalchemy.orm import Session


def create_admin_user():
    db: Session = next(get_db())

    username = "admin"
    password = "adminpassword"  # You can change this to a stronger password
    role = "admin"

    # Check if user already exists
    db_user = crud.get_user_by_username(db, username=username)
    if db_user:
        print(f"User '{username}' already exists.")
        return

    

    # Create user schema
    user_create = schemas.UserCreate(
        username=username,
        password=password,  # The password field in UserCreate is not hashed
        role=role,
    )

    # Create user in DB
    user = crud.create_user(db=db, user=user_create)
    print(f"Admin user '{user.username}' created successfully with role '{user.role}'.")


if __name__ == "__main__":
    create_admin_user()
