import type { DeviceTypeInfo } from "../types/deviceTypes";

// Map device type keys to display names
export const DEVICE_TYPE_DISPLAY_NAMES: Record<string, string> = {
  "cisco_ios_router": "Cisco IOS Router",
  "cisco_ios_switch": "Cisco IOS Switch",
  "aruba_procurve": "Aruba Procurve",
  "ubiquiti_edgerouter": "Ubiquiti Edge Router",
  "ubiquiti_edgeswitch": "Ubiquiti Edge Switch",
  "ubiquiti_unifiswitch": "Ubiquiti UniFi Switch",
  "juniper_junos": "Juniper Junos"
};

/**
 * Get display name for a device type
 * @param deviceTypeKey The device type key (e.g., "cisco_ios_router")
 * @returns The user-friendly display name or the original key if not found
 */
export const getDeviceTypeDisplayName = (deviceTypeKey: string): string => {
  return DEVICE_TYPE_DISPLAY_NAMES[deviceTypeKey] || deviceTypeKey;
};

/**
 * Find display name for a device type from the device types array
 * @param deviceTypes Array of device types with key and display_name properties
 * @param deviceTypeKey The device type key to find
 * @returns The display name or the key if not found
 */
export const findDeviceTypeDisplayName = (deviceTypes: DeviceTypeInfo[], deviceTypeKey: string): string => {
  const deviceType = deviceTypes.find(type => type.key === deviceTypeKey);
  return deviceType ? deviceType.display_name : deviceTypeKey;
};