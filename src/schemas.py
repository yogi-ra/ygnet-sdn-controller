from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Union, Any
from enum import Enum


class DeviceType(str, Enum):
    CISCO_IOS_ROUTER = "cisco_ios_router"
    CISCO_IOS_SWITCH = "cisco_ios_switch"
    JUNIPER_JUNOS = "juniper_junos"
    ARUBA_PROCURVE = "aruba_procurve"
    UBIQUITI_EDGEROUTER = "ubiquiti_edgerouter"
    UBIQUITI_EDGESWITCH = "ubiquiti_edgeswitch"
    UBIQUITI_UNIFISWITCH = "ubiquiti_unifiswitch"


# --- Device Schemas ---
class DeviceBase(BaseModel):
    name: str
    ip_address: str
    port: Optional[int] = 22
    device_type: DeviceType  # Our internal granular type (e.g., cisco_ios_router)
    username: str


class DeviceCreate(DeviceBase):
    password: str
    secret: Optional[str] = None


class Device(DeviceBase):
    id: int
    is_reachable: bool = False # Add is_reachable to the schema
    model_config = ConfigDict(from_attributes=True)


class VersionInfo(BaseModel):
    software_image: Optional[str] = None
    version: Optional[str] = None
    release: Optional[str] = None
    rommon: Optional[str] = None
    hostname: Optional[str] = None
    uptime: Optional[str] = None
    uptime_years: Optional[str] = None
    uptime_weeks: Optional[str] = None
    uptime_days: Optional[str] = None
    uptime_hours: Optional[str] = None
    uptime_minutes: Optional[str] = None
    reload_reason: Optional[str] = None
    running_image: Optional[str] = None
    hardware: Optional[List[str]] = None
    serial: Optional[List[str]] = None
    config_register: Optional[str] = None
    mac_address: Optional[List[str]] = None
    restarted: Optional[str] = None

class DeviceDetail(Device):
    version: Optional[VersionInfo] = None
    interfaces: Optional[list[dict]] = None # Changed to list[dict] based on common Netmiko output for interfaces
    is_reachable: bool = False # Add is_reachable to the schema


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    device_type: Optional[DeviceType] = None  # Use the Enum here
    username: Optional[str] = None
    password: Optional[str] = None
    secret: Optional[str] = None


# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    role: Optional[str] = "user"


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


# --- Token Schemas ---

class LocalUser(BaseModel):
    line: str
    privilege: Optional[str] = None
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# --- Command Schemas ---
class CommandInput(BaseModel):
    command: Union[str, List[str]]
    is_config: bool = False


class CommandOutput(BaseModel):
    output: str


class SingleCommandOutput(BaseModel):
    output: str
    device_level: str


class MultilineCommandRequest(BaseModel):
    commands: List[List[str]] = Field(..., description="List of [command, pattern] pairs for multiline execution.")


class MultilineCommandOutput(BaseModel):
    output: str


class FeatureActionRequest(BaseModel):
    feature_name: str = Field(..., description="The name of the feature to act upon.")
    value: Any = Field(None, description="The value associated with the action (e.g., for toggles, input fields).")


# --- Cache Schemas ---
class CacheClearInput(BaseModel):
    prefixes: List[str] = Field(..., description="A list of cache key prefixes to be cleared.")
