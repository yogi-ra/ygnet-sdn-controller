import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';
import { taskPollingRegistry } from '../utils/taskPollingRegistry';

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
  const { interval = 1000, onSuccess, onError } = options;
  const { token } = useAuth();
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [pollingError, setPollingError] = useState<string | null>(null);
  
  // Generate a unique component ID for registry tracking
  const componentId = useRef(`${taskId}-${Date.now()}-${Math.random()}`).current;

  // Callback to handle task status updates
  const handleTaskUpdate = useCallback((status: TaskStatus, error: string | null) => {
    if (status) {
      setTaskStatus(status);
      
      if (status.status === 'SUCCESS') {
        onSuccess?.(status.result);
      } else if (status.status === 'FAILURE') {
        const errorMessage = status.error || 'Task failed';
        setPollingError(errorMessage);
        onError?.(errorMessage);
      }
    } else if (error) {
      setPollingError(error);
      onError?.(error);
    }
  }, [onSuccess, onError]);

  useEffect(() => {
    if (!taskId || !token) {
      setTaskStatus(null);
      setPollingError(null);
      return;
    }

    // Check if task is already being polled and get current status
    const currentStatus = taskPollingRegistry.getCurrentStatus(taskId);
    if (currentStatus?.status) {
      setTaskStatus(currentStatus.status);
      if (currentStatus.error) {
        setPollingError(currentStatus.error);
      }
    }

    // Subscribe to the task polling registry
    taskPollingRegistry.subscribe(taskId, componentId, handleTaskUpdate, interval);

    // Clean up on unmount or when dependencies change
    return () => {
      taskPollingRegistry.unsubscribe(taskId, componentId);
    };
  }, [taskId, token, interval, componentId, handleTaskUpdate]);

  // Loading is true when task status is PENDING or PROCESSING
  const isLoading = taskStatus?.status === 'PENDING' || taskStatus?.status === 'PROCESSING';

  // Refetch function - in the registry system, we just trigger a manual fetch
  const refetch = useCallback(async () => {
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

  return {
    taskStatus,
    taskResult: taskStatus?.status === 'SUCCESS' ? taskStatus.result : taskStatus,
    loading: isLoading,
    error: pollingError,
    refetch,
  };
};