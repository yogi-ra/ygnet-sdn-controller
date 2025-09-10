# Strategic Refactoring for Device Features: Cisco IOS Focus

This document outlines a strategy to refactor the Ygnet SDN controller's backend and frontend, focusing specifically on Cisco IOS devices (routers and switches) to provide clear API contracts for frontend developers.

## Core Principles

1. **API-First Approach**: Define clear, simple API endpoints that frontend developers can easily consume
2. **Separation of Concerns**: Backend provides data, frontend handles presentation
3. **Performance**: Eliminate unnecessary complexity that slows down the application
4. **Maintainability**: Reduce code complexity to make the system easier to maintain
5. **Static Views**: Create device-type specific static views in the frontend for better performance and maintainability

## Simplified Backend API Structure

### Device Features Endpoint
`GET /api/devices/supported-features`

Returns a dictionary mapping device types to their supported features. This endpoint helps frontend developers understand what features are available for each device type:

```json
{
  "cisco_ios_router": {
    "view_features": [
      "system_version",
      "system_hostname",
      "system_uptime",
      "system_clock",
      "interfaces_brief",
      "interfaces_status"
    ],
    "action_features": [
      "interface_state_toggle",
      "system_reboot"
    ]
  },
  "cisco_ios_switch": {
    "view_features": [
      "system_version",
      "system_hostname",
      "system_uptime",
      "system_clock",
      "interfaces_brief",
      "interfaces_status"
    ],
    "action_features": [
      "interface_state_toggle",
      "system_reboot"
    ]
  }
}
```

### Device Detail Endpoint
`GET /api/devices/{device_id}`

Returns detailed information about a specific device including its type:

```json
{
  "id": 1,
  "name": "Router1",
  "device_type": "cisco_ios_router",
  "ip_address": "192.168.1.1",
  "port": 22,
  "username": "admin"
}
```

### Feature Data Endpoints
Each feature has its own endpoint for retrieving or manipulating data:

1. `GET /api/devices/{device_id}/system/version` - Get system version
2. `GET /api/devices/{device_id}/system/hostname` - Get system hostname
3. `GET /api/devices/{device_id}/system/uptime` - Get system uptime
4. `GET /api/devices/{device_id}/system/clock` - Get system clock
5. `GET /api/devices/{device_id}/interfaces/brief` - Get brief interface status
6. `GET /api/devices/{device_id}/interfaces/status` - Get detailed interface status
7. `POST /api/devices/{device_id}/interfaces/{interface_name}/state` - Toggle interface state
8. `POST /api/devices/{device_id}/system/reboot` - Reboot device

## Implementation Plan

### Performance Enhancements

1. **Low-Level Netmiko Prompt Checking**
   - Implement low-level prompt checking in Netmiko to reduce the delay between commands.
   - Use `global_delay_factor=0.5` and `fast_cli=True` in the `ConnectHandler` to speed up interactions.

### Backend Changes

1. **Simplify Device Feature Discovery**
   - Add `/api/devices/supported-features` endpoint to inform frontend about available features
   - Remove complex feature definition classes
   - Create simple mapping of device types to available features

2. **Create Dedicated Endpoints**
   - Create individual endpoints for each feature
   - Each endpoint returns data in a consistent format
   - Use appropriate HTTP methods (GET for read, POST for actions)

3. **Optimize Data Retrieval**
   - Direct command execution without dynamic method resolution
   - Proper error handling and logging
   - Caching where appropriate

### Frontend Changes

1. **Async Frontend**
   - Ensure all data fetching and processing is done asynchronously to prevent UI blocking.
   - Use `useEffect` and `useState` to manage loading and error states.
   - Utilize `@tanstack/react-query` for efficient server state management.

2. **User Experience**
   - Provide clear loading indicators (e.g., spinners) when data is being fetched.
   - Disable interactive elements (e.g., buttons) during loading to prevent inconsistent states.
   - Use a modern notification system (e.g., `react-hot-toast`) for user feedback instead of blocking alerts.

1. **Static Device-Type Specific Views**
   - Create separate view components for each device type (e.g., Cisco IOS Router, Cisco IOS Switch)
   - Use device type information from the backend to render the appropriate view
   - Eliminate dynamic feature rendering in favor of static, purpose-built components

2. **Improved Performance**
   - Static views load faster than dynamic feature rendering
   - Reduced JavaScript bundle size by removing dynamic feature components
   - Better code organization and maintainability

3. **Clear API Contracts**
   - Frontend developers can easily see what features are available for each device type
   - Clear mapping between device types and their respective views
   - Consistent data fetching patterns across all device types

## Benefits of Simplified Approach

* **Clarity**: Clear API contracts make development easier for both teams
* **Performance**: Static views and reduced complexity lead to faster response times
* **Maintainability**: Simpler code is easier to understand and modify
* **Flexibility**: Frontend developers can easily integrate with backend APIs
* **Reliability**: Fewer moving parts reduce potential points of failure
* **Developer Experience**: Frontend engineers have clear information about available features

## Migration Steps

1. **API Implementation**
   - Implement `/api/devices/supported-features` endpoint
   - Document API contracts clearly

2. **Frontend Implementation**
   - Create device-type specific view components
   - Implement routing logic to render appropriate views based on device type
   - Update existing components to use new static views

3. **Testing and Deployment**
   - Test all device types with their respective views
   - Verify that the new `/api/devices/supported-features` endpoint works correctly
   - Gradually deploy changes to production

This simplified approach will create a more maintainable and performant system while providing clear contracts between frontend and backend teams, focusing specifically on Cisco IOS devices.

## Refactoring Plan for File Management

To improve maintainability and scalability, we'll refactor both frontend and backend file structures:

### Backend Refactoring

1. **Organize by Device Type and Feature**
   - Restructure backend files to group by device type and feature
   - Create dedicated directories for each device type (e.g., cisco_ios, aruba_procurve)
   - Within each device type directory, organize by feature (vlans, interfaces, system, etc.)

2. **Implement Device Type Router Pattern**
   - Create a class-based approach where each device type has its own handler class
   - API endpoints will determine the device type from the device_id and route to the appropriate handler
   - This approach provides clear separation of concerns and makes it easier to add new device types

3. **Standardize API Response Format**
   - Ensure all API endpoints return consistent response formats
   - Implement proper error handling with standardized error responses

### Frontend Refactoring

1. **Component Organization by Device Type**
   - Organize frontend components by device type (Cisco IOS Router, Cisco IOS Switch, etc.)
   - Create dedicated directories for each device type's components
   - Implement static views for each device type with device-specific features

2. **API Integration Layer**
   - Create a dedicated API integration layer that abstracts API calls
   - Implement device type detection in the API layer to route calls to appropriate endpoints
   - Standardize data fetching patterns across all components

3. **Improved State Management**
   - Utilize React Context or Redux for global state management
   - Implement proper loading and error states for all API calls
   - Create reusable hooks for common data fetching patterns

This refactoring will result in a more maintainable, scalable, and performant system that's easier for developers to work with.