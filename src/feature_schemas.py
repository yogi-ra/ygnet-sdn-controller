from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, Union
from enum import Enum

class FeatureType(str, Enum):
    TOGGLE = "toggle"          # e.g., Enable/Disable SNMP
    INPUT_TEXT = "input_text"  # e.g., Set NTP Server IP
    DISPLAY_TABLE = "display_table" # e.g., Show ARP Table
    DISPLAY_TEXT = "display_text"  # e.g., Show Running Config snippet
    SELECT_OPTION = "select_option" # e.g., Choose VLAN mode (access/trunk)
    BUTTON = "button"          # e.g., Reload Device

class HeaderFieldType(str, Enum):
    TEXT = "text"
    STATISTIC = "statistic"
    STATUS = "status"

class FeatureOption(BaseModel):
    label: str
    value: str

class FeatureDependency(BaseModel):
    feature_name: str
    operator: Literal["equals", "not_equals"]
    value: Union[str, bool, int]

class FeatureSchema(BaseModel):
    name: str = Field(..., description="Unique identifier for the feature (e.g., 'snmp_status', 'ntp_server').")
    label: str = Field(..., description="Human-readable name for the feature (e.g., 'SNMP Status', 'NTP Server Configuration').")
    description: Optional[str] = Field(None, description="Detailed explanation of the feature.")
    type: FeatureType = Field(..., description="The type of UI component this feature requires.")
    read_only: bool = Field(False, description="If true, the feature is for display only.")
    # UI-specific properties
    default_value: Any = Field(None, description="Default value for input fields or toggles.")
    options: Optional[List[FeatureOption]] = Field(None, description="For 'select_option' types.")
    placeholder: Optional[str] = Field(None, description="Placeholder text for 'input_text' types.")
    # Dependencies and visibility rules
    dependencies: Optional[List[FeatureDependency]] = Field(None, description="Rules for conditional visibility or enablement.")
    # Backend mapping
    backend_method: Optional[str] = Field(None, description="Name of the backend method to call for this feature.")
    backend_command: Optional[str] = Field(None, description="CLI command template associated with this feature (for display or execution).")
    # Additional context for display/form rendering
    group: Optional[str] = Field(None, description="Optional grouping for UI organization (e.g., 'System', 'Network').")
    order: Optional[int] = Field(None, description="Optional order for UI display within a group.")
    display_location: Optional[Literal["header"]] = Field(None, description="If set to 'header', this feature will also be displayed in the device header.")

class HeaderFieldSchema(BaseModel):
    name: str = Field(..., description="Unique identifier for the header field (e.g., 'hostname', 'uptime').")
    label: str = Field(..., description="Human-readable label for the header field (e.g., 'Hostname', 'Uptime').")
    type: HeaderFieldType = Field(..., description="The type of data this header field represents (e.g., 'text', 'statistic', 'status').")
    value: Any = Field(None, description="The current value of the header field.")
    unit: Optional[str] = Field(None, description="Unit for statistic types (e.g., 'Mbps', '%').")
    format: Optional[str] = Field(None, description="Formatting hint (e.g., 'duration', 'percentage').")
    order: Optional[int] = Field(None, description="Optional order for display within the header.")
