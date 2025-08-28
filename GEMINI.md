# Strategic Refactoring for Dynamic Device Features

This document outlines a comprehensive strategy to refactor the Ygnet SDN controller's backend and frontend, transitioning from a static, hardcoded feature model to a dynamic, data-driven approach. This will enable greater flexibility, extensibility, and modularity for device feature management.

## 1. Define a Universal Feature Data Structure

**Why it's crucial:**
Currently, features are likely implicitly defined within controller classes or directly in the frontend, making additions or modifications cumbersome due to changes required in multiple places. A universal data structure acts as the contract between backend and frontend, decoupling the *definition* of a feature from its *implementation* and *display*.

**Proposed Structure (Pydantic/TypeScript example):**

```python
# In src/feature_schemas.py (new file) or extending src/schemas.py

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
```

**Implementation Considerations:**
*   **Location:** A new file like `src/feature_schemas.py` is ideal for separation of concerns.
*   **Validation:** Pydantic models will provide automatic data validation.
*   **Extensibility:** The schema is designed to be easily extended.

## 2. Develop a Backend Feature API

**Why it's crucial:**
This API endpoint will become the single source of truth for the frontend regarding supported device features, eliminating hardcoded logic in the frontend.

**Endpoint Structure:**
`GET /api/devices/{device_id}/features`
*   `device_id`: The ID of the device for which features are requested.

**Backend Logic (`src/api/routers/devices.py` or new `src/api/routers/features.py`):**
1.  **Retrieve Device Information:** Fetch `device_info` (including `device_type`) from the database.
2.  **Dynamic Feature Determination:**
    *   Introduce a new mechanism (e.g., `FeatureRegistry` or an extension to `src/controllers/__init__.py`) to map `device_type` to a list of supported `FeatureSchema` instances.
    *   This registry could be populated by:
        *   **Explicit Definition:** Each device controller class (`CiscoIosRouter`, `ArubaProcurve`) defines its supported `FeatureSchema` objects.
        *   **Automated Discovery (Advanced):** Using Python reflection to discover feature-enabled methods within `src/controllers/features/` modules and generate `FeatureSchema` objects.
3.  **Filtering and Formatting:**
    *   Select relevant `FeatureSchema` objects based on `device_type`.
    *   Populate dynamic fields (e.g., current value for a "SNMP status" toggle) by making quick `send_command` calls if live data for read-only features is needed.
    *   Return a `List[FeatureSchema]` as a JSON response.

**Interaction with existing code:**
*   Leverage `get_device_handler` in `src/controllers/__init__.py` to instantiate the correct device controller.
*   Query the device controller instance for its supported features.
*   Ensure proper authentication and authorization.

## 3. Modularize Backend Feature Logic

**Why it's crucial:**
Existing feature-related code in `src/controllers/features/` modules (e.g., `get_aaa_config`, `configure_interface`) needs to be discoverable and callable by the new feature API.

**How to achieve modularity:**
*   **Feature Classes:** Each file in `src/controllers/features/{feature_category}/` represents a specific feature *implementation* for a given device platform.
*   **Standardized Interfaces:** Methods within these feature classes corresponding to `FeatureSchema` entries (e.g., `get_aaa_config`, `set_snmp_status`) must have consistent input/output types.
*   **Registration/Mapping:**
    *   `BaseDevice` or its subclasses could maintain a dictionary mapping `FeatureSchema.name` to the actual method or a callable that executes the corresponding feature logic.
    *   When the API receives a request to *perform* a feature action, it uses the `backend_method` from the `FeatureSchema` to dynamically call the appropriate method on the device controller instance.

**Example Backend Feature Logic within `CiscoIosController` (conceptual extension):**

```python
# In src/controllers/cisco_ios.py (conceptual extension)

from src.controllers.base import BaseDevice
from src.controllers.features.aaa.cisco_ios import CiscoIosAaa
# ... other feature imports

class CiscoIosRouter(BaseDevice):
    def __init__(self, device_info):
        super().__init__(device_info)
        self.aaa = CiscoIosAaa(self) # Pass self (the device handler) to the feature
        # self.interfaces = CiscoIosInterfaces(self)
        # ... other feature modules

    # New method to expose supported features
    def get_supported_features(self) -> List[FeatureSchema]:
        # This is where you define the features for Cisco IOS Router
        # You can construct these directly or load from a config/registry
        return [
            FeatureSchema(
                name="aaa_config_display",
                label="AAA Configuration",
                description="Displays the current AAA configuration.",
                type=FeatureType.DISPLAY_TEXT,
                read_only=True,
                backend_method="aaa.get_aaa_config" # Points to the method to call
            ),
            FeatureSchema(
                name="snmp_status_toggle",
                label="Enable/Disable SNMP",
                description="Toggles SNMP service on the device.",
                type=FeatureType.TOGGLE,
                default_value=True, # Will be overridden by live data
                backend_method="snmp.toggle_snmp_service" # Placeholder
            ),
            # ... more features
        ]

    # ... existing methods
```

## 4. Refactor Frontend for Dynamic Feature Consumption

**Why it's crucial:**
The frontend should not have hardcoded logic about specific device types or features. It should react to the data provided by the backend API.

**Frontend Changes (`frontend/src/pages/DeviceDetailPage.tsx` or new `components/DeviceFeatures.tsx`):**
1.  **Data Fetching:** When `DeviceDetailPage` loads, it will fetch device basic info, then make a `GET` request to `/api/devices/{device_id}/features`.
2.  **State Management:** Store the fetched `List<FeatureSchema>` in the component's state.
3.  **No More Static Imports:** Iterate over the `features` array from the backend to render components, instead of conditional rendering based on static `device_type` logic.

**Conceptual React Component:**

```tsx
// In frontend/src/components/DeviceFeatures.tsx (new component)
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FeatureSchema } from '../types/featureTypes'; // TypeScript equivalent of backend schema
import FeatureRenderer from './FeatureRenderer'; // Component to handle rendering each feature

const DeviceFeatures: React.FC = () => {
    const { deviceId } = useParams<{ deviceId: string }>();
    const [features, setFeatures] = useState<FeatureSchema[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchFeatures = async () => {
            try {
                const response = await fetch(`/api/devices/${deviceId}/features`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data: FeatureSchema[] = await response.json();
                setFeatures(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (deviceId) {
            fetchFeatures();
        }
    }, [deviceId]);

    if (loading) return <div>Loading features...</div>;
    if (error) return <div>Error loading features: {error}</div>;
    if (features.length === 0) return <div>No features available for this device.</div>;

    return (
        <div className="device-features-container">
            {features.map((feature) => (
                <FeatureRenderer key={feature.name} feature={feature} deviceId={deviceId} />
            ))}
        </div>
    );
};

export default DeviceFeatures;
```

## 5. Implement Dynamic Frontend UI Rendering

**Why it's crucial:**
This is where the magic happens. Instead of writing `if (device.type === 'cisco') { /* render Cisco UI */ }`, you'll have a generic `FeatureRenderer` component that knows how to map `FeatureType` to a specific UI component.

**Component Mapping:**
Create a dictionary or switch statement that maps `FeatureType` values (e.g., `"toggle"`, `"input_text"`) to actual React components.

```tsx
// In frontend/src/components/FeatureRenderer.tsx (new component)
import React from 'react';
import { FeatureSchema, FeatureType } from '../types/featureTypes';
import ToggleFeature from './features/ToggleFeature'; // Dedicated component for toggle
import TextInputFeature from './features/TextInputFeature'; // Dedicated component for text input
import DisplayTableFeature from './features/DisplayTableFeature'; // Dedicated component for table display
import DisplayTextFeature from './features/DisplayTextFeature';
import SelectOptionFeature from './features/SelectOptionFeature';
import ButtonFeature from './features/ButtonFeature';

interface FeatureRendererProps {
    feature: FeatureSchema;
    deviceId: string;
}

// Map FeatureType to a React component
const featureComponentMap: Record<FeatureType, React.FC<any>> = {
    [FeatureType.TOGGLE]: ToggleFeature,
    [FeatureType.INPUT_TEXT]: TextInputFeature,
    [FeatureType.DISPLAY_TABLE]: DisplayTableFeature,
    [FeatureType.DISPLAY_TEXT]: DisplayTextFeature,
    [FeatureType.SELECT_OPTION]: SelectOptionFeature,
    [FeatureType.BUTTON]: ButtonFeature,
    // Add other feature types as needed
};

const FeatureRenderer: React.FC<FeatureRendererProps> = ({ feature, deviceId }) => {
    const Component = featureComponentMap[feature.type];

    if (!Component) {
        console.warn(`No component found for feature type: ${feature.type}`);
        return null; // Or render a fallback UI
    }

    // You would also implement dependency checking here to conditionally render or disable
    // based on `feature.dependencies` and the current state of other features.

    return (
        <div className="feature-card">
            <h3>{feature.label}</h3>
            {feature.description && <p>{feature.description}</p>}
            <Component feature={feature} deviceId={deviceId} />
        </div>
    );
};

export default FeatureRenderer;
```

**Handling Dependencies:**
The `FeatureRenderer` (or individual feature components) will need logic to evaluate `feature.dependencies`, conditionally rendering or disabling components based on other features' states.

**Form Submission/Action Triggering:**
When a user interacts with a feature, the frontend will:
1.  Construct a payload with `feature.name` and the new value.
2.  Send this payload to a generic backend API endpoint (e.g., `POST /api/devices/{device_id}/action`).
3.  The backend then uses `feature.name` and the `backend_method` from `FeatureSchema` to dynamically call the correct method on the device controller.

## 6. Consider Database Schema Changes (if necessary)

**When it's necessary:**
*   **Custom Features:** If users can define their own features or templates.
*   **User-Specific Feature Settings:** If feature parameters need to be stored per device or per user.
*   **Feature-Specific Data:** If a feature generates or consumes data requiring long-term persistence (e.g., historical statistics, saved configurations).

**Potential Schema Modifications:**
*   **`features` table:** For metadata about user-defined or globally configurable features.
*   **`device_features` join table:** To link devices to specific feature configurations, or to store dynamic feature values/settings.
*   **JSONB columns:** For flexible storage of feature-related metadata or configuration directly within the `devices` table.

## 7. Plan for Migration of Existing Static Feature Definitions

**The Challenge:**
Transitioning existing hardcoded logic.

**Migration Steps:**
1.  **Identify all static feature definitions:** Locate `if device_type == 'cisco_ios_router': ...` blocks in frontend and backend.
2.  **Translate to `FeatureSchema`:** Convert these static definitions into instances of the new `FeatureSchema` Pydantic model.
3.  **Implement Backend Methods:** Ensure corresponding backend methods exist (or are refactored) in `src/controllers/features/` modules, callable by the `backend_method` specified in `FeatureSchema`.
4.  **Gradual Rollout:**
    *   Start by defining and exposing a few simple, read-only features through the new API.
    *   Gradually migrate more complex or interactive features.
    *   Maintain old and new systems in parallel temporarily if needed.

## Overall Benefits of This Strategy:

*   **Modularity:** Clear separation of feature definition, backend implementation, and frontend rendering.
*   **Extensibility:** Easier addition of new features or device types with minimal frontend changes.
*   **Maintainability:** Localized changes for each feature.
*   **Scalability:** Supports growth without a tangled codebase.
*   **Reduced Code Duplication:** Generic rendering and action handling reduce redundant code.

## 8. Implemented Changes

This section documents the changes that have been implemented to make the frontend more modular and dynamic, and confirms the completion of the dynamic feature system.

### Backend

*   **Universal Feature Data Structure (`src/feature_schemas.py`):** The `FeatureSchema` Pydantic model and related enums/models are defined, serving as the universal contract for features. **Extended with `HeaderFieldSchema` and `HeaderFieldType` for dynamic device header and general information display.**
*   **Backend Feature API (`GET /api/devices/{device_id}/features`):** This endpoint in `src/api/routers/devices.py` is implemented to return a list of `FeatureSchema` objects for a specific device, leveraging the `get_supported_features` method of the device handler. **Now also returns `HeaderFieldSchema` objects with live device data for dynamic header and general information display, including error handling for data retrieval.**
*   **Backend Feature Action API (`POST /api/devices/{device_id}/action`):** This endpoint in `src/api/routers/devices.py` is implemented to handle dynamic feature actions based on the `backend_method` defined in `FeatureSchema`.
*   **Modularized Backend Feature Logic (`get_supported_features`):** The `get_supported_features` method is implemented in device controller classes (e.g., `CiscoIosDevice` in `src/controllers/cisco_ios.py` and `ArubaProcurve` in `src/controllers/aruba_procurve.py`) to return their supported features as `FeatureSchema` objects. **`CiscoIosSystem` (`src/controllers/features/system/cisco_ios.py`) was updated to correctly retrieve hostname, uptime, and clock information.**
*   **`BaseFeature` Class and Updated Feature Base Classes:** `src/controllers/features/base.py` defines `BaseFeature`, and all existing feature base classes inherit from it, enabling introspection for feature discovery. **`BaseSystem` (`src/controllers/features/system/base.py`) was updated to include abstract methods for `get_uptime` and `get_clock` (returning string).**
*   **`GET /api/devices/supported-features` Endpoint:** This endpoint in `src/api/routers/devices.py` returns a dictionary of supported device types and their features, using introspection for dynamic discovery.
*   **Ubiquiti UniFi Controller and System Feature:** Added `src/controllers/ubiquiti_unifi.py` for Ubiquiti UniFi devices and `src/controllers/features/system/ubiquiti_unifi.py` for its system features. The `UbiquitiUniFi` controller is integrated into `src/controllers/__init__.py`.

### Frontend

*   **Dynamic Feature Consumption (`frontend/src/pages/DeviceFeaturesPage.tsx`):** This page fetches the `List[FeatureSchema]` from the backend and uses `FeatureRenderer` to dynamically render the features. **`frontend/src/pages/DeviceDetailPage.tsx` was refactored to fetch and display both `FeatureSchema` and `HeaderFieldSchema` data.**
*   **Dynamic Frontend UI Rendering (`frontend/src/components/FeatureRenderer.tsx`):** This component maps `FeatureType` to specific React components (e.g., `ToggleFeature`, `TextInputFeature`, `DisplayTableFeature`, `DisplayTextFeature`, `SelectOptionFeature`, `ButtonFeature`).
*   **Action-Oriented Feature Components:** Components like `ToggleFeature.tsx`, `TextInputFeature.tsx`, `SelectOptionFeature.tsx`, and `ButtonFeature.tsx` correctly construct and send `FeatureActionRequest` payloads to the `POST /api/devices/{device_id}/action` endpoint.
*   **Display-Only Feature Components:** Components like `DisplayTableFeature.tsx` and `DisplayTextFeature.tsx` correctly fetch and display data from the `GET /api/devices/${deviceId}/features/${feature.name}` endpoint.
*   **`ConfigContext`:** `frontend/src/context/ConfigContext.tsx` fetches and stores supported features from the backend for dynamic UI rendering.
*   **`DeviceListPage` Refactor:** `frontend/src/pages/DeviceListPage.tsx` uses the `useConfig` hook to display supported features and navigate to the `DeviceFeaturesPage`.
*   **`FeatureOutputPage`:** `frontend/src/pages/FeatureOutputPage.tsx` displays the output of a specific feature.
*   **`api.ts` Update:** `frontend/src/api.ts` includes the `FeatureSchema` interface and functions for fetching supported features, device-specific features, and individual feature outputs. **Updated `fetchDeviceFeatures` to expect and return the combined `features` and `header_fields` response.**
*   **`featureTypes.ts` Update:** **`frontend/src/types/featureTypes.ts` was updated to include `HeaderFieldSchema` and `HeaderFieldType` interfaces, and `display_location` in `FeatureSchema`.**
*   **Dynamic Device Header and General Information Tab:** **`frontend/src/pages/DeviceDetailPage.tsx` now dynamically renders device header information based on `HeaderFieldSchema` and includes a new "General Information" tab that displays these fields in a prettified format.**