import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './useAuth';

export type TaskStatus = {
  task_id: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';
  result?: any;
  error?: string;
  traceback?: string;
  info?: string;
};

type UseTaskPollingOptions = {
  interval?: number;
  onSuccess?: (result: any) => void;
  onError?: (error: string) => void;
};

export const useTaskPolling = (taskId: string | null, options: UseTaskPollingOptions = {}) => {
  const { interval = 250, onSuccess, onError } = options;
  const { token } = useAuth();
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [pollingError, setPollingError] = useState<string | null>(null);

  const fetchTaskStatus = useCallback(async () => {
    if (!taskId || !token) return;

    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch task status: ${response.statusText}`);
      }

      const data: TaskStatus = await response.json();
      setTaskStatus(data);

      if (data.status === 'SUCCESS') {
        onSuccess?.(data.result);
      } else if (data.status === 'FAILURE') {
        const errorMessage = data.error || 'Task failed';
        setPollingError(errorMessage);
        onError?.(errorMessage);
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Error fetching task status';
      setPollingError(errorMessage);
      onError?.(errorMessage);
    }
  }, [taskId, token, onSuccess, onError]);

  useEffect(() => {
    if (!taskId) {
      setTaskStatus(null);
      setPollingError(null);
      return;
    }

    // Fetch immediately
    fetchTaskStatus();

    // Set up polling
    const intervalId = setInterval(fetchTaskStatus, interval);

    // Clean up interval on unmount or when taskId changes
    return () => clearInterval(intervalId);
  }, [taskId, fetchTaskStatus, interval]);

  // Loading is true when task status is PENDING or PROCESSING
  const isLoading = taskStatus?.status === 'PENDING' || taskStatus?.status === 'PROCESSING';

  return {
    taskStatus,
    loading: isLoading,
    error: pollingError,
    refetch: fetchTaskStatus,
  };
};