# Refactoring Plan: Towards a Standardized and Extensible Architecture

This document outlines a plan to refactor the codebase to make it more standardized, extensible, and easier to maintain. The goal is to address the current issues of code tangling, lack of clear structure, and difficulty in adding new device types.

## 1. Feature-Based Architecture

We will move away from monolithic device controller classes and adopt a more granular, feature-based architecture.

### 1.1. Feature Modules

The functionality will be broken down into smaller, feature-based modules. Each module will be responsible for a specific area of device interaction. The initial set of feature modules will be:

-   `system`: For system-level information like version, hostname, and users.
-   `interfaces`: For managing device interfaces.
-   `vlans`: For managing VLANs.
-   `routing`: For routing-related information.
-   `acls`: For managing Access Control Lists.
-   `snmp`: For SNMP configuration.
-   `logging`: For logging configuration.
-   `ntp`: For NTP configuration.
-   `aaa`: For AAA configuration.

These modules will be located in `src/controllers/features/`.

### 1.2. Abstract Base Classes (ABCs)

For each feature module, we will define an Abstract Base Class (ABC) that specifies a common interface. For example, `src/controllers/features/system/base.py` will contain a `BaseSystem` class with abstract methods like `get_version_info()` and `get_hostname()`.

### 1.3. Device-Specific Implementations

For each supported device type (e.g., Cisco IOS), we will provide a concrete implementation of the feature ABCs. For example, `src/controllers/features/system/cisco_ios.py` will contain a `CiscoIosSystem` class that inherits from `BaseSystem` and implements the abstract methods for Cisco IOS devices.

## 2. Composition over Inheritance

The main device controller classes (e.g., `CiscoIosRouter`) will be composed of the feature-based classes. This means that instead of inheriting all the methods, the controller will have attributes that are instances of the feature classes.

For example, the `CiscoIosRouter` class will look something like this:

```python
from .features.system.cisco_ios import CiscoIosSystem
from .features.interfaces.cisco_ios import CiscoIosInterface
# ... other feature imports

class CiscoIosRouter(BaseDevice):
    def __init__(self, device_info):
        super().__init__(device_info)
        self.system = CiscoIosSystem(self)
        self.interfaces = CiscoIosInterface(self)
        # ... other feature initializations
```

## 3. API Simplification

The API will be simplified to interact with the new feature-based architecture.

### 3.1. Generic Feature-Based Endpoints

We will create generic, feature-based endpoints in the API. For example, instead of having a specific endpoint for every "show" command, we will have endpoints that are structured around features.

For example:
-   `GET /devices/{device_id}/system/version`
-   `GET /devices/{device_id}/interfaces/brief`
-   `GET /devices/{device_id}/vlans/brief`

This will make the API more consistent and easier to use.

### 3.2. Simplified API Router

The API router in `src/api/routers/devices.py` will be significantly simplified. The large number of repetitive endpoints will be replaced by a smaller number of generic, feature-based endpoints.

## 4. Device Type Handling

We will ensure that the `device_type` is handled correctly and consistently.

### 4.1. Distinct `device_type` for Routers and Switches

The `device_type` for our custom Cisco IOS router and switch will be distinct (e.g., `"cisco_ios_router"` and `"cisco_ios_switch"`). This will be reflected in the `DEVICE_HANDLER_MAP` in `src/controllers/__init__.py` and in the database.

### 4.2. Clear Separation of Device-Specific Logic

Device-specific logic will be clearly separated into the device-specific feature implementations. This will make it easy to add new device types without affecting the existing code.
