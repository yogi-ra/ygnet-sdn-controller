import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

// Task types
export type TaskStatus = 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';
export type TaskType = 'INTERFACE_TOGGLE' | 'COMMAND_EXECUTION' | 'VLAN_OPERATION' | 'CACHE_CLEAR';

export interface Task {
  id: string;
  type: TaskType;
  status: TaskStatus;
  deviceId?: string;
  description: string;
  result?: any;
  error?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Action types
type TaskAction =
  | { type: 'ADD_TASK'; payload: Task }
  | { type: 'UPDATE_TASK'; payload: { id: string; updates: Partial<Task> } }
  | { type: 'REMOVE_TASK'; payload: string }
  | { type: 'CLEAR_COMPLETED_TASKS' };

// Reducer
const taskReducer = (state: Task[], action: TaskAction): Task[] => {
  switch (action.type) {
    case 'ADD_TASK':
      return [...state, action.payload];
    case 'UPDATE_TASK':
      return state.map(task => 
        task.id === action.payload.id 
          ? { ...task, ...action.payload.updates, updatedAt: new Date() }
          : task
      );
    case 'REMOVE_TASK':
      return state.filter(task => task.id !== action.payload);
    case 'CLEAR_COMPLETED_TASKS':
      return state.filter(task => task.status === 'PENDING' || task.status === 'PROCESSING');
    default:
      return state;
  }
};

// Context
interface TaskContextType {
  tasks: Task[];
  addTask: (task: Omit<Task, 'createdAt' | 'updatedAt'>) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  removeTask: (id: string) => void;
  clearCompletedTasks: () => void;
  getTask: (id: string) => Task | undefined;
  getTasksByDevice: (deviceId: string) => Task[];
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

// Provider component
export const TaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tasks, dispatch] = useReducer(taskReducer, []);
  const { token } = useAuth();

  // Add a new task
  const addTask = useCallback((task: Omit<Task, 'createdAt' | 'updatedAt'>) => {
    dispatch({
      type: 'ADD_TASK',
      payload: {
        ...task,
        createdAt: new Date(),
        updatedAt: new Date()
      }
    });
  }, []);

  // Update a task
  const updateTask = useCallback((id: string, updates: Partial<Task>) => {
    dispatch({
      type: 'UPDATE_TASK',
      payload: { id, updates }
    });
  }, []);

  // Remove a task
  const removeTask = useCallback((id: string) => {
    dispatch({
      type: 'REMOVE_TASK',
      payload: id
    });
  }, []);

  // Clear completed tasks
  const clearCompletedTasks = useCallback(() => {
    dispatch({
      type: 'CLEAR_COMPLETED_TASKS'
    });
  }, []);

  // Get a specific task
  const getTask = useCallback((id: string) => {
    return tasks.find(task => task.id === id);
  }, [tasks]);

  // Get tasks for a specific device
  const getTasksByDevice = useCallback((deviceId: string) => {
    return tasks.filter(task => task.deviceId === deviceId);
  }, [tasks]);

  // Poll for task status updates
  useEffect(() => {
    if (!token) return;

    const interval = setInterval(async () => {
      // Get all pending/processing tasks
      const activeTasks = tasks.filter(task => 
        task.status === 'PENDING' || task.status === 'PROCESSING'
      );

      // Poll for each active task
      for (const task of activeTasks) {
        try {
          const response = await fetch(`/api/tasks/${task.id}`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const data = await response.json();
            
            // Update task with new status
            if (data.status !== task.status || data.result || data.error) {
              updateTask(task.id, {
                status: data.status,
                result: data.result,
                error: data.error,
                info: data.info
              });
            }
          } else {
            // Handle error response
            updateTask(task.id, {
              status: 'FAILURE',
              error: `Failed to fetch task status: ${response.statusText}`
            });
          }
        } catch (error) {
          // Handle network error
          updateTask(task.id, {
            status: 'FAILURE',
            error: error instanceof Error ? error.message : 'Unknown error occurred'
          });
        }
      }
    }, 1000); // Poll every second

    return () => clearInterval(interval);
  }, [tasks, token, updateTask]);

  return (
    <TaskContext.Provider
      value={{
        tasks,
        addTask,
        updateTask,
        removeTask,
        clearCompletedTasks,
        getTask,
        getTasksByDevice
      }}
    >
      {children}
    </TaskContext.Provider>
  );
};

// Hook to use the task context
export const useTasks = () => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTasks must be used within a TaskProvider');
  }
  return context;
};