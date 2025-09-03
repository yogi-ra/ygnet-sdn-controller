import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";

interface SystemInfo {
  version?: string;
  hostname?: string;
  uptime?: string;
  clock?: string;
}

interface InterfaceBrief {
  interface: string;
  ip_address?: string;
  status: string;
  protocol: string;
}

export const useStaticDeviceDetails = (deviceId: string | undefined) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  // Fetch system information
  const {
    data: systemInfo,
    isLoading: systemLoading,
    error: systemError,
  } = useQuery<SystemInfo, Error>({
    queryKey: ["systemInfo", deviceId],
    queryFn: async () => {
      if (!token) {
        logout();
        navigate("/login");
        throw new Error("No authentication token found. Please log in.");
      }
      
      const endpoints = [
        `/api/devices/${deviceId}/system/version`,
        `/api/devices/${deviceId}/system/hostname`,
        `/api/devices/${deviceId}/system/uptime`,
        `/api/devices/${deviceId}/system/clock`
      ];
      
      const results = await Promise.all(
        endpoints.map(endpoint => 
          fetch(endpoint, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }).then(res => {
            if (res.status === 401) {
              logout();
              navigate("/login");
              throw new Error("Session expired or unauthorized. Please log in again.");
            }
            if (!res.ok) {
              throw new Error(`Failed to fetch: ${res.statusText}`);
            }
            return res.json();
          })
        )
      );
      
      return {
        version: results[0]?.version || results[0]?.software_version,
        hostname: results[1]?.hostname,
        uptime: results[2]?.uptime,
        clock: results[3]?.clock
      };
    },
    enabled: !!deviceId,
  });

  // Fetch interface brief
  const {
    data: interfaces,
    isLoading: interfacesLoading,
    error: interfacesError,
  } = useQuery<InterfaceBrief[], Error>({
    queryKey: ["interfacesBrief", deviceId],
    queryFn: async () => {
      if (!token) {
        logout();
        navigate("/login");
        throw new Error("No authentication token found. Please log in.");
      }
      
      const response = await fetch(`/api/devices/${deviceId}/interfaces/brief`, {
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
        throw new Error(`Failed to fetch interfaces: ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!deviceId,
  });

  // Fetch device reachability
  const { data: isReachable = false } = useQuery<boolean, Error>({
    queryKey: ["deviceReachability", deviceId],
    queryFn: async () => {
      if (!token) {
        throw new Error("No authentication token found.");
      }
      
      const response = await fetch(`/api/devices/${deviceId}/check-reachability`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch reachability: ${response.statusText}`);
      }
      
      return response.json();
    },
    enabled: !!deviceId,
    refetchInterval: 5000, // Poll reachability every 5 seconds
  });

  return {
    systemInfo,
    interfaces,
    isReachable,
    loading: systemLoading || interfacesLoading,
    errors: {
      system: systemError?.message || null,
      interfaces: interfacesError?.message || null,
    },
  };
};