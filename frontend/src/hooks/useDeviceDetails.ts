
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";

// Define the types for device data
interface Device {
  id: string;
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
  is_reachable: boolean;
}

// Make all feature-related fields optional in DeviceDetail
interface VersionInfo {
  software_image?: string;
  version?: string;
  release?: string;
  rommon?: string;
  hostname?: string;
  uptime?: string;
  uptime_years?: string;
  uptime_weeks?: string;
  uptime_days?: string;
  uptime_hours?: string;
  uptime_minutes?: string;
  reload_reason?: string;
  running_image?: string;
  hardware?: string[];
  serial?: string[];
  config_register?: string;
  mac_address?: string[];
  restarted?: string;
}

// Make all feature-related fields optional in DeviceDetail
interface DeviceDetail extends Device {
  is_reachable?: boolean; // Add is_reachable to the interface
  version?: VersionInfo;
  interfaces?: {
    interface: string;
    ip_address: string;
    status: string;
    proto: string;
  }[];
  hostname?: string;
  active_users?: any[];
  local_users?: any[];
  current_clock?: string;
  vlan_brief?: any[];
  routing_table?: any[];
  acls_data?: any[];
  snmp_config_data?: any[];
  logging_config_data?: any[];
  ntp_config_data?: any[];
  aaa_config_data?: any[];
  interfacesTrunk?: any[]; // Added this as it's used in DeviceDetailPage
}

// State for the hook
export const useDeviceDetails = (deviceId: string | undefined) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  // New: Function to fetch a specific feature
  const fetchFeature = useCallback(
    async (featureName: string, key: string) => {
      if (!token) {
        logout();
        navigate("/login");
        return null;
      }
      try {
        const response = await fetch(
          `/api/devices/${deviceId}/features/${featureName}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        if (response.status === 401) {
          logout();
          navigate("/login");
          return null;
        }
        if (!response.ok) {
          throw new Error(`Failed to fetch ${key}`);
        }
        return await response.json();
      } catch (error: any) {
        console.error(`Failed to fetch ${key}:`, error);
        throw error; // Re-throw to be caught by the component's state
      }
    },
    [deviceId, token, logout, navigate]
  );

  const queryClient = useQueryClient();

  const { data: device, isLoading: loading, error: primaryError } = useQuery<DeviceDetail, Error>({
    queryKey: ["device", deviceId],
    queryFn: async () => {
      if (!token) {
        logout();
        navigate("/login");
        throw new Error("No authentication token found. Please log in.");
      }
      const response = await fetch(`/api/devices/${deviceId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Session expired or unauthorized. Please log in again.");
      }
      if (!response.ok) {
        throw new Error(`Failed to fetch device details: ${response.statusText}`);
      }
      return response.json();
    },
    enabled: !!deviceId, // Only run query if deviceId is available
    refetchInterval: 5000, // Refetch every 5 seconds
    onError: (err) => {
        console.error("Error fetching primary device details:", err);
        if (err.message.includes("Authentication failed") || err.message.includes("Session expired")) {
          logout();
          navigate("/login");
        }
      },
    }
  );

  useEffect(() => {
    if (device && device.device_type === "aruba_procurve" && !device.version) {
      const fetchArubaVersion = async () => {
        try {
          const versionData = await fetchFeature("system", "version_info");
          if (versionData) {
            queryClient.setQueryData(["device", deviceId], (oldData: DeviceDetail | undefined) => {
              if (oldData) {
                return { ...oldData, version: versionData };
              }
              return oldData;
            });
          }
        } catch (err) {
          console.error("Failed to fetch Aruba version:", err);
        }
      };
      fetchArubaVersion();
    }
  }, [device, deviceId, fetchFeature, queryClient]);

  return {
    device: device || null,
    loading,
    errors: { primary: primaryError?.message || null },
    fetchFeature,
  };
};
