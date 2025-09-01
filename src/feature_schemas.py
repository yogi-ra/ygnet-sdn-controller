from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, Union
from enum import Enum

class TableAction(BaseModel):
    feature_name: str
    backend_method: str

class ViewFeatureType(str, Enum):
    DISPLAY_TABLE = "display_table"
    DISPLAY_TEXT = "display_text"

class ActionFeatureType(str, Enum):
    TOGGLE = "toggle"
    INPUT_TEXT = "input_text"
    SELECT_OPTION = "select_option"
    BUTTON = "button"
    TEXT_AREA = "text_area"

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

class TableAction(BaseModel):
    feature_name: str
    backend_method: str

class ViewFeatureSchema(BaseModel):
    name: str = Field(..., description="Unique identifier for the feature.")
    label: str = Field(..., description="Human-readable name for the feature.")
    description: Optional[str] = Field(None, description="Detailed explanation of the feature.")
    type: ViewFeatureType = Field(..., description="The type of UI component this feature requires.")
    backend_method: str = Field(..., description="Name of the backend method to call to get the data for this feature.")
    group: Optional[str] = Field(None, description="Optional grouping for UI organization.")
    order: Optional[int] = Field(None, description="Optional order for UI display within a group.")
    actions: Optional[List[TableAction]] = Field(None, description="Actions that can be performed on a table row.")
    row_identifier: Optional[str] = Field(None, description="The column in the table data to use as the row identifier for actions.")

class ActionFeatureSchema(BaseModel):
    name: str = Field(..., description="Unique identifier for the feature.")
    label: str = Field(..., description="Human-readable name for the feature.")
    description: Optional[str] = Field(None, description="Detailed explanation of the feature.")
    type: ActionFeatureType = Field(..., description="The type of UI component this feature requires.")
    backend_method: str = Field(..., description="Name of the backend method to call for this feature.")
    default_value: Any = Field(None, description="Default value for input fields or toggles.")
    options: Optional[List[FeatureOption]] = Field(None, description="For 'select_option' types.")
    placeholder: Optional[str] = Field(None, description="Placeholder text for 'input_text' types.")
    dependencies: Optional[List[FeatureDependency]] = Field(None, description="Rules for conditional visibility or enablement.")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules for the frontend.")
    group: Optional[str] = Field(None, description="Optional grouping for UI organization.")
    order: Optional[int] = Field(None, description="Optional order for UI display within a group.")

class HeaderFieldSchema(BaseModel):
    name: str = Field(..., description="Unique identifier for the header field.")
    label: str = Field(..., description="Human-readable label for the header field.")
    type: HeaderFieldType = Field(..., description="The type of data this header field represents.")
    value: Any = Field(None, description="The current value of the header field.")
    unit: Optional[str] = Field(None, description="Unit for statistic types.")
    format: Optional[str] = Field(None, description="Formatting hint.")
    order: Optional[int] = Field(None, description="Optional order for display within the header.")

class FeatureActionRequest(BaseModel):
    feature_name: str
    backend_method: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class FeatureActionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class DeviceFeaturesResponse(BaseModel):
    view_features: List[ViewFeatureSchema]
    action_features: List[ActionFeatureSchema]
    header_fields: List[HeaderFieldSchema]
    groups: List[str]

class SupportedFeaturesResponse(BaseModel):
    supported_features: Dict[str, List[Union[ViewFeatureSchema, ActionFeatureSchema]]]