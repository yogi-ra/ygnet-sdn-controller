import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchDevices, deleteDevice, clearDeviceCache, type Device } from "../api";
import { useAuth } from "./useAuth";

export const useDevices = () => {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const {
    data: devices = [],
    isLoading,
    isError,
    error,
  } = useQuery<Device[], Error>({
    queryKey: ["devices"],
    queryFn: () => fetchDevices(token),
    refetchOnWindowFocus: false,
  });

  const deleteDeviceMutation = useMutation({
    mutationFn: (deviceId: number) => deleteDevice(deviceId.toString(), token), // Convert number to string for API call
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  const clearDeviceCacheMutation = useMutation({
    mutationFn: (deviceId: number) => clearDeviceCache(deviceId.toString(), token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  const refreshDevices = () => {
    queryClient.invalidateQueries({ queryKey: ["devices"] });
  };

  return {
    devices,
    isLoading,
    isError,
    error,
    deleteDevice: deleteDeviceMutation.mutate,
    clearDeviceCache: clearDeviceCacheMutation.mutate,
    refreshDevices,
  };
};