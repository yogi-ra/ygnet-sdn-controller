// Global registry to track active task polling
// This prevents multiple components from polling the same task ID simultaneously

interface TaskPollingEntry {
  intervalId: NodeJS.Timeout;
  subscribers: Map<string, (status: any, error: string | null) => void>; // Map of component IDs to their callbacks
  lastResult: any;
  lastError: string | null;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE' | null;
}

class TaskPollingRegistry {
  private registry: Map<string, TaskPollingEntry> = new Map();
  private readonly defaultInterval: number = parseInt(import.meta.env.VITE_TASK_POLLING_INTERVAL || '1000', 10); // Configurable via environment variable, default 1 second

  /**
   * Register a component to start polling a task
   * @param taskId The ID of the task to poll
   * @param componentId A unique identifier for the component requesting polling
   * @param callback Function to call when task status updates
   * @param interval Polling interval in milliseconds
   * @returns The current task status if already being polled, otherwise null
   */
  subscribe(
    taskId: string,
    componentId: string,
    callback: (status: any, error: string | null) => void,
    interval: number = this.defaultInterval
  ): { status: any; error: string | null } | null {
    // Check if task is already being polled
    if (this.registry.has(taskId)) {
      const entry = this.registry.get(taskId)!;
      // Add this component as a subscriber with its callback
      entry.subscribers.set(componentId, callback);
      
      // Return current status if available
      if (entry.status) {
        return { status: entry.lastResult, error: entry.lastError };
      }
      return null;
    }

    // Create a new polling entry
    const intervalId = setInterval(async () => {
      try {
        const token = localStorage.getItem('token'); // Get token from auth context
        if (!token) {
          console.error('No authentication token found');
          return;
        }

        const response = await fetch(`/api/tasks/${taskId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch task status: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Update the registry with the latest status
        const entry = this.registry.get(taskId);
        if (entry) {
          entry.status = data.status;
          entry.lastResult = data;
          entry.lastError = null;

          // Notify all subscribers
          entry.subscribers.forEach((callback, subId) => {
            callback(data, null);
          });
        }

        // Stop polling if task is complete
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
          this.cleanupTask(taskId);
        }
      } catch (err: any) {
        console.error(`Error polling task ${taskId}:`, err);
        
        const entry = this.registry.get(taskId);
        if (entry) {
          entry.status = 'FAILURE';
          entry.lastError = err.message || 'Error fetching task status';
          
          // Notify all subscribers of the error
          entry.subscribers.forEach((callback, subId) => {
            callback(null, err.message || 'Error fetching task status');
          });
        }
      }
    }, interval);

    // Add to registry
    this.registry.set(taskId, {
      intervalId,
      subscribers: new Map([[componentId, callback]]),
      lastResult: null,
      lastError: null,
      status: null,
    });

    return null;
  }

  /**
   * Unregister a component from polling a task
   * @param taskId The ID of the task
   * @param componentId The component identifier
   */
  unsubscribe(taskId: string, componentId: string): void {
    if (!this.registry.has(taskId)) {
      return;
    }

    const entry = this.registry.get(taskId)!;
    entry.subscribers.delete(componentId);

    // If no more subscribers, stop polling
    if (entry.subscribers.size === 0) {
      this.cleanupTask(taskId);
    }
  }

  /**
   * Get the current status of a task if it's being polled
   * @param taskId The ID of the task
   * @returns The current task status or null if not being polled
   */
  getCurrentStatus(taskId: string): { status: any; error: string | null } | null {
    if (!this.registry.has(taskId)) {
      return null;
    }

    const entry = this.registry.get(taskId)!;
    if (!entry.status) {
      return null;
    }

    return { status: entry.lastResult, error: entry.lastError };
  }

  /**
   * Clean up a task polling entry
   * @param taskId The ID of the task to clean up
   */
  private cleanupTask(taskId: string): void {
    if (!this.registry.has(taskId)) {
      return;
    }

    const entry = this.registry.get(taskId)!;
    clearInterval(entry.intervalId);
    this.registry.delete(taskId);
  }

  /**
   * Check if a task is currently being polled
   * @param taskId The ID of the task
   * @returns True if the task is being polled, false otherwise
   */
  isPolling(taskId: string): boolean {
    return this.registry.has(taskId);
  }

  /**
   * Get the number of subscribers for a task
   * @param taskId The ID of the task
   * @returns The number of subscribers
   */
  getSubscriberCount(taskId: string): number {
    if (!this.registry.has(taskId)) {
      return 0;
    }
    return this.registry.get(taskId)!.subscribers.size;
  }
}

// Create a singleton instance
export const taskPollingRegistry = new TaskPollingRegistry();