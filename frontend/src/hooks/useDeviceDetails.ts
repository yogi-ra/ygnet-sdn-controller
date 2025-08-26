
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
}

// Make all feature-related fields optional in DeviceDetail
interface DeviceDetail extends Device {
  version?: string;
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
interface DeviceDetailsState {
  device: DeviceDetail | null;
  loading: boolean;
  errors: { [key: string]: string | null };
  // New: Functions to fetch specific features
  fetchFeature: (featureName: string, key: string) => Promise<any>;
}

// The custom hook
export const useDeviceDetails = (deviceId: string | undefined) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState<DeviceDetailsState>({
    device: null,
    loading: true,
    errors: {},
    fetchFeature: async () => {}, // Placeholder, will be replaced in useEffect
  });

  // Helper to fetch individual details and handle errors
  const fetchDetail = useCallback(
    async (url: string, key: string) => {
      if (!token) {
        logout();
        navigate("/login");
        return null;
      }
      try {
        const response = await fetch(url, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
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
        setState((prevState) => ({
          ...prevState,
          errors: {
            ...prevState.errors,
            [key]: error.message || `Failed to fetch ${key}`,
          },
        }));
        return null;
      }
    },
    [token, logout, navigate]
  );

  // New: Function to fetch a specific feature
  const fetchFeature = useCallback(
    async (featureName: string, key: string) => {
      setState((prevState) => ({
        ...prevState,
        errors: { ...prevState.errors, [key]: null }, // Clear previous error
      }));
      const data = await fetchDetail(
        `/api/devices/${deviceId}/features/${featureName}`,
        key
      );
      if (data) {
        setState((prevState) => ({
          ...prevState,
          device: {
            ...prevState.device,
            [key]: data, // Store the fetched feature data
          } as DeviceDetail, // Type assertion
        }));
      }
      return data;
    },
    [deviceId, fetchDetail]
  );

  useEffect(() => {
    if (!deviceId) {
      setState((prevState) => ({
        ...prevState,
        device: null,
        loading: false,
        errors: { general: "No device ID provided." },
      }));
      return;
    }

    const fetchPrimaryDetails = async () => {
      setState((prevState) => ({
        ...prevState,
        device: null,
        loading: true,
        errors: {},
      }));

      const primaryDetails = await fetchDetail(
        `/api/devices/${deviceId}`,
        "primary"
      );

      if (!primaryDetails) {
        setState((prevState) => ({
          ...prevState,
          loading: false,
          errors: {
            ...prevState.errors,
            primary: "Failed to fetch essential device details.",
          },
        }));
        return;
      }

      setState((prevState) => ({
        ...prevState,
        device: primaryDetails,
        loading: false,
      }));
    };

    fetchPrimaryDetails();
  }, [deviceId, fetchDetail]);

  // Update the state with the fetchFeature function after initial render
  useEffect(() => {
    setState((prevState) => ({
      ...prevState,
      fetchFeature: fetchFeature,
    }));
  }, [fetchFeature]);


  return state;
};
