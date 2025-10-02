import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchDevices, deleteDevice, type DevicesResponse } from "../api";
import { useAuth } from "./useAuth";

export const useDevices = (page: number, pageSize: number) => {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery<DevicesResponse, Error>({
    queryKey: ["devices", page, pageSize],
    queryFn: () => fetchDevices(token, (page - 1) * pageSize, pageSize),
    refetchOnWindowFocus: false,
  });

  const deleteDeviceMutation = useMutation({
    mutationFn: (deviceId: number) => deleteDevice(deviceId.toString(), token), // Convert number to string for API call
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  const refreshDevices = () => {
    queryClient.invalidateQueries({ queryKey: ["devices"] });
  };

  return {
    devices: data?.devices ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    error,
    deleteDevice: deleteDeviceMutation.mutate,
    refreshDevices,
  };
};