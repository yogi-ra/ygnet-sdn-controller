# Universal Cisco IOS APIs

The following API endpoints are compatible with both Cisco IOS Routers and Cisco IOS Switches, as they are implemented in the `CiscoIosDevice` base class.

## Device Information

-   **GET /devices/{device_id}/version**
    -   Retrieves device version information.
-   **GET /devices/{device_id}/interfaces**
    -   Retrieves a brief list of IP interfaces and their status.
-   **GET /devices/{device_id}/hostname**
    -   Retrieves the device hostname.
-   **GET /devices/{device_id}/active-users**
    -   Retrieves a list of currently logged-in users (active sessions).
-   **GET /devices/{device_id}/local-users**
    -   Retrieves a list of locally configured users.
-   **GET /devices/{device_id}/clock**
    -   Retrieves the device's current clock/time.

## Configuration Fragments

-   **GET /devices/{device_id}/interfaces/{interface_name}/config**
    -   Retrieves the configuration for a specific interface.
-   **GET /devices/{device_id}/line-config**
    -   Retrieves the line configuration (vty, console).
-   **GET /devices/{device_id}/banners**
    -   Retrieves the banner configuration (MOTD, login).
-   **GET /devices/{device_id}/ntp-config**
    -   Retrieves the NTP configuration.
-   **GET /devices/{device_id}/snmp-config**
    -   Retrieves the SNMP configuration.
-   **GET /devices/{device_id}/logging-config**
    -   Retrieves the logging configuration.
-   **GET /devices/{device_id}/acls**
    -   Retrieves Access Control Lists (ACLs).
-   **GET /devices/{device_id}/aaa-config**
    -   Retrieves AAA (Authentication, Authorization, and Accounting) configuration.

## Neighbor Discovery

-   **GET /devices/{device_id}/cdp-neighbors**
    -   Retrieves CDP (Cisco Discovery Protocol) neighbors.
-   **GET /devices/{device_id}/lldp-neighbors**
    -   Retrieves LLDP (Link Layer Discovery Protocol) neighbors.
