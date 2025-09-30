import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';

interface InterfaceVlanConfig {
  interface_name: string;
  mode: string;
  access_vlan?: number;
  allowed_vlans?: string;
  native_vlan?: number;
}

export const useShutdownInterface = (deviceId: string | undefined) => {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (interfaceName: string) => {
      if (!token || !deviceId) {
        throw new Error('Missing token or device ID');
      }
      const response = await fetch(`/api/devices/${deviceId}/interfaces/${interfaceName}/shutdown`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to shutdown interface');
      }
      return response.json();
    },
    onSuccess: () => {
      // queryClient.invalidateQueries(['interfaces', deviceId]);
    },
  });
};

export const useNoShutdownInterface = (deviceId: string | undefined) => {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (interfaceName: string) => {
      if (!token || !deviceId) {
        throw new Error('Missing token or device ID');
      }
      const response = await fetch(`/api/devices/${deviceId}/interfaces/${interfaceName}/no-shutdown`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to no shutdown interface');
      }
      return response.json();
    },
    onSuccess: () => {
      // queryClient.invalidateQueries(['interfaces', deviceId]);
    },
  });
};

export const useConfigureInterfaceVlan = (deviceId: string | undefined) => {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (config: InterfaceVlanConfig) => {
      if (!token || !deviceId) {
        throw new Error('Missing token or device ID');
      }

      const response = await fetch(`/api/devices/${deviceId}/interfaces/vlan-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to configure interface VLAN');
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['interfacesBrief', deviceId] });
      queryClient.invalidateQueries({ queryKey: ['vlanInfo', deviceId] });
    },
  });
};

export const useSetInterfaceDescription = (deviceId: string | undefined) => {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ interfaceName, description }: { interfaceName: string; description: string }) => {
      if (!token || !deviceId) {
        throw new Error('Missing token or device ID');
      }

      const response = await fetch(`/api/devices/${deviceId}/interfaces/description`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ interface_name: interfaceName, description }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to set interface description');
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['interfacesBrief', deviceId] });
      queryClient.invalidateQueries({ queryKey: ['interfacesDescription', deviceId] });
    },
  });
};
