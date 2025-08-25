from dataclasses import dataclass
from typing import Optional

@dataclass
class DeviceConnectionInfo:
    """
    Represents the connection details for a network device.
    This dataclass holds the raw information retrieved from the database.
    """

    ip_address: str
    device_type: str  # Our internal granular type (e.g., cisco_ios, juniper_junos)
    username: str
    password: str
    port: int = 22
    name: Optional[str] = None
    secret: Optional[str] = None
