import { QueryClient } from "@tanstack/react-query";
import { Device } from "./index";
import { useTaskPolling } from "../hooks/useTaskPolling";

export const queryClient = new QueryClient();

export class UnauthorizedError extends Error {}

const getAuthHeaders = (token: string | null) => {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
};

// Device System APIs
export const fetchSystemVersion = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/system/version`, { headers });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch system version: ${response.statusText}`);
  }
  
  return response.json();
};

export const fetchSystemHostname = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/system/hostname`, { headers });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch system hostname: ${response.statusText}`);
  }
  
  return response.json();
};

export const fetchSystemUptime = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/system/uptime`, { headers });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch system uptime: ${response.statusText}`);
  }
  
  return response.json();
};

export const fetchSystemClock = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/system/clock`, { headers });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch system clock: ${response.statusText}`);
  }
  
  return response.json();
};

export const rebootDevice = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/system/reboot`, {
    method: "POST",
    headers,
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to reboot device: ${response.statusText}`);
  }
  
  return response.json();
};

// Device Interface APIs
export const fetchInterfacesBrief = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/interfaces/brief`, { headers });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch interfaces brief: ${response.statusText}`);
  }
  
  return response.json();
};

export const fetchInterfacesStatus = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/interfaces/status`, { headers });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch interfaces status: ${response.statusText}`);
  }
  
  return response.json();
};

export const fetchInterfacesDescription = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/interfaces/description`, { headers });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch interfaces description: ${response.statusText}`);
  }
  
  return response.json();
};

export const setInterfaceState = async (
  deviceId: string,
  interfaceName: string,
  state: boolean,
  token: string | null
) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/interfaces/state`, {
    method: "POST",
    headers,
    body: JSON.stringify({ interface_name: interfaceName, state }),
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to set interface state: ${response.statusText}`);
  }
  
  return response.json();
};

// Device VLAN APIs
export const fetchVlansBrief = async (deviceId: string, token: string | null) => {
  const headers = getAuthHeaders(token);
  const response = await fetch(`/api/devices/${deviceId}/vlans/brief`, { headers });
  
  if (!response.ok) {
    if (response.status === 401) {
      throw new UnauthorizedError("Unauthorized");
    }
    throw new Error(`Failed to fetch VLANs brief: ${response.statusText}`);
  }
  
  return response.json();
};