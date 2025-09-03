import { QueryClient } from "@tanstack/react-query";
import type { DeviceTypeInfo } from "./types/deviceTypes.ts";

export const queryClient = new QueryClient();

export class UnauthorizedError extends Error {}

export interface Device {
  id: number;
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
  is_reachable?: boolean;
}

const getAuthHeaders = (token: string | null) => {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

export const fetchSupportedFeatures = async (token: string | null): Promise<Record<string, string[]>> => {
  const headers = getAuthHeaders(token);
  const response = await fetch("/api/devices/supported-features", { headers });

  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch supported features: ${response.statusText}`);
  }

  return response.json();
};

export type { DeviceTypeInfo };

export const fetchDeviceTypes = async (token: string | null): Promise<DeviceTypeInfo[]> => {
  const headers = getAuthHeaders(token);
  const response = await fetch("/api/devices/device-types", { headers });

  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch device types: ${response.statusText}`);
  }

  return response.json();
};

export const fetchDevices = async (token: string | null): Promise<Device[]> => {
  const headers = getAuthHeaders(token);
  const response = await fetch("/api/devices/", { headers });

  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch devices: ${response.statusText}`);
  }

  const data = await response.json();
  return Array.isArray(data) ? data : [];
};

export const deleteDevice = async (
  deviceId: string,
  token: string | null
): Promise<void> => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}`, {
    method: "DELETE",
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to delete device: ${response.statusText}`);
  }
};