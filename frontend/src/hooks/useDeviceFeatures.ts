import { useQuery } from "@tanstack/react-query";
import { fetchDeviceFeatures } from "../api";
import * as FeatureTypes from "../types/featureTypes.ts";
import { useAuth } from "./useAuth";

export const useDeviceFeatures = (deviceId: string | undefined) => {
  const { token } = useAuth();

  const {
    data: features,
    isLoading,
    isError,
    error,
  } = useQuery<FeatureTypes.FeatureSchema[], Error>({
    queryKey: ["deviceFeatures", deviceId],
    queryFn: () => {
      if (!deviceId || !token) {
        throw new Error("Device ID or token is missing.");
      }
      return fetchDeviceFeatures(deviceId, token);
    },
    enabled: !!deviceId && !!token, // Only run the query if deviceId and token are available
  });

  return {
    features,
    isLoading,
    isError,
    error,
  };
};
