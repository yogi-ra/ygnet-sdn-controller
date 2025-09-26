import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Container,
  Card,
  Row,
  Col,
  Alert,
  Spinner,
  Form,
  Button,
  Badge,
  Table,
  Tabs,
  Tab,
  Toast,
  InputGroup,
  Modal,
} from "react-bootstrap";
import { useAuth } from "../../hooks/useAuth";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAssignPortToVlan, useChangeVlanName, useCreateVlan, useDeleteVlan } from '../../api/vlans';
import { useConfigureInterfaceVlan } from '../../api/interfaces';
import { useTaskPolling } from "../../hooks/useTaskPolling";

// Separate hook for system information with lazy loading
const useSystemInfo = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean, deviceData: any) => {
  // Return the version information from the passed device data instead of making another request
  return {
    data: deviceData?.version || {},
    isLoading: false,
    error: null
  };
};

// Separate hook for clock information with task-based fetching and localStorage caching
const useClockInfo = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [clockData, setClockData] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = deviceId ? `clock_${deviceId}` : null;

  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(taskId, {
    interval: 250,
    onSuccess: (result) => {
      // Handle the case where result is a string directly (clock data)
      if (typeof result === 'string') {
        setClockData(result || "N/A");
        if (cacheKey) {
            localStorage.setItem(cacheKey, result || "N/A");
        }
      } else if (result && typeof result === 'object' && result.clock) {
        // Handle the case where result is an object with a clock property
        setClockData(result.clock || "N/A");
        if (cacheKey) {
            localStorage.setItem(cacheKey, result.clock || "N/A");
        }
      } else {
        setClockData("N/A");
      }
      // Clear the task ID to stop polling
      setTaskId(null);
      setLoading(false);
    },
    onError: (err) => {
      setError(err);
      // Clear the task ID to stop polling
      setTaskId(null);
      setLoading(false);
    }
  });

  const fetchClockInfo = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null); // Reset task ID before new request

      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
            setClockData(cachedData);
            setLoading(false);
            return;
        }
      }
      
      const response = await fetch(`/api/devices/${deviceId}/system/clock`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Session expired or unauthorized. Please log in again.");
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch clock info: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // If we get a task_id, start polling
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (data && data.clock) {
        // If we get direct data, use it
        setClockData(data.clock || "N/A");
        if (cacheKey) {
            localStorage.setItem(cacheKey, data.clock || "N/A");
        }
        setLoading(false);
      } else {
        // Handle case where we get an unexpected response
        setClockData("N/A");
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch clock information");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  // Reset state when deviceId or enabled changes
  useEffect(() => {
    setTaskId(null);
    if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
            setClockData(cachedData);
        } else {
            setClockData(null);
        }
    } else {
        setClockData(null);
    }
    setLoading(false);
    setError(null);
  }, [deviceId, enabled, cacheKey]);

  // Fetch data when enabled and device is reachable
  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchClockInfo();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchClockInfo]);

  const clearCache = useCallback(() => {
    if (cacheKey) {
        localStorage.removeItem(cacheKey);
        setClockData(null);
    }
  }, [cacheKey]);

  return {
    data: clockData,
    isFetching: loading || taskLoading,
    error: error || taskError,
    refetch: fetchClockInfo,
    clearCache
  };
};

// Separate hook for interfaces with task-based fetching and localStorage caching
const useInterfaces = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [interfacesData, setInterfacesData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = deviceId ? `interfaces_${deviceId}` : null;

  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(taskId, {
    interval: 250,
    onSuccess: (result) => {
      // Handle the case where result is an array directly (interfaces data)
      if (Array.isArray(result)) {
        setInterfacesData(result);
        // Cache the result in localStorage
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setInterfacesData([]);
      }
      // Clear the task ID to stop polling
      setTaskId(null);
      setLoading(false);
    },
    onError: (err) => {
      setError(err);
      // Clear the task ID to stop polling
      setTaskId(null);
      setLoading(false);
    }
  });

  const fetchInterfaces = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null); // Reset task ID before new request

      // Check if data exists in localStorage cache
      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          const parsedData = JSON.parse(cachedData);
          setInterfacesData(parsedData);
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`/api/devices/${deviceId}/interfaces/brief`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Session expired or unauthorized. Please log in again.");
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch interfaces: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // If we get a task_id, start polling
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        // If we get direct data, use it
        setInterfacesData(data);
        // Cache the result in localStorage
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        // Handle case where we get an unexpected response
        setInterfacesData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch interfaces");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  // Reset state when deviceId or enabled changes
  useEffect(() => {
    setTaskId(null);
    // Check for cached data when component mounts
    if (cacheKey) {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        setInterfacesData(JSON.parse(cachedData));
      } else {
        setInterfacesData(null);
      }
    } else {
      setInterfacesData(null);
    }
    setLoading(false);
    setError(null);
  }, [deviceId, enabled, cacheKey]);

  // Fetch data when enabled and device is reachable
  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchInterfaces();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchInterfaces]);

  // Function to clear cache
  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setInterfacesData(null); // Reset to null to trigger a refetch
    }
  }, [cacheKey]);

  return {
    data: interfacesData,
    isFetching: loading || taskLoading,
    error: error || taskError,
    refetch: fetchInterfaces,
    clearCache
  };
};

// Separate hook for VLAN information with task-based fetching and localStorage caching
const useVlanInfo = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [vlanData, setVlanData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = deviceId ? `vlans_${deviceId}` : null;

  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(taskId, {
    interval: 250,
    onSuccess: (result) => {
      // Handle the case where result is an array directly (VLAN data)
      if (Array.isArray(result)) {
        setVlanData(result);
        // Cache the result in localStorage
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setVlanData([]);
      }
      // Clear the task ID to stop polling
      setTaskId(null);
      setLoading(false);
    },
    onError: (err) => {
      setError(err);
      // Clear the task ID to stop polling
      setTaskId(null);
      setLoading(false);
    }
  });

  const fetchVlanInfo = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null); // Reset task ID before new request

      // Check if data exists in localStorage cache
      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          const parsedData = JSON.parse(cachedData);
          setVlanData(parsedData);
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`/api/devices/${deviceId}/vlans/brief`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Session expired or unauthorized. Please log in again.");
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch VLANs: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // If we get a task_id, start polling
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        // If we get direct data, use it
        setVlanData(data);
        // Cache the result in localStorage
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        // Handle case where we get an unexpected response
        setVlanData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch VLANs");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  // Reset state when deviceId or enabled changes
  useEffect(() => {
    setTaskId(null);
    // Check for cached data when component mounts
    if (cacheKey) {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        setVlanData(JSON.parse(cachedData));
      } else {
        setVlanData(null);
      }
    } else {
      setVlanData(null);
    }
    setLoading(false);
    setError(null);
  }, [deviceId, enabled, cacheKey]);

  // Fetch data when enabled and device is reachable
  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchVlanInfo();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchVlanInfo]);

  // Function to clear cache
  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setVlanData(null); // Reset to null to trigger a refetch
    }
  }, [cacheKey]);

  return {
    data: vlanData,
    isFetching: loading || taskLoading,
    error: error || taskError,
    refetch: fetchVlanInfo,
    clearCache
  };
};

// Separate hook for ARP table with task-based fetching and localStorage caching
const useArpTable = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [arpData, setArpData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = deviceId ? `arp_${deviceId}` : null;

  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(taskId, {
    interval: 250,
    onSuccess: (result) => {
      // Handle the case where result is an array directly (ARP data)
      if (Array.isArray(result)) {
        setArpData(result);
        // Cache the result in localStorage
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setArpData([]);
      }
      // Clear the task ID to stop polling
      setTaskId(null);
      setLoading(false);
    },
    onError: (err) => {
      setError(err);
      // Clear the task ID to stop polling
      setTaskId(null);
      setLoading(false);
    }
  });

  const fetchArpTable = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null); // Reset task ID before new request

      // Check if data exists in localStorage cache
      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          const parsedData = JSON.parse(cachedData);
          setArpData(parsedData);
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`/api/devices/${deviceId}/arp`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Session expired or unauthorized. Please log in again.");
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch ARP table: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // If we get a task_id, start polling
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        // If we get direct data, use it
        setArpData(data);
        // Cache the result in localStorage
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        // Handle case where we get an unexpected response
        setArpData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch ARP table");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  // Reset state when deviceId or enabled changes
  useEffect(() => {
    setTaskId(null);
    // Check for cached data when component mounts
    if (cacheKey) {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        setArpData(JSON.parse(cachedData));
      } else {
        setArpData(null);
      }
    } else {
      setArpData(null);
    }
    setLoading(false);
    setError(null);
  }, [deviceId, enabled, cacheKey]);

  // Fetch data when enabled and device is reachable
  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchArpTable();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchArpTable]);

  // Function to clear cache
  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setArpData(null); // Reset to null to trigger a refetch
    }
  }, [cacheKey]);

  return {
    data: arpData,
    isFetching: loading || taskLoading,
    error: error || taskError,
    refetch: fetchArpTable,
    clearCache
  };
};

// Separate hook for CDP neighbors with task-based fetching and localStorage caching
const useCdpNeighbors = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [cdpData, setCdpData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = deviceId ? `cdp_${deviceId}` : null;

  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(taskId, {
    interval: 250,
    onSuccess: (result) => {
      if (Array.isArray(result)) {
        setCdpData(result);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setCdpData([]);
      }
      setTaskId(null);
      setLoading(false);
    },
    onError: (err) => {
      setError(err);
      setTaskId(null);
      setLoading(false);
    }
  });

  const fetchCdpNeighbors = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null);

      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          setCdpData(JSON.parse(cachedData));
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`/api/devices/${deviceId}/cdp`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Session expired or unauthorized. Please log in again.");
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch CDP neighbors: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        setCdpData(data);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        setCdpData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch CDP neighbors");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  useEffect(() => {
    setTaskId(null);
    if (cacheKey) {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        setCdpData(JSON.parse(cachedData));
      } else {
        setCdpData(null);
      }
    } else {
      setCdpData(null);
    }
    setLoading(false);
    setError(null);
  }, [deviceId, enabled, cacheKey]);

  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchCdpNeighbors();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchCdpNeighbors]);

  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setCdpData(null);
    }
  }, [cacheKey]);

  return {
    data: cdpData,
    isFetching: loading || taskLoading,
    error: error || taskError,
    refetch: fetchCdpNeighbors,
    clearCache
  };
};

// Separate hook for LLDP neighbors with task-based fetching and localStorage caching
const useLldpNeighbors = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [lldpData, setLldpData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = deviceId ? `lldp_${deviceId}` : null;

  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(taskId, {
    interval: 250,
    onSuccess: (result) => {
      if (Array.isArray(result)) {
        setLldpData(result);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setLldpData([]);
      }
      setTaskId(null);
      setLoading(false);
    },
    onError: (err) => {
      setError(err);
      setTaskId(null);
      setLoading(false);
    }
  });

  const fetchLldpNeighbors = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null);

      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          setLldpData(JSON.parse(cachedData));
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`/api/devices/${deviceId}/lldp`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Session expired or unauthorized. Please log in again.");
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch LLDP neighbors: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        setLldpData(data);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        setLldpData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch LLDP neighbors");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  useEffect(() => {
    setTaskId(null);
    if (cacheKey) {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        setLldpData(JSON.parse(cachedData));
      } else {
        setLldpData(null);
      }
    } else {
      setLldpData(null);
    }
    setLoading(false);
    setError(null);
  }, [deviceId, enabled, cacheKey]);

  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchLldpNeighbors();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchLldpNeighbors]);

  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setLldpData(null);
    }
  }, [cacheKey]);

  return {
    data: lldpData,
    isFetching: loading || taskLoading,
    error: error || taskError,
    refetch: fetchLldpNeighbors,
    clearCache
  };
};

// Helper function to determine if interface is administratively up
const isInterfaceAdminUp = (status: string) => {
  // Interface is administratively down only if explicitly marked as such
  return !status?.toLowerCase().includes("administratively down");
};

const CiscoIosSwitchDetailPage = ({ device }: { device: any }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState("overview");
  const [activeDiscoveryTab, setActiveDiscoveryTab] = useState('arp');
  const [activeVlanTab, setActiveVlanTab] = useState('create-vlan');
  
  // Device reachability (always loaded)
  const { data: isReachable = false } = useQuery<boolean, Error>({
    queryKey: ["deviceReachability", id],
    queryFn: async () => {
      if (!token) {
        throw new Error("No authentication token found.");
      }

      const response = await fetch(`/api/devices/${id}/check-reachability`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch reachability: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: !!id && device?.is_reachable !== false, // Only enabled if device is not explicitly offline
    initialData: device?.is_reachable, // Use initial data from passed device object
    refetchInterval: 5000, // Poll reachability every 5 seconds
  });
  
  // Task state
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [taskAction, setTaskAction] = useState<string | null>(null);
  
  // Use task polling hook
  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(currentTaskId, {
    interval: 1000,
    onSuccess: () => {
      // Invalidate relevant queries to refresh data after task completion
      if (taskAction === 'toggleInterface') {
        queryClient.invalidateQueries({ queryKey: ["interfacesBrief", id] });
      } else if (taskAction === 'assignPortToVlan' || taskAction === 'changeVlanName' || 
                 taskAction === 'createVlan' || taskAction === 'deleteVlan' || 
                 taskAction === 'configureInterfaceVlan') {
        queryClient.invalidateQueries({ queryKey: ["vlanInfo", id] });
      } else if (taskAction === 'executeCommand') {
        // No specific invalidation needed for command execution
      }
    }
  });
  
  // Fetch interfaces once for both interfaces and VLANs tabs to avoid duplicate API calls
  const { data: interfaces, isFetching: interfacesLoading, error: interfacesError, refetch: refetchInterfaces, clearCache: clearInterfacesCache } = useInterfaces(id, activeTab === "interfaces" || activeTab === "vlans", isReachable);
  
  // Lazy load data based on active tab
  const { data: systemInfo, isLoading: systemLoading, error: systemError } = useSystemInfo(id, activeTab === "overview", isReachable, device);
  const { data: clockInfo, isFetching: clockLoading, error: clockError, refetch: refetchClockInfo, clearCache: clearClockCache } = useClockInfo(id, activeTab === "overview", isReachable);
  const { data: vlanInfo, isFetching: vlanLoading, error: vlanError, refetch: refetchVlanInfo, clearCache: clearVlanInfoCache } = useVlanInfo(id, activeTab === "vlans", isReachable);
  const { data: arpTable, isFetching: arpLoading, error: arpError, refetch: refetchArpTable, clearCache: clearArpTableCache } = useArpTable(id, activeTab === 'discovery' && activeDiscoveryTab === 'arp', isReachable);
  const { data: cdpNeighbors, isFetching: cdpLoading, error: cdpError, refetch: refetchCdpNeighbors, clearCache: clearCdpCache } = useCdpNeighbors(id, activeTab === 'discovery' && activeDiscoveryTab === 'cdp', isReachable);
  const { data: lldpNeighbors, isFetching: lldpLoading, error: lldpError, refetch: refetchLldpNeighbors, clearCache: clearLldpCache } = useLldpNeighbors(id, activeTab === 'discovery' && activeDiscoveryTab === 'lldp', isReachable);
  
  // Command execution state
  const [command, setCommand] = useState("");
  const [isConfigCommand, setIsConfigCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);
  const [deviceLevel, setDeviceLevel] = useState<string | null>(null);
  const [executingCommand, setExecutingCommand] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);
  const [selectedPorts, setSelectedPorts] = useState<{ [key: string]: string }>({});
  
  // Interface toggle loading states
  const [togglingInterfaces, setTogglingInterfaces] = useState<{ [key: string]: boolean }>({});
  
  // Toast state
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState<'success' | 'danger'>('success');

  // VLAN specific state from VlanConfiguration
  const [interfaceConfigs, setInterfaceConfigs] = useState<{ [key: string]: any }>({});
  const [vlanNameEdits, setVlanNameEdits] = useState<{ [key: string]: string }>({});
  const [newVlanId, setNewVlanId] = useState<string>('');
  const [newVlanName, setNewVlanName] = useState<string>('');
  const [isCreatingVlan, setIsCreatingVlan] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [vlanToDelete, setVlanToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [applyingConfigs, setApplyingConfigs] = useState<{ [key: string]: boolean }>({});

  // API hooks
  const assignPortToVlan = useAssignPortToVlan(id);
  const changeVlanName = useChangeVlanName(id);
  const createVlan = useCreateVlan(id);
  const deleteVlan = useDeleteVlan(id);
  const configureInterfaceVlan = useConfigureInterfaceVlan(id);

  const handleRefresh = () => {
    clearInterfacesCache();
    clearVlanInfoCache();
    clearArpTableCache();
    clearCdpCache();
    clearLldpCache();
    clearClockCache();
    refetchInterfaces();
    refetchVlanInfo();
    refetchArpTable();
    refetchCdpNeighbors();
    refetchLldpNeighbors();
    refetchClockInfo();
  };

  useEffect(() => {
    if (interfaces && interfaces.length > 0) {
      const initialConfigs: { [key: string]: any } = {};
      interfaces.forEach(iface => {
        const ifaceName = iface.interface || iface.intf;
        if (ifaceName) {
          initialConfigs[ifaceName] = {
            mode: 'access', // Default to access mode
            accessVlan: '',
            allowedVlans: '',
            nativeVlan: '',
          };
        }
      });
      setInterfaceConfigs(initialConfigs);
    }
  }, [interfaces]);

  // Handle tab changes
  const handleTabSelect = (tabKey: string | null) => {
    if (tabKey) {
      setActiveTab(tabKey);
    }
  };

  const handleInterfaceConfigChange = (ifaceName: string, field: string, value: string) => {
    setInterfaceConfigs(prev => ({
      ...prev,
      [ifaceName]: {
        ...prev[ifaceName],
        [field]: value,
      },
    }));
  };

  const handleVlanNameChange = (vlanId: string, newName: string) => {
    setVlanNameEdits(prev => ({
      ...prev,
      [vlanId]: newName
    }));
  };

  const handleCancelVlanNameEdit = (vlanId: string) => {
    setVlanNameEdits(prev => {
      const newState = { ...prev };
      delete newState[vlanId];
      return newState;
    });
  };

  const handleSaveVlanName = async (vlanId: string) => {
    const newName = vlanNameEdits[vlanId];
    if (!id || newName === undefined) return;

    try {
      // Set the task action immediately to show loading state
      const response = await changeVlanName.mutateAsync({ vlanId, newName });
      setCurrentTaskId(response.task_id);
      setTaskAction('changeVlanName');
    } catch (err: any) {
      // On error, show toast and reset task state
      setToastMessage(`Error changing VLAN name: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    }
  };

  const handleCreateVlan = async () => {
    if (!id || !newVlanId) return;

    setIsCreatingVlan(true);
    try {
      const vlanIdNum = parseInt(newVlanId);
      if (isNaN(vlanIdNum)) {
        throw new Error("VLAN ID must be a number");
      }

      setTaskAction('createVlan');
      const response = await createVlan.mutateAsync({ id: vlanIdNum, name: newVlanName || undefined });
      setCurrentTaskId(response.task_id);
    } catch (err: any) {
      setToastMessage(`Error creating VLAN: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    } finally {
      setIsCreatingVlan(false);
    }
  };

  const openDeleteModal = (vlanId: string) => {
    setVlanToDelete(vlanId);
    setShowDeleteModal(true);
  };

  const confirmDeleteVlan = async () => {
    if (!vlanToDelete) return;

    setIsDeleting(true);
    try {
      setTaskAction('deleteVlan');
      const response = await deleteVlan.mutateAsync(vlanToDelete);
      setCurrentTaskId(response.task_id);
    } catch (err: any) {
      setToastMessage(`Error deleting VLAN: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
      setVlanToDelete(null);
    }
  };

  // Handle interface toggle
  const handleToggleInterface = async (interfaceName: string, currentState: string) => {
    if (!id || !token) return;
    
    // Set loading state for this interface
    setTogglingInterfaces(prev => ({ ...prev, [interfaceName]: true }));
    setTaskAction('toggleInterface');
    
    // Toggle based on administrative state, not operational state
    const newState = !isInterfaceAdminUp(currentState);
    
    try {
      const response = await fetch(`/api/devices/${id}/interfaces/state`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ interface_name: interfaceName, state: newState }),
      });
      
      if (response.status === 401) {
        logout();
        navigate("/login");
        return;
      }
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to toggle interface");
      }
      
      const data = await response.json();
      setCurrentTaskId(data.task_id);
      
      
    } catch (err: any) {
      console.error("Error toggling interface:", err);
      // Show error toast
      setToastMessage(`Error toggling interface: ${err.message || "Unknown error"}`);
      setToastVariant('danger');
      setShowToast(true);
      // Reset loading state for this interface
      setTogglingInterfaces(prev => {
        const newState = { ...prev };
        delete newState[interfaceName];
        return newState;
      });
    }
  };

  const handlePortSelection = (vlanId: string, port: string) => {
    setSelectedPorts(prev => ({
      ...prev,
      [vlanId]: port
    }));
  };

  const handleAssignPort = async (vlanId: string) => {
    const port = selectedPorts[vlanId];
    if (!id || !port) return;

    try {
      setTaskAction('assignPortToVlan');
      const response = await assignPortToVlan.mutateAsync({ vlanId, port });
      setCurrentTaskId(response.task_id);
    } catch (err: any) {
      console.error("Error assigning port to VLAN:", err);
      setToastMessage(`Error assigning port to VLAN: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    }
  };

  const handleApplyInterfaceConfig = async (ifaceName: string) => {
    const config = interfaceConfigs[ifaceName];
    if (!id || !config) return;

    setApplyingConfigs(prev => ({ ...prev, [ifaceName]: true }));

    try {
      const vlanConfig: any = {
        interface_name: ifaceName,
        mode: config.mode,
      };

      if (config.mode === 'access') {
        if (config.accessVlan) {
          vlanConfig.access_vlan = parseInt(config.accessVlan);
        }
      } else if (config.mode === 'trunk') {
        if (config.allowedVlans) {
          vlanConfig.allowed_vlans = config.allowedVlans;
        }
        if (config.nativeVlan) {
          vlanConfig.native_vlan = parseInt(config.nativeVlan);
        }
      }

      setTaskAction('configureInterfaceVlan');
      const response = await configureInterfaceVlan.mutateAsync(vlanConfig);
      setCurrentTaskId(response.task_id);
    } catch (err: any) {
      setToastMessage(`Error configuring interface: ${err.message || "Unknown error"}`);
      setToastVariant('danger');
      setShowToast(true);
    } finally {
      setApplyingConfigs(prev => {
        const newState = { ...prev };
        delete newState[ifaceName];
        return newState;
      });
    }
  };

  const handleExecuteCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    setExecutingCommand(true);
    setCommandOutput(null);
    setCommandError(null);
    setTaskAction('executeCommand');

    const endpoint = `/api/devices/${id}/execute-command`;
    const payload = { command, is_config: isConfigCommand };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.status === 401) {
        logout();
        navigate("/login");
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to execute command");
      }

      setCurrentTaskId(data.task_id);
    } catch (err: any) {
      setCommandError(err.message || "An unknown error occurred.");
      setExecutingCommand(false);
      setCommand("");
    }
  };

  

  // Handle task completion
  useEffect(() => {
    if (taskStatus?.status === 'SUCCESS') {
      if (taskAction === 'toggleInterface') {
        // Show success toast
        setToastMessage('Interface toggled successfully');
        setToastVariant('success');
        setShowToast(true);
        
        // Reset interface loading states
        setTogglingInterfaces({});
        
        // Refresh interfaces to show latest changes
        clearInterfacesCache();
        refetchInterfaces();
      } else if (taskAction === 'assignPortToVlan') {
        setToastMessage('Successfully assigned port to VLAN');
        setToastVariant('success');
        setShowToast(true);
        
        // Refresh VLANs to show latest changes
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'changeVlanName') {
        setToastMessage(`Successfully changed VLAN name`);
        setToastVariant('success');
        setShowToast(true);
        
        // Refresh VLANs to show latest changes
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'createVlan') {
        setToastMessage('Successfully created VLAN');
        setToastVariant('success');
        setShowToast(true);
        setNewVlanId('');
        setNewVlanName('');
        
        // Refresh VLANs to show latest changes
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'deleteVlan') {
        setToastMessage('Successfully deleted VLAN');
        setToastVariant('success');
        setShowToast(true);
        
        // Refresh VLANs to show latest changes
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'configureInterfaceVlan') {
        setToastMessage('Successfully configured VLAN settings for interface');
        setToastVariant('success');
        setShowToast(true);
        
        // Refresh interfaces to show latest changes
        clearInterfacesCache();
        refetchInterfaces();
      } else if (taskAction === 'executeCommand') {
        // Handle command execution result
        // The result can be in either 'result' or 'info' field depending on how the backend formats it
        const output = taskStatus.result || taskStatus.info || "No output";
        setCommandOutput(output);
        setDeviceLevel(null); // Switch commands don't typically have a device level
        setExecutingCommand(false);
        setCommand("");
      }
      
      // Reset task state
      setCurrentTaskId(null);
      setTaskAction(null);
    } else if (taskStatus?.status === 'FAILURE') {
      // Handle task failure
      const errorMessage = taskStatus.error || 'Task failed';
      
      if (taskAction === 'toggleInterface') {
        setToastMessage(`Error toggling interface: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        setTogglingInterfaces({});
        
        // Refresh interfaces to show latest changes
        clearInterfacesCache();
        refetchInterfaces();
      } else if (taskAction === 'assignPortToVlan') {
        setToastMessage(`Error assigning port to VLAN: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        
        // Refresh VLANs to show latest changes
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'changeVlanName') {
        setToastMessage(`Error changing VLAN name: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        
        // Refresh VLANs to show latest changes
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'createVlan') {
        setToastMessage(`Error creating VLAN: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        
        // Refresh VLANs to show latest changes
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'deleteVlan') {
        setToastMessage(`Error deleting VLAN: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        
        // Refresh VLANs to show latest changes
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'configureInterfaceVlan') {
        setToastMessage(`Error configuring interface VLAN: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        
        // Refresh interfaces to show latest changes
        clearInterfacesCache();
        refetchInterfaces();
      } else if (taskAction === 'executeCommand') {
        setCommandError(errorMessage);
        setExecutingCommand(false);
        setCommand("");
      }
      
      // Reset task state
      setCurrentTaskId(null);
      setTaskAction(null);
    }
  }, [taskStatus, taskAction, vlanToDelete]);

  return (
    <Container fluid className="mt-4">
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body>
              <div className="d-flex justify-content-between align-items-start">
                <div>
                  <Card.Title as="h1" className="mb-3">
                    {device?.name || "Unknown Device"} ({device?.ip_address || "Unknown IP"})
                    <Badge bg={device?.is_reachable ? "success" : "danger"} className="ms-2">
                      {device?.is_reachable ? "Online" : "Offline"}
                    </Badge>
                  </Card.Title>
                  <Card.Subtitle className="mb-2 text-muted">
                    Device ID: {device?.id} | IP: {device?.ip_address} | Type: Cisco IOS Switch
                  </Card.Subtitle>
                </div>
                <div>
                  <Button variant="outline-primary" onClick={handleRefresh}>
                    Refresh
                  </Button>
                  <Button variant="secondary" onClick={() => navigate(-1)} className="ms-2">
                    Back to Devices
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {taskError && (
        <Row className="mb-3">
          <Col>
            <Alert variant="danger">
              Error processing task: {taskError}
            </Alert>
          </Col>
        </Row>
      )}

      <Tabs
        activeKey={activeTab}
        onSelect={handleTabSelect}
        className="mb-3"
        mountOnEnter={true}
        unmountOnExit={true}
      >
        <Tab eventKey="overview" title="Overview">
          <Row className="mb-4">
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">System Information</Card.Title>
                  {systemError ? (
                    <Alert variant="danger">
                      Error: {systemError.message}. Please try again later.
                    </Alert>
                  ) : (systemLoading || clockLoading) ? (
                    <div className="text-center">
                      <Spinner animation="border" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </Spinner>
                    </div>
                  ) : systemInfo ? (
                    <Table striped bordered hover>
                      <tbody>
                        <tr>
                          <td><strong>Hostname</strong></td>
                          <td>{systemInfo.hostname || "N/A"}</td>
                        </tr>
                        <tr>
                          <td><strong>Version</strong></td>
                          <td>{systemInfo.version || "N/A"}</td>
                        </tr>
                        <tr>
                          <td><strong>Uptime</strong></td>
                          <td>{systemInfo.uptime || "N/A"}</td>
                        </tr>
                        <tr>
                          <td><strong>Clock</strong></td>
                          <td>{clockInfo || "N/A"}</td>
                        </tr>
                      </tbody>
                    </Table>
                  ) : (
                    <Alert variant="info">No system information available.</Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="interfaces" title="Interfaces">
          <Row className="mb-4">
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">Interfaces</Card.Title>
                  {interfacesError ? (
                    <Alert variant="danger">
                      Error: {interfacesError.message}. Please try again later.
                    </Alert>
                  ) : interfacesLoading ? (
                    <div className="text-center">
                      <Spinner animation="border" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </Spinner>
                    </div>
                  ) : interfaces && interfaces.length > 0 ? (
                    <Table striped bordered hover responsive>
                      <thead>
                        <tr>
                          <th>Interface</th>
                          <th>IP Address</th>
                          <th>Status</th>
                          <th>Protocol</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {interfaces.map((iface: any, index: number) => (
                          <tr key={index}>
                            <td>{iface.interface || iface.intf || "N/A"}</td>
                            <td>{iface.ip_address || iface.ip || "N/A"}</td>
                            <td>{iface.status || "N/A"}</td>
                            <td>{iface.proto || "N/A"}</td>
                            <td>
                              <Button
                                size="sm"
                                variant={isInterfaceAdminUp(iface.status) ? "danger" : "success"}
                                onClick={() => handleToggleInterface(
                                  iface.interface || iface.intf || "",
                                  iface.status || ""
                                )}
                                disabled={!device?.is_reachable || togglingInterfaces[iface.interface || iface.intf || ""] || !!currentTaskId}
                              >
                                {(togglingInterfaces[iface.interface || iface.intf || ""] || 
                                  (currentTaskId && taskAction === 'toggleInterface')) ? (
                                  <>
                                    <Spinner
                                      as="span"
                                      animation="border"
                                      size="sm"
                                      role="status"
                                      aria-hidden="true"
                                    />
                                    <span className="visually-hidden">Loading...</span>
                                  </>
                                ) : isInterfaceAdminUp(iface.status) ? "Shut Down" : "Enable"}
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  ) : (
                    <Alert variant="info">No interfaces found.</Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="vlans" title="VLANs">
          <Tabs
            activeKey={activeVlanTab}
            onSelect={(k) => setActiveVlanTab(k || 'create-vlan')}
            className="mb-3"
            mountOnEnter
            unmountOnExit
          >
            <Tab eventKey="create-vlan" title="Create VLAN">
              <Card>
                <Card.Body>
                  <Form>
                    <Row>
                      <Col md={3}>
                        <Form.Group controlId="new-vlan-id">
                          <Form.Label>VLAN ID</Form.Label>
                          <Form.Control type="text" placeholder="Enter VLAN ID" value={newVlanId} onChange={(e) => setNewVlanId(e.target.value)} disabled={!isReachable || !!currentTaskId} />
                        </Form.Group>
                      </Col>
                      <Col md={4}>
                        <Form.Group controlId="new-vlan-name">
                          <Form.Label>VLAN Name (Optional)</Form.Label>
                          <Form.Control type="text" placeholder="Enter VLAN Name" value={newVlanName} onChange={(e) => setNewVlanName(e.target.value)} disabled={!isReachable || !!currentTaskId} />
                        </Form.Group>
                      </Col>
                      <Col md={2} className="d-flex align-items-end">
                        <Button variant="primary" onClick={handleCreateVlan} disabled={!newVlanId || !isReachable || isCreatingVlan || !!currentTaskId}>
                          {isCreatingVlan || (currentTaskId && taskAction === 'createVlan') ? <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" /> : "Create VLAN"}
                        </Button>
                      </Col>
                    </Row>
                  </Form>
                </Card.Body>
              </Card>
            </Tab>
            <Tab eventKey="vlan-list" title="VLAN List">
              <Card>
                <Card.Body>
                  {vlanError ? (
                    <Alert variant="danger">Error: {vlanError.message}</Alert>
                  ) : vlanLoading ? (
                    <div className="text-center"><Spinner animation="border" /></div>
                  ) : vlanInfo && vlanInfo.length > 0 ? (
                    <Table striped bordered hover responsive>
                      <thead>
                        <tr>
                          <th>VLAN ID</th>
                          <th>Name</th>
                          <th>Status</th>
                          <th>Ports</th>
                          <th>Assign Port</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {vlanInfo.map((vlan: any) => {
                          const vlanId = vlan.vlan_id || vlan.id;
                          const currentName = vlan.vlan_name || "N/A";
                          const isEditing = vlanNameEdits.hasOwnProperty(vlanId);
                          const editedName = vlanNameEdits[vlanId] ?? currentName;

                          return (
                            <tr key={vlanId}>
                              <td>{vlanId}</td>
                              <td>
                                {isEditing ? (
                                  <InputGroup>
                                    <Form.Control
                                      type="text"
                                      size="sm"
                                      value={editedName}
                                      onChange={(e) => handleVlanNameChange(vlanId, e.target.value)}
                                      disabled={!isReachable || !!currentTaskId}
                                    />
                                    <Button 
                                      size="sm" 
                                      variant="success" 
                                      onClick={() => handleSaveVlanName(vlanId)} 
                                      disabled={!isReachable || !!currentTaskId || (currentTaskId && taskAction === 'changeVlanName')}
                                    >
                                      {currentTaskId && taskAction === 'changeVlanName' ? <Spinner as="span" animation="border" size="sm" /> : "Save"}
                                    </Button>
                                    <Button 
                                      size="sm" 
                                      variant="outline-secondary" 
                                      onClick={() => handleCancelVlanNameEdit(vlanId)} 
                                      disabled={!!currentTaskId}
                                    >
                                      ×
                                    </Button>
                                  </InputGroup>
                                ) : (
                                  <div>
                                    {currentName}
                                    <Button size="sm" variant="outline-primary" className="ms-2" onClick={() => handleVlanNameChange(vlanId, currentName)} disabled={!isReachable || !!currentTaskId}>Edit</Button>
                                  </div>
                                )}
                              </td>
                              <td>{vlan.status || "N/A"}</td>
                              <td>{vlan.interfaces ? (Array.isArray(vlan.interfaces) ? vlan.interfaces.join(', ') : vlan.interfaces) : "N/A"}</td>
                              <td>
                                <InputGroup>
                                  <Form.Select size="sm" value={selectedPorts[vlanId] || ''} onChange={(e) => handlePortSelection(vlanId, e.target.value)} disabled={!isReachable || !!currentTaskId}>
                                    <option value="">Select Port</option>
                                    {interfaces?.map((iface: any) => (
                                      <option key={iface.interface || iface.intf} value={iface.interface || iface.intf}>{iface.interface || iface.intf}</option>
                                    ))}
                                  </Form.Select>
                                  <Button 
                                    size="sm" 
                                    variant="primary" 
                                    onClick={() => handleAssignPort(vlanId)} 
                                    disabled={!selectedPorts[vlanId] || !isReachable || !!currentTaskId || (currentTaskId && taskAction === 'assignPortToVlan')}
                                  >
                                    {currentTaskId && taskAction === 'assignPortToVlan' ? <Spinner as="span" animation="border" size="sm" /> : "+"}
                                  </Button>
                                </InputGroup>
                              </td>
                              <td>
                                <Button 
                                  size="sm" 
                                  variant="danger" 
                                  onClick={() => openDeleteModal(vlanId)} 
                                  disabled={!isReachable || isDeleting || !!currentTaskId || (currentTaskId && taskAction === 'deleteVlan')}
                                >
                                  {isDeleting && vlanToDelete === vlanId ? <Spinner as="span" animation="border" size="sm" /> : "Delete"}
                                </Button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </Table>
                  ) : (
                    <Alert variant="info">No VLAN information available.</Alert>
                  )}
                </Card.Body>
              </Card>
            </Tab>
             <Tab eventKey="interface-config" title="Interface Configuration">
                <Card>
                  <Card.Body>
                    {interfacesError ? (
                      <Alert variant="danger">Error: {interfacesError.message}</Alert>
                    ) : interfacesLoading ? (
                      <div className="text-center"><Spinner animation="border" /></div>
                    ) : interfaces && interfaces.length > 0 ? (
                      <Table striped bordered hover responsive>
                        <thead>
                          <tr>
                            <th>Interface</th>
                            <th>Port Mode</th>
                            <th>VLAN ID (Access) / Allowed VLANs (Trunk)</th>
                            <th>Native VLAN (Trunk)</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {interfaces.map((iface: any) => {
                            const ifaceName = iface.interface || iface.intf;
                            const config = interfaceConfigs[ifaceName];
                            if (!config) return null;

                            return (
                              <tr key={ifaceName}>
                                <td>{ifaceName}</td>
                                <td>
                                  <Form.Select size="sm" value={config.mode} onChange={(e) => handleInterfaceConfigChange(ifaceName, 'mode', e.target.value)} disabled={!isReachable || !!currentTaskId}>
                                    <option value="access">Access</option>
                                    <option value="trunk">Trunk</option>
                                  </Form.Select>
                                </td>
                                <td>
                                  {config.mode === 'access' ? (
                                    <Form.Control type="text" size="sm" placeholder="VLAN ID" value={config.accessVlan} onChange={(e) => handleInterfaceConfigChange(ifaceName, 'accessVlan', e.target.value)} disabled={!isReachable || !!currentTaskId} />
                                  ) : (
                                    <Form.Control type="text" size="sm" placeholder="Allowed VLANs (e.g., 10,20,30-40)" value={config.allowedVlans} onChange={(e) => handleInterfaceConfigChange(ifaceName, 'allowedVlans', e.target.value)} disabled={!isReachable || !!currentTaskId} />
                                  )}
                                </td>
                                <td>
                                  {config.mode === 'trunk' && (
                                    <Form.Control type="text" size="sm" placeholder="Native VLAN ID" value={config.nativeVlan} onChange={(e) => handleInterfaceConfigChange(ifaceName, 'nativeVlan', e.target.value)} disabled={!isReachable || !!currentTaskId} />
                                  )}
                                </td>
                                <td>
                                  <Button
                                    size="sm"
                                    variant="success"
                                    onClick={() => handleApplyInterfaceConfig(ifaceName)}
                                    disabled={!isReachable || applyingConfigs[ifaceName] || !!currentTaskId || (currentTaskId && taskAction === 'configureInterfaceVlan')}
                                  >
                                    {applyingConfigs[ifaceName] || (currentTaskId && taskAction === 'configureInterfaceVlan') ? (
                                      <>
                                        <Spinner
                                          as="span"
                                          animation="border"
                                          size="sm"
                                          role="status"
                                          aria-hidden="true"
                                        />
                                        <span className="visually-hidden">Loading...</span>
                                      </>
                                    ) : (
                                      "Apply"
                                    )}
                                  </Button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </Table>
                    ) : (
                      <Alert variant="info">No interfaces available for configuration.</Alert>
                    )}
                  </Card.Body>
                </Card>
              </Tab>
          </Tabs>
        </Tab>
        
        <Tab eventKey="discovery" title="Network Discovery">
          <Tabs
            activeKey={activeDiscoveryTab}
            onSelect={(k) => setActiveDiscoveryTab(k || 'arp')}
            className="mb-3"
            mountOnEnter={true}
            unmountOnExit={true}
          >
            <Tab eventKey="arp" title="ARP Table">
              <Row className="mb-4">
                <Col md={12}>
                  <Card>
                    <Card.Body>
                      <Card.Title as="h2">ARP Table</Card.Title>
                      {arpError ? (
                        <Alert variant="danger">
                          Error: {arpError}. Please try again later.
                        </Alert>
                      ) : arpLoading ? (
                        <div className="text-center">
                          <Spinner animation="border" role="status">
                            <span className="visually-hidden">Loading...</span>
                          </Spinner>
                        </div>
                      ) : arpTable && arpTable.length > 0 ? (
                        <Table striped bordered hover responsive>
                          <thead>
                            <tr>
                              <th>Address</th>
                              <th>MAC Address</th>
                              <th>Interface</th>
                              <th>Age</th>
                            </tr>
                          </thead>
                          <tbody>
                            {arpTable.map((entry: any, index: number) => (
                              <tr key={index}>
                                <td>{entry.ip_address || entry.address ||  "N/A"}</td>
                                <td>{entry.mac_address || entry.hardware_address || "N/A"}</td>
                                <td>{entry.interface || entry.port || "N/A"}</td>
                                <td>{entry.age || "N/A"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      ) : (
                        <Alert variant="info">No ARP entries found.</Alert>
                      )}
                    </Card.Body>
                  </Card>
                </Col>
              </Row>
            </Tab>
            <Tab eventKey="cdp" title="CDP Neighbors">
              <Row className="mb-4">
                <Col md={12}>
                  <Card>
                    <Card.Body>
                      <Card.Title as="h2">CDP Neighbors</Card.Title>
                      {cdpError ? (
                        <Alert variant="danger">
                          Error: {cdpError}. Please try again later.
                        </Alert>
                      ) : cdpLoading ? (
                        <div className="text-center">
                          <Spinner animation="border" role="status">
                            <span className="visually-hidden">Loading...</span>
                          </Spinner>
                        </div>
                      ) : cdpNeighbors && cdpNeighbors.length > 0 ? (
                        <Table striped bordered hover responsive>
                          <thead>
                            <tr>
                              <th>Device ID</th>
                              <th>Local Interface</th>
                              <th>Hold Time</th>
                              <th>Capability</th>
                              <th>Platform</th>
                              <th>Port ID</th>
                            </tr>
                          </thead>
                          <tbody>
                            {cdpNeighbors.map((neighbor: any, index: number) => (
                              <tr key={index}>
                                <td>{neighbor.device_id || "N/A"}</td>
                                <td>{neighbor.local_interface || "N/A"}</td>
                                <td>{neighbor.hold_time || "N/A"}</td>
                                <td>{neighbor.capability || "N/A"}</td>
                                <td>{neighbor.platform || "N/A"}</td>
                                <td>{neighbor.port_id || "N/A"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      ) : (
                        <Alert variant="info">No CDP neighbors found.</Alert>
                      )}
                    </Card.Body>
                  </Card>
                </Col>
              </Row>
            </Tab>
            <Tab eventKey="lldp" title="LLDP Neighbors">
              <Row className="mb-4">
                <Col md={12}>
                  <Card>
                    <Card.Body>
                      <Card.Title as="h2">LLDP Neighbors</Card.Title>
                      {lldpError ? (
                        <Alert variant="danger">
                          Error: {lldpError}. Please try again later.
                        </Alert>
                      ) : lldpLoading ? (
                        <div className="text-center">
                          <Spinner animation="border" role="status">
                            <span className="visually-hidden">Loading...</span>
                          </Spinner>
                        </div>
                      ) : lldpNeighbors && lldpNeighbors.length > 0 ? (
                        <Table striped bordered hover responsive>
                          <thead>
                            <tr>
                              <th>Device ID</th>
                              <th>Local Interface</th>
                              <th>Hold Time</th>
                              <th>Capability</th>
                              <th>Platform</th>
                              <th>Port ID</th>
                            </tr>
                          </thead>
                          <tbody>
                            {lldpNeighbors.map((neighbor: any, index: number) => (
                              <tr key={index}>
                                <td>{neighbor.device_id || "N/A"}</td>
                                <td>{neighbor.local_interface || "N/A"}</td>
                                <td>{neighbor.hold_time || "N/A"}</td>
                                <td>{neighbor.capability || "N/A"}</td>
                                <td>{neighbor.platform || "N/A"}</td>
                                <td>{neighbor.port_id || "N/A"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      ) : (
                        <Alert variant="info">No LLDP neighbors found.</Alert>
                      )}
                    </Card.Body>
                  </Card>
                </Col>
              </Row>
            </Tab>
          </Tabs>
        </Tab>
        
        <Tab eventKey="commands" title="Commands">
          <Row>
            <Col md={6}>
              <Card>
                <Card.Body style={{ maxHeight: "400px", overflowY: "auto" }}>
                  <Card.Title as="h2">Execute Command</Card.Title>
                  <Form onSubmit={handleExecuteCommand}>
                    <Form.Group className="mb-3" controlId="commandInput">
                      <Form.Label>Command</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={3}
                        placeholder="Enter command to execute"
                        value={command}
                        onChange={(e) => setCommand(e.target.value)}
                        required
                        disabled={executingCommand || !!currentTaskId}
                      />
                    </Form.Group>
                    <Form.Group
                      className="mb-3"
                      controlId="isConfigCommandCheckbox"
                    >
                      <Form.Check
                        type="checkbox"
                        label="Configuration Command"
                        checked={isConfigCommand}
                        onChange={(e) => setIsConfigCommand(e.target.checked)}
                        disabled={executingCommand || !!currentTaskId}
                      />
                    </Form.Group>
                    <Button
                      variant="primary"
                      type="submit"
                      disabled={executingCommand || !!currentTaskId}
                    >
                      {(executingCommand || (currentTaskId && taskAction === 'executeCommand')) ? (
                        <Spinner as="span" animation="border" size="sm" />
                      ) : (
                        "Execute"
                      )}
                    </Button>
                  </Form>
                  {commandError && (
                    <Alert variant="danger" className="mt-3">
                      {commandError}
                    </Alert>
                  )}
                  {commandOutput && (
                    <div
                      className="mt-3 p-3 bg-light rounded"
                      style={{
                        whiteSpace: "pre-wrap",
                        fontFamily: "monospace",
                      }}
                    >
                      {deviceLevel && (
                        <>
                          <strong>Device Level:</strong> {deviceLevel}
                          <br />
                        </>
                      )}
                      <strong>Output:</strong>
                      <br />
                      {typeof commandOutput === 'string' ? commandOutput : JSON.stringify(commandOutput, null, 2)}
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
      </Tabs>
      
      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm VLAN Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete VLAN {vlanToDelete}? This action cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)} disabled={isDeleting || !!currentTaskId}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDeleteVlan} disabled={isDeleting || !!currentTaskId}>
            {isDeleting || (currentTaskId && taskAction === 'deleteVlan') ? <Spinner as="span" animation="border" size="sm" /> : 'Proceed'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Toast for user feedback */}
      <Toast 
        show={showToast} 
        onClose={() => setShowToast(false)} 
        delay={3000} 
        autohide
        style={{
          position: 'fixed',
          top: 20,
          right: 20,
          zIndex: 9999,
        }}
      >
        <Toast.Header>
          <strong className="me-auto">
            {toastVariant === 'success' ? 'Success' : 'Error'}
          </strong>
        </Toast.Header>
        <Toast.Body 
          className={toastVariant === 'success' ? 'text-success' : 'text-danger'}
        >
          {toastMessage}
        </Toast.Body>
      </Toast>
    </Container>
  );
};

export default CiscoIosSwitchDetailPage;