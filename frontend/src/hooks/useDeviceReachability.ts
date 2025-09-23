import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import { checkDevicesReachability } from '../api';
import { useTaskPolling } from './useTaskPolling';

export const useDeviceReachability = () => {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [taskId, setTaskId] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!token) {
        throw new Error("No authentication token available");
      }
      const result = await checkDevicesReachability(token);
      return result;
    },
    onSuccess: (data) => {
      if (data && data.task_id) {
        setTaskId(data.task_id);
      }
    },
    onError: (error) => {
      console.error("Error starting reachability check:", error);
    }
  });

  const onTaskSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['devices'] });
  };

  const { taskStatus, loading, error } = useTaskPolling(taskId, {
    interval: 250,
    onSuccess: onTaskSuccess,
  });

  return {
    triggerReachabilityCheck: mutation.mutate,
    isCheckingReachability: mutation.isPending || loading,
    reachabilityCheckError: mutation.error || error,
    reachabilityTaskStatus: taskStatus,
  };
};
