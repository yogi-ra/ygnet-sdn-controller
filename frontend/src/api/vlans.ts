import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';
import { queryClient } from '../hooks/useAuthQueryClient';

export const useAssignPortToVlan = (deviceId: string | undefined) => {
  const { token } = useAuth();

  console.log('useAssignPortToVlan - queryClient:', queryClient);

  return useMutation({
    client: queryClient, // Explicitly pass the queryClient
    mutationFn: async ({ vlanId, port }: { vlanId: string; port: string }) => {
      if (!token || !deviceId) {
        throw new Error('Missing token or device ID');
      }

      const response = await fetch(`/api/devices/${deviceId}/vlans/${vlanId}/assign-port`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ port }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to assign port to VLAN');
      }

      return response.json();
    },
    onSuccess: () => {
      console.log('Port assignment successful, will re-fetch VLANs later.');
      // queryClient.invalidateQueries(['vlanInfo', deviceId]); // Re-enable if the error is gone
    },
  });
};
