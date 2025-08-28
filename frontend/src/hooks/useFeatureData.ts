import { useQuery } from "@tanstack/react-query";
import { fetchFeature } from "../api";
import { useAuth } from "./useAuth";

export const useFeatureData = (deviceId: string | undefined, featureName: string) => {
  const { token } = useAuth();

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<any, Error>({
    queryKey: ["featureData", deviceId, featureName],
    queryFn: () => {
      if (!deviceId || !token) {
        throw new Error("Device ID or token is missing.");
      }
      return fetchFeature(deviceId, featureName, token);
    },
    enabled: !!deviceId && !!token, // Only run the query if deviceId and token are available
  });

  return {
    data,
    isLoading,
    isError,
    error,
    refetch,
  };
};