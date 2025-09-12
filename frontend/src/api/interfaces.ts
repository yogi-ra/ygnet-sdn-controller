import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const shutdownInterface = async ({ deviceId, interfaceName }: { deviceId: string; interfaceName: string }) => {
  const response = await axios.post(`/api/devices/${deviceId}/interfaces/${interfaceName}/shutdown`);
  return response.data;
};

const noShutdownInterface = async ({ deviceId, interfaceName }: { deviceId: string; interfaceName: string }) => {
  const response = await axios.post(`/api/devices/${deviceId}/interfaces/${interfaceName}/no-shutdown`);
  return response.data;
};

export const useShutdownInterface = (deviceId: string | undefined) => {
  const queryClient = useQueryClient();
  return useMutation({ 
    mutationFn: (interfaceName: string) => shutdownInterface({ deviceId: deviceId!, interfaceName }),
    onSuccess: () => {
      // queryClient.invalidateQueries(['interfaces', deviceId]);
    },
  });
};

export const useNoShutdownInterface = (deviceId: string | undefined) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (interfaceName: string) => noShutdownInterface({ deviceId: deviceId!, interfaceName }),
    onSuccess: () => {
      // queryClient.invalidateQueries(['interfaces', deviceId]);
    },
  });
};
