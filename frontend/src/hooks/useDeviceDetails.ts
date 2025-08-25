
import { useState, useEffect } from "react";
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

interface DeviceDetail extends Device {
  version: string;
  interfaces: {
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
}

// State for the hook
interface DeviceDetailsState {
  device: DeviceDetail | null;
  loading: boolean;
  errors: { [key: string]: string | null };
}

// The custom hook
export const useDeviceDetails = (deviceId: string | undefined) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState<DeviceDetailsState>({
    device: null,
    loading: true,
    errors: {},
  });

  useEffect(() => {
    if (!deviceId) {
      setState({
        device: null,
        loading: false,
        errors: { general: "No device ID provided." },
      });
      return;
    }

    const fetchAllDetails = async () => {
      if (!token) {
        logout();
        navigate("/login");
        return;
      }

      setState({
        device: null,
        loading: true,
        errors: {},
      });

      const headers = {
        Authorization: `Bearer ${token}`,
      };

      // Helper to fetch individual details and handle errors
      const fetchDetail = async (url: string, key: string) => {
        try {
          const response = await fetch(url, { headers });
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
      };

      // Fetch primary device details first
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

      // Fetch all other details in parallel using the unified /features endpoint
      const featureEndpoints = [
        { key: "hostname", feature: "system", extract: (data: any) => data?.hostname },
        { key: "active_users", feature: "active_users", extract: (data: any) => data },
        { key: "local_users", feature: "local_users", extract: (data: any) => data },
        { key: "current_clock", feature: "clock", extract: (data: any) => data },
        { key: "vlan_brief", feature: "vlans", extract: (data: any) => data },
        { key: "routing_table", feature: "routing", extract: (data: any) => data },
        { key: "acls_data", feature: "acls", extract: (data: any) => data },
        { key: "snmp_config_data", feature: "snmp", extract: (data: any) => data },
        { key: "logging_config_data", feature: "logging", extract: (data: any) => data },
        { key: "ntp_config_data", feature: "ntp", extract: (data: any) => data },
        { key: "aaa_config_data", feature: "aaa", extract: (data: any) => data },
      ];

      // Collect unique feature names to avoid redundant API calls
      const uniqueFeaturesToFetch = Array.from(new Set(featureEndpoints.map(ep => ep.feature)));

      const featureResults = await Promise.all(
        uniqueFeaturesToFetch.map(featureName =>
          fetchDetail(`/api/devices/${deviceId}/features/${featureName}`, featureName)
        )
      );

      const additionalDetails: Partial<DeviceDetail> = {};
      featureEndpoints.forEach(ep => {
        const resultIndex = uniqueFeaturesToFetch.indexOf(ep.feature);
        if (resultIndex !== -1 && featureResults[resultIndex] !== null) {
          try {
            const extractedData = ep.extract(featureResults[resultIndex]);
            if (extractedData !== undefined) {
              (additionalDetails as any)[ep.key] = extractedData;
            }
          } catch (e) {
            console.error(`Error extracting ${ep.key} from ${ep.feature} data:`, e);
            setState((prevState) => ({
              ...prevState,
              errors: {
                ...prevState.errors,
                [ep.key]: `Failed to parse ${ep.key} data.`,
              },
            }));
          }
        }
      });

      setState((prevState) => ({
        ...prevState,
        device: { ...primaryDetails, ...additionalDetails },
        loading: false,
      }));
    };

    fetchAllDetails();
  }, [deviceId, token, navigate, logout]);

  return state;
};
