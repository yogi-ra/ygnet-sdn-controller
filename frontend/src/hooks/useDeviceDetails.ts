import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";
import type { FeatureSchema, HeaderFieldSchema, DeviceFeaturesResponse } from "../types/featureTypes.ts";
import { HeaderFieldType } from "../types/featureTypes.ts";

export const useDeviceDetails = (deviceId: string | undefined) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  const {
    data,
    isLoading: loading,
    error: primaryError,
  } = useQuery<DeviceFeaturesResponse, Error>({
    queryKey: ["deviceFeatures", deviceId],
    queryFn: async () => {
      if (!token) {
        logout();
        navigate("/login");
        throw new Error("No authentication token found. Please log in.");
      }
      const response = await fetch(`/api/devices/${deviceId}/features`, {
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
        throw new Error(`Failed to fetch device features: ${response.statusText}`);
      }
      return response.json();
    },
    enabled: !!deviceId,
    // Removed refetchInterval for static header fields
    onError: (err) => {
      console.error("Error fetching device features:", err);
      if (err.message.includes("Authentication failed") || err.message.includes("Session expired")) {
        logout();
        navigate("/login");
      }
    },
  });

  // Separate query for device reachability
  const { data: isReachable = false } = useQuery<boolean, Error>({
    queryKey: ["deviceReachability", deviceId],
    queryFn: async () => {
      if (!token) {
        // No need to logout/navigate here, as main query handles it
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
    onError: (err) => {
      console.error("Error fetching device reachability:", err);
    },
  });

  const features: FeatureSchema[] = data?.features || [];
  const headerFields: HeaderFieldSchema[] = data?.header_fields || [];

  return {
    features,
    headerFields,
    loading,
    errors: { primary: primaryError?.message || null },
    isReachable, // Include isReachable in the returned object
  };
};