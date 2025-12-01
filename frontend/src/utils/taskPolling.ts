/**
 * Utility functions for polling task status
 */
import { API_BASE_URL } from '../api';

export interface TaskStatus {
  task_id: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';
  result?: any;
  error?: string;
  traceback?: string;
  info?: string;
}

/**
 * Polls a task status endpoint until the task completes or fails
 * @param taskId - The ID of the task to poll
 * @param token - Authentication token
 * @param interval - Polling interval in milliseconds (default: 1000)
 * @param maxAttempts - Maximum number of polling attempts (default: 30)
 * @returns Promise that resolves with the final task status
 */
export async function pollTaskStatus(
  taskId: string,
  token: string,
  interval: number = parseInt(import.meta.env.VITE_TASK_POLLING_INTERVAL || '1000', 10),
  maxAttempts: number = 30
): Promise<TaskStatus> {
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch task status: ${response.statusText}`);
      }
      
      const taskStatus: TaskStatus = await response.json();
      
      // If task is completed (success or failure), return the result
      if (taskStatus.status === 'SUCCESS' || taskStatus.status === 'FAILURE') {
        return taskStatus;
      }
      
      // If still processing, wait and try again
      await new Promise(resolve => setTimeout(resolve, interval));
      attempts++;
    } catch (error) {
      console.error('Error polling task status:', error);
      throw error;
    }
  }
  
  // If we've exceeded max attempts, throw an error
  throw new Error(`Task polling timed out after ${maxAttempts} attempts`);
}

/**
 * Executes a task and polls for its completion
 * @param endpoint - API endpoint to call to start the task
 * @param token - Authentication token
 * @param body - Request body (if any)
 * @param options - Additional options for polling
 * @returns Promise that resolves with the task result
 */
export async function executeTaskAndPoll(
  endpoint: string,
  token: string,
  body?: any,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    interval?: number;
    maxAttempts?: number;
  } = {}
): Promise<any> {
  const { method = 'POST', interval = parseInt(import.meta.env.VITE_TASK_POLLING_INTERVAL || '1000', 10), maxAttempts = 30 } = options;
  
  try {
    // Start the task
    const response = await fetch(endpoint, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      ...(body && { body: JSON.stringify(body) }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Failed to start task: ${response.statusText}`);
    }
    
    const taskData = await response.json();
    const taskId = taskData.task_id;
    
    if (!taskId) {
      throw new Error('Task ID not found in response');
    }
    
    // Poll for task completion
    const taskStatus = await pollTaskStatus(taskId, token, interval, maxAttempts);
    
    if (taskStatus.status === 'SUCCESS') {
      return taskStatus.result;
    } else {
      throw new Error(taskStatus.error || 'Task failed');
    }
  } catch (error) {
    console.error('Error executing task:', error);
    throw error;
  }
}