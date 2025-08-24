from sqlalchemy import Column, Integer, String, ForeignKey, Boolean # Import Boolean
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)  # e.g., "admin", "user"


class NetworkDevice(Base):
    __tablename__ = "network_devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String, unique=True, index=True, nullable=False)
    port = Column(Integer, default=22, nullable=False)
    device_type = Column(String, nullable=False)  # Our internal granular type
    username = Column(String, nullable=False)
    encrypted_password = Column(String, nullable=False)  # Password is encrypted
    secret = Column(String, nullable=True)  # Enable secret, also encrypted
    is_reachable = Column(Boolean, default=False) # New field for reachability status
