import React, { useState, useEffect, useCallback, useMemo} from "react";
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
import { useChangeVlanName, useCreateVlan, useDeleteVlan } from '../../api/vlans';
import { useConfigureInterfaceVlan, useSetInterfaceDescription } from '../../api/interfaces';
import { useTaskPolling } from "../../hooks/useTaskPolling";
import { API_BASE_URL } from '../../api';

// ============= HOOKS (tetap sama) =============
const useSystemInfo = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean, deviceData: any) => {
  return {
    data: deviceData?.version || {},
    isLoading: false,
    error: null
  };
};

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
      if (typeof result === 'string') {
        setClockData(result || "N/A");
        if (cacheKey) {
            localStorage.setItem(cacheKey, result || "N/A");
        }
      } else if (result && typeof result === 'object' && result.clock) {
        setClockData(result.clock || "N/A");
        if (cacheKey) {
            localStorage.setItem(cacheKey, result.clock || "N/A");
        }
      } else {
        setClockData("N/A");
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

  const fetchClockInfo = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null);

      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
            setClockData(cachedData);
            setLoading(false);
            return;
        }
      }
      
      const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/system/clock`, {
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
      
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (data && data.clock) {
        setClockData(data.clock || "N/A");
        if (cacheKey) {
            localStorage.setItem(cacheKey, data.clock || "N/A");
        }
        setLoading(false);
      } else {
        setClockData("N/A");
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch clock information");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

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
      if (Array.isArray(result)) {
        setInterfacesData(result);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setInterfacesData([]);
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

  const fetchInterfaces = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null);

      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          const parsedData = JSON.parse(cachedData);
          setInterfacesData(parsedData);
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/interfaces/brief`, {
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
      
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        setInterfacesData(data);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        setInterfacesData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch interfaces");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  useEffect(() => {
    setTaskId(null);
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

  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchInterfaces();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchInterfaces]);

  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setInterfacesData(null);
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

const useInterfaceDescriptions = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [descriptionsData, setDescriptionsData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = deviceId ? `interface_descriptions_${deviceId}` : null;

  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(taskId, {
    interval: 250,
    onSuccess: (result) => {
      if (Array.isArray(result)) {
        setDescriptionsData(result);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setDescriptionsData([]);
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

  const fetchInterfaceDescriptions = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null);

      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          const parsedData = JSON.parse(cachedData);
          setDescriptionsData(parsedData);
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/interfaces/description`, {
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
        throw new Error(`Failed to fetch interface descriptions: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        setDescriptionsData(data);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        setDescriptionsData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch interface descriptions");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  useEffect(() => {
    setTaskId(null);
    if (cacheKey) {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        setDescriptionsData(JSON.parse(cachedData));
      } else {
        setDescriptionsData(null);
      }
    } else {
      setDescriptionsData(null);
    }
    setLoading(false);
    setError(null);
  }, [deviceId, enabled, cacheKey]);

  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchInterfaceDescriptions();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchInterfaceDescriptions]);

  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setDescriptionsData(null);
    }
  }, [cacheKey]);

  return {
    data: descriptionsData,
    isFetching: loading || taskLoading,
    error: error || taskError,
    refetch: fetchInterfaceDescriptions,
    clearCache
  };
};

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
      if (Array.isArray(result)) {
        setVlanData(result);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setVlanData([]);
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

  const fetchVlanInfo = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null);

      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          const parsedData = JSON.parse(cachedData);
          setVlanData(parsedData);
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/vlans/brief`, {
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
      
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        setVlanData(data);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        setVlanData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch VLANs");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  useEffect(() => {
    setTaskId(null);
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

  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchVlanInfo();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchVlanInfo]);

  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setVlanData(null);
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
      if (Array.isArray(result)) {
        setArpData(result);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(result));
        }
      } else {
        setArpData([]);
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

  const fetchArpTable = useCallback(async () => {
    if (!token || !deviceId || !enabled || !isDeviceReachable) return;

    try {
      setLoading(true);
      setError(null);
      setTaskId(null);

      if (cacheKey) {
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          const parsedData = JSON.parse(cachedData);
          setArpData(parsedData);
          setLoading(false);
          return;
        }
      }
      
      const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/arp`, {
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
      
      if (data && data.task_id) {
        setTaskId(data.task_id);
      } else if (Array.isArray(data)) {
        setArpData(data);
        if (cacheKey) {
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
        setLoading(false);
      } else {
        setArpData([]);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch ARP table");
      setLoading(false);
    }
  }, [token, deviceId, enabled, isDeviceReachable, logout, navigate, cacheKey]);

  useEffect(() => {
    setTaskId(null);
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

  useEffect(() => {
    if (enabled && isDeviceReachable && deviceId) {
      fetchArpTable();
    }
  }, [enabled, isDeviceReachable, deviceId, fetchArpTable]);

  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
      setArpData(null);
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
      
      const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/cdp`, {
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
      
      const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/lldp`, {
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

// ============= HELPER FUNCTIONS =============
const isPhysicalInterface = (interfaceName: string) => {
  if (!interfaceName) return false;
  return /^(FastEthernet|Fa|GigabitEthernet|Gi|Ethernet|Eth)/i.test(interfaceName);
};

const formatInterfaceName = (name: string) => {
  if (name.startsWith('FastEthernet')) return name.replace('FastEthernet', 'Fa');
  if (name.startsWith('GigabitEthernet')) return name.replace('GigabitEthernet', 'Gi');
  if (name.startsWith('Ethernet')) return name.replace('Ethernet', 'Eth');
  return name;
};

const isInterfaceAdminUp = (status: string) => {
  return !status?.toLowerCase().includes("administratively down");
};

// ============= TYPE DEFINITIONS =============
interface VlanInterfaceConfig {
  interface_name: string;
  mode: 'access' | 'trunk';
  access_vlan?: number;
  native_vlan?: number;
  allowed_vlans?: string;
}

// ============= MAIN COMPONENT =============
const CiscoIosSwitchDetailPage = ({ device }: { device: any }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const queryClient = useQueryClient();
  
  // ============= TAB STATE =============
  const [activeTab, setActiveTab] = useState("overview");
  const [activeDiscoveryTab, setActiveDiscoveryTab] = useState('arp');
  const [activeVlanTab, setActiveVlanTab] = useState('vlan-settings');
  
  // ============= DEVICE REACHABILITY =============
  const { data: isReachable = false } = useQuery<boolean, Error>({
    queryKey: ["deviceReachability", id],
    queryFn: async () => {
      if (!token) {
        throw new Error("No authentication token found.");
      }

      const response = await fetch(`${API_BASE_URL}/devices/${id}/check-reachability`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch reachability: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: !!id && device?.is_reachable !== false,
    initialData: device?.is_reachable,
    refetchInterval: 5000,
  });
  
  // ============= TASK STATE =============
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [taskAction, setTaskAction] = useState<string | null>(null);
  
  const { taskStatus, loading: taskLoading, error: taskError } = useTaskPolling(currentTaskId, {
    interval: 1000,
    onSuccess: () => {
      if (taskAction === 'toggleInterface') {
        queryClient.invalidateQueries({ queryKey: ["interfacesBrief", id] });
      } else if (taskAction === 'assignPortToVlan' || taskAction === 'changeVlanName' || 
                 taskAction === 'createVlan' || taskAction === 'deleteVlan' || 
                 taskAction === 'configureInterfaceVlan' || taskAction === 'addVlanMember') {
        queryClient.invalidateQueries({ queryKey: ["vlanInfo", id] });
      }
    }
  });
  
  // ============= DATA FETCHING =============
  const { data: interfaces, isFetching: interfacesLoading, error: interfacesError, refetch: refetchInterfaces, clearCache: clearInterfacesCache } = useInterfaces(id, activeTab === "interfaces" || activeTab === "vlans", isReachable);
  const { data: systemInfo, isLoading: systemLoading, error: systemError } = useSystemInfo(id, activeTab === "overview", isReachable, device);
  const { data: clockInfo, isFetching: clockLoading, error: clockError, refetch: refetchClockInfo, clearCache: clearClockCache } = useClockInfo(id, activeTab === "overview", isReachable);
  const { data: vlanInfo, isFetching: vlanLoading, error: vlanError, refetch: refetchVlanInfo, clearCache: clearVlanInfoCache } = useVlanInfo(id, activeTab === "vlans", isReachable);
  const { data: arpTable, isFetching: arpLoading, error: arpError, refetch: refetchArpTable, clearCache: clearArpTableCache } = useArpTable(id, activeTab === 'discovery' && activeDiscoveryTab === 'arp', isReachable);
  const { data: cdpNeighbors, isFetching: cdpLoading, error: cdpError, refetch: refetchCdpNeighbors, clearCache: clearCdpCache } = useCdpNeighbors(id, activeTab === 'discovery' && activeDiscoveryTab === 'cdp', isReachable);
  const { data: lldpNeighbors, isFetching: lldpLoading, error: lldpError, refetch: refetchLldpNeighbors, clearCache: clearLldpCache } = useLldpNeighbors(id, activeTab === 'discovery' && activeDiscoveryTab === 'lldp', isReachable);
  const { data: interfaceDescriptions, isFetching: interfaceDescriptionsLoading, error: interfaceDescriptionsError, refetch: refetchInterfaceDescriptions, clearCache: clearInterfaceDescriptionsCache } = useInterfaceDescriptions(id, activeTab === "interfaces", isReachable);
  
  // ============= COMMAND EXECUTION STATE =============
  const [command, setCommand] = useState("");
  const [isConfigCommand, setIsConfigCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);
  const [deviceLevel, setDeviceLevel] = useState<string | null>(null);
  const [executingCommand, setExecutingCommand] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);
  
  // ============= INTERFACE STATES =============
  const [togglingInterfaces, setTogglingInterfaces] = useState<{ [key: string]: boolean }>({});
  const [descriptionEdits, setDescriptionEdits] = useState<{ [key: string]: string }>({});
  const [savingDescription, setSavingDescription] = useState<{ [key: string]: boolean }>({});
  
  // ============= TOAST STATE =============
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState<'success' | 'danger'>('success');

  // ============= VLAN MEMBERS STATE =============
  const [vlanMembers, setVlanMembers] = useState<any[]>([]);
  const [newVlanMemberId, setNewVlanMemberId] = useState<string>('');
  const [newVlanMemberName, setNewVlanMemberName] = useState<string>('');
  const [isAddingVlanMember, setIsAddingVlanMember] = useState(false);
  const [selectedVlanMembers, setSelectedVlanMembers] = useState<string[]>([]);
  const [showDeleteVlanMemberModal, setShowDeleteVlanMemberModal] = useState(false);
  const [vlanMemberToDelete, setVlanMemberToDelete] = useState<string | null>(null);
  const [isDeletingVlanMember, setIsDeletingVlanMember] = useState(false);
  const [permitVlanSearch, setPermitVlanSearch] = useState<string>("");
  const [showPermitVlanDropdown, setShowPermitVlanDropdown] = useState<boolean>(false);

  // ============= VLAN SETTINGS STATE - PER PORT CONFIG =============
  const physicalInterfaces = useMemo(() => {
    return interfaces?.filter((iface: any) => {
      const ifaceName = iface.interface || iface.intf || '';
      return isPhysicalInterface(ifaceName);
    }) || [];
  }, [interfaces]);

  const [selectedPorts, setSelectedPorts] = useState<string[]>([]);
  const [portSearchTerm, setPortSearchTerm] = useState<string>('');
  const [showPortDropdown, setShowPortDropdown] = useState<boolean>(false);
  const [portConfig, setPortConfig] = useState<any>({
    vlanType: 'Access',
    accessVlan: '1',
    nativeVlan: '1',
    permitVlans: [],
  });
  const [applyingPortConfig, setApplyingPortConfig] = useState(false);

  // ============= VLAN MANAGEMENT STATE =============
  const [vlanNameEdits, setVlanNameEdits] = useState<{ [key: string]: string }>({});

  // ============= API HOOKS =============
  const changeVlanName = useChangeVlanName(id || '');
  const createVlan = useCreateVlan(id || '');
  const deleteVlan = useDeleteVlan(id || '');
  const configureInterfaceVlan = useConfigureInterfaceVlan(id || '');
  const setInterfaceDescription = useSetInterfaceDescription(id || '');

  // ============= MEMOIZED VALUES =============
  const vlanOptions = useMemo(() => {
    return vlanMembers?.filter((v: any) => (v.vlan_id || v.id) !== 1) || [];
  }, [vlanMembers]);

  const filteredPorts = useMemo(() => {
    return physicalInterfaces
      .map((iface: any) => iface.interface || iface.intf)
      .filter((port: string) => 
        !selectedPorts.includes(port) && 
        port.toLowerCase().includes(portSearchTerm.toLowerCase())
      );
  }, [physicalInterfaces, selectedPorts, portSearchTerm]);

  // ============= EFFECTS =============
  useEffect(() => {
    if (vlanInfo && vlanInfo.length > 0) {
      setVlanMembers(vlanInfo);
    }
  }, [vlanInfo]);

  // Reset when leaving VLAN Settings tab
  useEffect(() => {
    if (activeVlanTab !== 'vlan-settings') {
      setSelectedPorts([]);
      setPortSearchTerm('');
      setShowPortDropdown(false);
      setPortConfig({
        vlanType: 'Access',
        accessVlan: '1',
        nativeVlan: '1',
        permitVlans: [],
      });
      setPermitVlanSearch("");
      setShowPermitVlanDropdown(false);
    }
  }, [activeVlanTab]);

  // ============= HANDLERS =============
  const handleRefresh = useCallback(() => {
    clearInterfacesCache();
    clearInterfaceDescriptionsCache();
    clearVlanInfoCache();
    clearArpTableCache();
    clearCdpCache();
    clearLldpCache();
    clearClockCache();
    refetchInterfaces();
    refetchInterfaceDescriptions();
    refetchVlanInfo();
    refetchArpTable();
    refetchCdpNeighbors();
    refetchLldpNeighbors();
    refetchClockInfo();
  }, [
    clearInterfacesCache, clearInterfaceDescriptionsCache, clearVlanInfoCache,
    clearArpTableCache, clearCdpCache, clearLldpCache, clearClockCache,
    refetchInterfaces, refetchInterfaceDescriptions, refetchVlanInfo,
    refetchArpTable, refetchCdpNeighbors, refetchLldpNeighbors, refetchClockInfo
  ]);

  const handleTabSelect = (tabKey: string | null) => {
    if (tabKey) {
      setActiveTab(tabKey);
    }
  };

  // ============= VLAN MEMBERS HANDLERS =============
  const handleAddVlanMember = async () => {
    if (!id || !newVlanMemberId) return;

    setIsAddingVlanMember(true);
    try {
      const vlanIdNum = parseInt(newVlanMemberId);
      if (isNaN(vlanIdNum) || vlanIdNum < 1 || vlanIdNum > 4094) {
        throw new Error("VLAN ID must be between 1 and 4094");
      }

      setTaskAction('createVlan');
      const response = await createVlan.mutateAsync({ 
        id: vlanIdNum, 
        name: newVlanMemberName || `VLAN${vlanIdNum}` 
      });
      setCurrentTaskId(response.task_id);
      
      setNewVlanMemberId('');
      setNewVlanMemberName('');
    } catch (err: any) {
      setToastMessage(`Error adding VLAN member: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    } finally {
      setIsAddingVlanMember(false);
    }
  };

  const handleSelectVlanMember = (vlanId: string) => {
    setSelectedVlanMembers(prev => {
      if (prev.includes(vlanId)) {
        return prev.filter(id => id !== vlanId);
      } else {
        return [...prev, vlanId];
      }
    });
  };

  const handleSelectAllVlanMembers = () => {
    if (vlanMembers.length === selectedVlanMembers.length) {
      setSelectedVlanMembers([]);
    } else {
      setSelectedVlanMembers(vlanMembers.map(v => v.vlan_id || v.id));
    }
  };

  const handleDeleteVlanMember = async (vlanId: string) => {
    setIsDeletingVlanMember(true);
    try {
      setTaskAction('deleteVlan');
      const response = await deleteVlan.mutateAsync(vlanId);
      setCurrentTaskId(response.task_id);
      setToastMessage(`Successfully deleted VLAN ${vlanId}`);
      setToastVariant('success');
      setShowToast(true);
    } catch (err: any) {
      setToastMessage(`Error deleting VLAN: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    } finally {
      setIsDeletingVlanMember(false);
      setShowDeleteVlanMemberModal(false);
      setVlanMemberToDelete(null);
      setSelectedVlanMembers([]);
    }
  };

  const handleBulkDeleteVlanMembers = async () => {
    if (selectedVlanMembers.length === 0) return;
    
    setIsDeletingVlanMember(true);
    try {
      for (const vlanId of selectedVlanMembers) {
        setTaskAction('deleteVlan');
        await deleteVlan.mutateAsync(vlanId);
      }
      setToastMessage(`Successfully deleted ${selectedVlanMembers.length} VLAN(s)`);
      setToastVariant('success');
      setShowToast(true);
    } catch (err: any) {
      setToastMessage(`Error deleting VLANs: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    } finally {
      setIsDeletingVlanMember(false);
      setSelectedVlanMembers([]);
    }
  };

  const handleAddPermitVlan = useCallback((vlanId: string) => {
    setPortConfig(prev => {
      const currentPermitVlans = prev.permitVlans || [];
      if (!currentPermitVlans.includes(vlanId) && vlanId !== '1') {
        return {
          ...prev,
          permitVlans: [...currentPermitVlans, vlanId]
        };
      }
      return prev;
    });
  }, []);

  const handleRemovePermitVlan = useCallback((vlanId: string) => {
    setPortConfig(prev => ({
      ...prev,
      permitVlans: (prev.permitVlans || []).filter(id => id !== vlanId)
    }));
  }, []);

  const handleAddAllPermitVlans = useCallback(() => {
    const allVlanIds = vlanMembers
      .map(v => v.vlan_id || v.id)
      .filter((id: string) => id !== '1');
    
    setPortConfig(prev => ({
      ...prev,
      permitVlans: allVlanIds
    }));
  }, [vlanMembers]);

  const handleClearPermitVlans = useCallback(() => {
    setPortConfig(prev => ({
      ...prev,
      permitVlans: []
    }));
  }, []);

  // ============= PORT FILTER HANDLERS =============
  const handleAddPortToFilter = useCallback((portName: string) => {
    setSelectedPorts(prev => {
      if (!prev.includes(portName)) {
        return [...prev, portName];
      }
      return prev;
    });
  }, []);

  const handleRemovePortFromFilter = useCallback((portName: string) => {
    setSelectedPorts(prev => prev.filter(p => p !== portName));
  }, []);

  // ============= PORT CONFIG HANDLERS =============
  const handleVlanTypeChange = useCallback((value: string) => {
    setPortConfig(prev => ({
      ...prev,
      vlanType: value,
      accessVlan: value === 'Access' ? prev.accessVlan || '1' : '',
      nativeVlan: value === 'Trunk' ? prev.nativeVlan || '1' : '1',
      permitVlans: value === 'Trunk' ? prev.permitVlans || [] : []
    }));
  }, []);

  const handleAccessVlanChange = useCallback((value: string) => {
    setPortConfig(prev => ({
      ...prev,
      accessVlan: value
    }));
  }, []);

  const handleNativeVlanChange = useCallback((value: string) => {
    setPortConfig(prev => ({
      ...prev,
      nativeVlan: value
    }));
  }, []);

  const handlePermitVlanChange = useCallback((value: string) => {
    setPortConfig(prev => ({
      ...prev,
      permitVlan: value
    }));
  }, []);

  const handleApplyPortConfig = async () => {
    if (!id || selectedPorts.length === 0) return;

    setApplyingPortConfig(true);
    
    try {
      const configsArray: VlanInterfaceConfig[] = selectedPorts
        .map(portName => {
          const config = portConfig;
          if (!config) return null;
          
          const vlanConfig: VlanInterfaceConfig = {
            interface_name: portName,
            mode: config.vlanType.toLowerCase() as 'access' | 'trunk',
          };
          
          if (config.vlanType === 'Access') {
            if (config.accessVlan && config.accessVlan !== '') {
              vlanConfig.access_vlan = parseInt(config.accessVlan);
            }
          } else if (config.vlanType === 'Trunk') {
            if (config.nativeVlan && config.nativeVlan !== '') {
              vlanConfig.native_vlan = parseInt(config.nativeVlan);
            }
            
            if (config.permitVlans && config.permitVlans.length > 0) {
              if (config.permitVlans.includes('all')) {
                vlanConfig.allowed_vlans = '1-4094';
              } else {
                vlanConfig.allowed_vlans = config.permitVlans.join(',');
              }
              console.log(`✅ Adding allowed_vlans for ${portName}:`, config.permitVlans);
            }
          }
          
          return vlanConfig;
        })
        .filter((config): config is VlanInterfaceConfig => config !== null);
      
      const response = await configureInterfaceVlan.mutateAsync({ 
        configs: configsArray 
      });
      
      if (response.task_ids && response.task_ids.length > 0) {
        const lastTask = response.task_ids[response.task_ids.length - 1];
        setCurrentTaskId(lastTask.task_id);
      } else if (response.task_id) {
        setCurrentTaskId(response.task_id);
      }
      
      setTaskAction('configureInterfaceVlan');
    } catch (err: any) {
      console.error('❌ Error applying config:', err);
    } finally {
      setApplyingPortConfig(false);
    }
  };

  // ============= VLAN NAME MANAGEMENT HANDLERS =============
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
      const response = await changeVlanName.mutateAsync({ vlanId, newName });
      setCurrentTaskId(response.task_id);
      setTaskAction('changeVlanName');
    } catch (err: any) {
      setToastMessage(`Error changing VLAN name: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    }
  };

  // ============= INTERFACE HANDLERS =============
  const handleToggleInterface = async (interfaceName: string, currentState: string) => {
    if (!id || !token) return;
    
    setTogglingInterfaces(prev => ({ ...prev, [interfaceName]: true }));
    setTaskAction('toggleInterface');
    
    const newState = !isInterfaceAdminUp(currentState);
    
    try {
      const response = await fetch(`${API_BASE_URL}/devices/${id}/interfaces/state`, {
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
      setToastMessage(`Error toggling interface: ${err.message || "Unknown error"}`);
      setToastVariant('danger');
      setShowToast(true);
      setTogglingInterfaces(prev => {
        const newState = { ...prev };
        delete newState[interfaceName];
        return newState;
      });
    }
  };

  const handleDescriptionChange = (ifaceName: string, value: string) => {
    setDescriptionEdits(prev => ({
      ...prev,
      [ifaceName]: value
    }));
  };

  const handleCancelDescriptionEdit = (ifaceName: string) => {
    setDescriptionEdits(prev => {
      const newState = { ...prev };
      delete newState[ifaceName];
      return newState;
    });
  };

  const handleSaveDescription = async (ifaceName: string) => {
    const description = descriptionEdits[ifaceName];
    if (!id || description === undefined) return;

    try {
      const response = await setInterfaceDescription.mutateAsync({ interfaceName: ifaceName, description });
      setCurrentTaskId(response.task_id);
      setTaskAction('setInterfaceDescription');
    } catch (err: any) {
      setToastMessage(`Error setting interface description: ${err.message || 'Unknown error'}`);
      setToastVariant('danger');
      setShowToast(true);
    }
  };

  // ============= COMMAND EXECUTION HANDLER =============
  const handleExecuteCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    setExecutingCommand(true);
    setCommandOutput(null);
    setCommandError(null);
    setTaskAction('executeCommand');

    const endpoint = `${API_BASE_URL}/devices/${id}/execute-command`;
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

  // ============= TASK COMPLETION EFFECT =============
  useEffect(() => {
    if (taskStatus?.status === 'SUCCESS') {
      if (taskAction === 'toggleInterface') {
        setToastMessage('Interface toggled successfully');
        setToastVariant('success');
        setShowToast(true);
        setTogglingInterfaces({});
        clearInterfacesCache();
        refetchInterfaces();
      } else if (taskAction === 'setInterfaceDescription') {
        setToastMessage('Successfully changed device description');
        setToastVariant('success');
        setShowToast(true);
        clearInterfaceDescriptionsCache();
        refetchInterfaceDescriptions();
      } else if (taskAction === 'changeVlanName') {
        setToastMessage(`Successfully changed VLAN name`);
        setToastVariant('success');
        setShowToast(true);
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'createVlan') {
        setToastMessage('Successfully added VLAN member');
        setToastVariant('success');
        setShowToast(true);
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'deleteVlan') {
        setToastMessage('Successfully deleted VLAN');
        setToastVariant('success');
        setShowToast(true);
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'configureInterfaceVlan') {
        setToastMessage('Successfully configured VLAN settings for port(s)');
        setToastVariant('success');
        setShowToast(true);
        clearInterfacesCache();
        refetchInterfaces();
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'executeCommand') {
        const output = taskStatus.result || taskStatus.info || "No output";
        setCommandOutput(output);
        setDeviceLevel(null);
        setExecutingCommand(false);
        setCommand("");
      }
      
      setCurrentTaskId(null);
      setTaskAction(null);
    } else if (taskStatus?.status === 'FAILURE') {
      const errorMessage = taskStatus.error || 'Task failed';
      
      if (taskAction === 'toggleInterface') {
        setToastMessage(`Error toggling interface: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        setTogglingInterfaces({});
        clearInterfacesCache();
        refetchInterfaces();
      } else if (taskAction === 'setInterfaceDescription') {
        setToastMessage(`Error changing device description: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        clearInterfaceDescriptionsCache();
        refetchInterfaceDescriptions();
      } else if (taskAction === 'changeVlanName') {
        setToastMessage(`Error changing VLAN name: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'createVlan') {
        setToastMessage(`Error adding VLAN member: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'deleteVlan') {
        setToastMessage(`Error deleting VLAN: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'configureInterfaceVlan') {
        setToastMessage(`Error configuring port VLAN: ${errorMessage}`);
        setToastVariant('danger');
        setShowToast(true);
        clearInterfacesCache();
        refetchInterfaces();
        clearVlanInfoCache();
        refetchVlanInfo();
      } else if (taskAction === 'executeCommand') {
        setCommandError(errorMessage);
        setExecutingCommand(false);
        setCommand("");
      }
      
      setCurrentTaskId(null);
      setTaskAction(null);
    }
  }, [taskStatus, taskAction, clearInterfacesCache, clearInterfaceDescriptionsCache, clearVlanInfoCache, refetchInterfaces, refetchInterfaceDescriptions, refetchVlanInfo]);

  // ============= EARLY RETURN =============
  if (!id) {
    return <Alert variant="danger">Device ID is required</Alert>;
  }

  return (
    <Container fluid className="mt-4">
      {/* Header Card */}
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

      {/* Task Error Alert */}
      {taskError && (
        <Row className="mb-3">
          <Col>
            <Alert variant="danger">
              Error processing task: {taskError}
            </Alert>
          </Col>
        </Row>
      )}

      {/* Main Tabs */}
      <Tabs
        activeKey={activeTab}
        onSelect={handleTabSelect}
        className="mb-3"
        mountOnEnter={true}
        unmountOnExit={true}
      >
        {/* Overview Tab */}
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
                      <Spinner animation="border" role="status" />
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
        
        {/* Interfaces Tab */}
        <Tab eventKey="interfaces" title="Interfaces">
          <Row className="mb-4">
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">Interfaces</Card.Title>
                  {(interfacesError || interfaceDescriptionsError) ? (
                     <Alert variant="danger">
                      Error: {interfacesError || interfaceDescriptionsError}. Please try again later.
                     </Alert>
                  ) : (interfacesLoading || interfaceDescriptionsLoading) ? (
                     <div className="text-center">
                       <Spinner animation="border" role="status" />
                     </div>
                  ) : interfaces && interfaces.length > 0 ? (
                    <Table striped bordered hover responsive>
                      <thead>
                        <tr>
                          <th>Interface</th>
                          <th>Description</th>
                          <th>IP Address</th>
                          <th>Status</th>
                          <th>Protocol</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {interfaces.map((iface: any, index: number) => {
                          const ifaceName = iface.interface || iface.intf || "";
                          const isEditing = descriptionEdits.hasOwnProperty(ifaceName);
                          const editedDescription = descriptionEdits[ifaceName] ?? '';

                          const descriptionEntry = interfaceDescriptions?.find((desc: any) => {
                            if (desc.port === ifaceName) return true;
                            const shortInterfaceName = ifaceName.replace(/^GigabitEthernet/, 'Gi')
                                                              .replace(/^FastEthernet/, 'Fa')
                                                              .replace(/^Ethernet/, 'Eth')
                                                              .replace(/^Serial/, 'Se')
                                                              .replace(/^Loopback/, 'Lo')
                                                              .replace(/^Vlan/, 'Vl');
                            return desc.port === shortInterfaceName;
                          });

                          const currentDescription = descriptionEntry ? descriptionEntry.description : "N/A";

                          return (
                          <tr key={index}>
                            <td>{ifaceName}</td>
                            <td>
                              {isEditing ? (
                                <InputGroup>
                                  <Form.Control
                                    type="text"
                                    size="sm"
                                    value={editedDescription}
                                    onChange={(e) => handleDescriptionChange(ifaceName, e.target.value)}
                                    disabled={!device?.is_reachable || !!currentTaskId}
                                  />
                                  <Button 
                                    size="sm" 
                                    variant="success" 
                                    onClick={() => handleSaveDescription(ifaceName)} 
                                    disabled={!device?.is_reachable || !!currentTaskId || savingDescription[ifaceName]}
                                  >
                                    {(savingDescription[ifaceName] ||
                                      (currentTaskId && taskAction === "setInterfaceDescription")) ? 
                                      <Spinner as="span" animation="border" size="sm" /> : "Save"
                                    } 
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="outline-secondary" 
                                    onClick={() => handleCancelDescriptionEdit(ifaceName)} 
                                    disabled={!!currentTaskId}
                                  >
                                    ×
                                  </Button>
                                </InputGroup>
                              ) : (
                                <div>
                                  {currentDescription}
                                  <Button size="sm" variant="outline-primary" className="ms-2" onClick={() => handleDescriptionChange(ifaceName, currentDescription)} disabled={!device?.is_reachable || !!currentTaskId}>Edit</Button>
                                </div>
                              )}
                            </td>
                            <td>{iface.ip_address || iface.ip || "N/A"}</td>
                            <td>{iface.status || "N/A"}</td>
                            <td>{iface.proto || "N/A"}</td>
                            <td>
                              <Button
                                size="sm"
                                variant={isInterfaceAdminUp(iface.status) ? "danger" : "success"}
                                onClick={() => handleToggleInterface(ifaceName, iface.status || "")}
                                disabled={!device?.is_reachable || togglingInterfaces[ifaceName] || !!currentTaskId}
                              >
                                {(togglingInterfaces[ifaceName] || 
                                  (currentTaskId && taskAction === 'toggleInterface')) ? (
                                  <>
                                    <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                                  </>
                                ) : isInterfaceAdminUp(iface.status) ? "Shut Down" : "Enable"}
                              </Button>
                            </td>
                          </tr>
                        )})}
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
        
        {/* VLANs Tab */}
        <Tab eventKey="vlans" title="VLANs">
          <Tabs
            activeKey={activeVlanTab}
            onSelect={(k) => setActiveVlanTab(k || 'vlan-settings')}
            className="mb-3"
            mountOnEnter
            unmountOnExit
          >
            {/* ============= VLAN SETTINGS - PER PORT CONFIGURATION ============= */}
            <Tab eventKey="vlan-settings" title="VLAN Settings">
              <Card>
                <Card.Body>
                  <div className="mb-3">
                    <Alert variant="info">
                      You can go to VLAN Members to add a VLAN ID.
                    </Alert>
                  </div>
                  
                  {/* Port Selection - Search and Badges */}
                  <Row className="mb-4">
                    <Col md={12}>
                      <Form.Group>
                        <Form.Label>Port</Form.Label>
                        <div className="d-flex flex-wrap align-items-center gap-2 mb-2">
                          {/* Selected Ports Badges */}
                          {selectedPorts.map((port) => {
                            const config = portConfig || { vlanType: 'Access' };
                            return (
                              <Badge 
                                key={port} 
                                bg={config.vlanType === 'Trunk' ? 'warning' : 'primary'}
                                className="d-flex align-items-center p-2"
                                style={{ fontSize: '0.9rem' }}
                              >
                                {formatInterfaceName(port)}
                                <Button
                                  variant="link"
                                  size="sm"
                                  className="p-0 ms-2 text-white"
                                  onClick={() => handleRemovePortFromFilter(port)}
                                  style={{ textDecoration: 'none' }}
                                  disabled={!isReachable || !!currentTaskId}
                                >
                                  ×
                                </Button>
                              </Badge>
                            );
                          })}
                          
                          {/* Port Search Input */}
                          <div className="position-relative" style={{ minWidth: '200px' }}>
                            <Form.Control
                              type="text"
                              size="sm"
                              placeholder="Search port..."
                              value={portSearchTerm}
                              onChange={(e) => {
                                setPortSearchTerm(e.target.value);
                                setShowPortDropdown(true);
                              }}
                              onFocus={() => setShowPortDropdown(true)}
                              onBlur={() => setTimeout(() => setShowPortDropdown(false), 200)}
                              disabled={!isReachable || !!currentTaskId}
                            />
                            
                            {/* Port Dropdown */}
                            {showPortDropdown && filteredPorts.length > 0 && (
                              <div 
                                className="position-absolute bg-white border rounded shadow-sm"
                                style={{ 
                                  zIndex: 1000, 
                                  maxHeight: '200px', 
                                  overflowY: 'auto',
                                  width: '100%'
                                }}
                              >
                                {filteredPorts.map((port) => (
                                  <div
                                    key={port}
                                    className="p-2 cursor-pointer hover-bg-light"
                                    onMouseDown={() => handleAddPortToFilter(port)}
                                    style={{ cursor: 'pointer' }}
                                  >
                                    {formatInterfaceName(port)}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <Form.Text className="text-muted">
                          {selectedPorts.length === 0 
                            ? "Select one or more ports to configure" 
                            : `${selectedPorts.length} port(s) selected`
                          }
                        </Form.Text>
                      </Form.Group>
                    </Col>
                  </Row>

                  {/* Configuration Table - BULK CONFIG */}
                  {selectedPorts.length > 0 && (
                    <Table striped bordered hover responsive size="sm">
                      <thead>
                        <tr>
                          <th>VLAN Type</th>
                          <th>Access VLAN</th>
                          <th>Native VLAN</th>
                          <th>Permit VLAN</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          {/* VLAN Type Dropdown */}
                          <td>
                            <Form.Select 
                              size="sm"
                              value={portConfig.vlanType}
                              onChange={(e) => handleVlanTypeChange(e.target.value)}
                              disabled={!isReachable || !!currentTaskId}
                            >
                              <option value="Access">Access</option>
                              <option value="Trunk">Trunk</option>
                            </Form.Select>
                          </td>
                          
                          {/* Access VLAN Dropdown */}
                          <td>
                            {portConfig.vlanType === 'Access' ? (
                              <Form.Select 
                                size="sm"
                                value={portConfig.accessVlan || '1'}
                                onChange={(e) => handleAccessVlanChange(e.target.value)}
                                disabled={!isReachable || !!currentTaskId}
                              >
                                <option value="1">VLAN 1</option>
                                {vlanOptions.map((vlan: any) => (
                                  <option key={vlan.vlan_id || vlan.id} value={vlan.vlan_id || vlan.id}>
                                    VLAN {vlan.vlan_id || vlan.id} {vlan.vlan_name ? `(${vlan.vlan_name})` : ''}
                                  </option>
                                ))}
                              </Form.Select>
                            ) : (
                              <Form.Control
                                size="sm"
                                type="text"
                                value="--"
                                disabled
                                readOnly
                                style={{ backgroundColor: '#e9ecef' }}
                              />
                            )}
                          </td>
                          
                          {/* Native VLAN Dropdown */}
                          <td>
                            {portConfig.vlanType === 'Trunk' ? (
                              <Form.Select 
                                size="sm"
                                value={portConfig.nativeVlan || '1'}
                                onChange={(e) => handleNativeVlanChange(e.target.value)}
                                disabled={!isReachable || !!currentTaskId}
                              >
                                <option value="1">VLAN 1</option>
                                {vlanMembers?.map((vlan: any) => (
                                  <option key={vlan.vlan_id || vlan.id} value={vlan.vlan_id || vlan.id}>
                                    VLAN {vlan.vlan_id || vlan.id} {vlan.vlan_name ? `(${vlan.vlan_name})` : ''}
                                  </option>
                                ))}
                              </Form.Select>
                            ) : (
                              <Form.Control
                                size="sm"
                                type="text"
                                value="--"
                                disabled
                                readOnly
                                style={{ backgroundColor: '#e9ecef' }}
                              />
                            )}
                          </td>
                          {/* Permit VLANs Multi-Select */}
                          <td>
                            {portConfig.vlanType === 'Trunk' ? (
                              <div>
                                {/* Selected Permit VLANs Badges */}
                                <div className="d-flex flex-wrap align-items-center gap-1 mb-2">
                                  {(portConfig.permitVlans || []).map((vlanId: string) => (
                                    <Badge 
                                      key={vlanId} 
                                      bg="success" 
                                      className="d-flex align-items-center p-1"
                                      style={{ fontSize: '0.8rem' }}
                                    >
                                      VLAN {vlanId}
                                      <Button
                                        variant="link"
                                        size="sm"
                                        className="p-0 ms-1 text-white"
                                        onClick={() => handleRemovePermitVlan(vlanId)}
                                        style={{ textDecoration: 'none', fontSize: '1rem' }}
                                        disabled={!isReachable || !!currentTaskId}
                                      >
                                        ×
                                      </Button>
                                    </Badge>
                                  ))}
                                  
                                  {/* Add All Button */}
                                  {vlanMembers.length > 1 && (
                                    <Button
                                      size="sm"
                                      variant="outline-primary"
                                      className="me-1"
                                      onClick={() => handleAddAllPermitVlans()}
                                      disabled={!isReachable || !!currentTaskId}
                                      style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem' }}
                                    >
                                      All
                                    </Button>
                                  )}
                                  
                                  {/* Clear All Button */}
                                  {(portConfig.permitVlans || []).length > 0 && (
                                    <Button
                                      size="sm"
                                      variant="outline-danger"
                                      onClick={() => handleClearPermitVlans()}
                                      disabled={!isReachable || !!currentTaskId}
                                      style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem' }}
                                    >
                                      Clear
                                    </Button>
                                  )}
                                </div>
                                
                                {/* Search Input untuk Add VLAN */}
                                <div className="position-relative">
                                  <Form.Control
                                    type="text"
                                    size="sm"
                                    placeholder="Add VLAN ID..."
                                    value={permitVlanSearch}
                                    onChange={(e) => {
                                      setPermitVlanSearch(e.target.value);
                                      setShowPermitVlanDropdown(true);
                                    }}
                                    onFocus={() => setShowPermitVlanDropdown(true)}
                                    onBlur={() => setTimeout(() => setShowPermitVlanDropdown(false), 200)}
                                    disabled={!isReachable || !!currentTaskId}
                                  />
                                  
                                  {/* Dropdown untuk VLAN yang tersedia */}
                                  {showPermitVlanDropdown && (
                                    <div 
                                      className="position-absolute bg-white border rounded shadow-sm"
                                      style={{ 
                                        zIndex: 1000, 
                                        maxHeight: '150px', 
                                        overflowY: 'auto',
                                        width: '100%'
                                      }}
                                    >
                                      {vlanMembers
                                        .filter(v => (v.vlan_id || v.id) !== '1')
                                        .map(v => v.vlan_id || v.id)
                                        .filter((vlanId: string) => 
                                          !(portConfig.permitVlans || []).includes(vlanId) &&
                                          vlanId.includes(permitVlanSearch || '')
                                        )
                                        .map((vlanId: string) => (
                                          <div
                                            key={vlanId}
                                            className="p-2 cursor-pointer hover-bg-light"
                                            onMouseDown={() => handleAddPermitVlan(vlanId)}
                                            style={{ cursor: 'pointer' }}
                                          >
                                            VLAN {vlanId}
                                          </div>
                                        ))
                                      }
                                      {vlanMembers.filter(v => (v.vlan_id || v.id) !== '1').length === 0 && (
                                        <div className="p-2 text-muted">
                                          No VLANs available
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ) : (
                              <Form.Control
                                size="sm"
                                type="text"
                                value="--"
                                disabled
                                readOnly
                                style={{ backgroundColor: '#e9ecef' }}
                              />
                            )}
                          </td>
                        </tr>
                      </tbody>
                    </Table>
                  )}

                  {/* Save Button */}
                  <Row className="mt-3">
                    <Col md={12} className="text-end">
                      <Button 
                        variant="primary" 
                        onClick={handleApplyPortConfig}
                        disabled={selectedPorts.length === 0 || !isReachable || applyingPortConfig || !!currentTaskId}
                      >
                        {applyingPortConfig ? (
                          <>
                            <Spinner as="span" animation="border" size="sm" className="me-2" />
                            Applying...
                          </>
                        ) : (
                          'Save Configuration'
                        )}
                      </Button>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            </Tab>

            {/* ============= VLAN MEMBERS ============= */}
            <Tab eventKey="vlan-members" title="VLAN Members">
              <Card>
                <Card.Body>
                  <div className="mb-3">
                    <Alert variant="info">
                      VLAN Settings on. Up to <strong>16 VLAN members can be configured.</strong>
                    </Alert>
                  </div>

                  {/* Add VLAN Member Form */}
                  <Row className="mb-4">
                    <Col md={3}>
                      <Form.Group>
                        <Form.Label>VLAN ID</Form.Label>
                        <Form.Control
                          type="number"
                          size="sm"
                          placeholder="1-4094"
                          min="1"
                          max="4094"
                          value={newVlanMemberId}
                          onChange={(e) => setNewVlanMemberId(e.target.value)}
                          disabled={!isReachable || isAddingVlanMember || !!currentTaskId}
                        />
                        <Form.Text className="text-muted">
                          (1-4094)
                        </Form.Text>
                      </Form.Group>
                    </Col>
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label>VLAN Name (Optional)</Form.Label>
                        <Form.Control
                          type="text"
                          size="sm"
                          placeholder="Enter VLAN Name"
                          value={newVlanMemberName}
                          onChange={(e) => setNewVlanMemberName(e.target.value)}
                          disabled={!isReachable || isAddingVlanMember || !!currentTaskId}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={2} className="d-flex align-items-end">
                      <Button 
                        variant="primary" 
                        size="sm"
                        onClick={handleAddVlanMember}
                        disabled={!newVlanMemberId || !isReachable || isAddingVlanMember || !!currentTaskId}
                      >
                        {isAddingVlanMember ? <Spinner as="span" animation="border" size="sm" /> : 'Add'}
                      </Button>
                    </Col>
                  </Row>

                  {/* VLAN Members Table */}
                  {vlanError ? (
                    <Alert variant="danger">Error: {vlanError}</Alert>
                  ) : vlanLoading ? (
                    <div className="text-center"><Spinner animation="border" /></div>
                  ) : vlanMembers && vlanMembers.length > 0 ? (
                    <>
                      <div className="mb-2">
                        <Form.Check
                          type="checkbox"
                          label="Select All"
                          checked={vlanMembers.length === selectedVlanMembers.length}
                          onChange={handleSelectAllVlanMembers}
                          disabled={!isReachable}
                        />
                      </div>
                      <Table striped bordered hover responsive size="sm">
                        <thead>
                          <tr>
                            <th style={{ width: '5%' }}>No.</th>
                            <th style={{ width: '5%' }}>Select</th>
                            <th style={{ width: '20%' }}>VLAN ID</th>
                            <th style={{ width: '40%' }}>VLAN Name</th>
                            <th style={{ width: '30%' }}>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {vlanMembers.map((vlan, index) => {
                            const vlanId = vlan.vlan_id || vlan.id;
                            const vlanName = vlan.vlan_name || `VLAN${vlanId}`;
                            const isEditing = vlanNameEdits.hasOwnProperty(vlanId);
                            const editedName = vlanNameEdits[vlanId] ?? vlanName;

                            return (
                              <tr key={vlanId}>
                                <td>{index + 1}</td>
                                <td className="text-center">
                                  <Form.Check
                                    type="checkbox"
                                    checked={selectedVlanMembers.includes(vlanId)}
                                    onChange={() => handleSelectVlanMember(vlanId)}
                                    disabled={vlanId === 1 || !isReachable}
                                  />
                                </td>
                                <td>
                                  <strong>VLAN {vlanId}</strong>
                                  {vlanId === 1 && (
                                    <Badge bg="secondary" className="ms-2">Default</Badge>
                                  )}
                                </td>
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
                                        disabled={!isReachable || !!currentTaskId}
                                      >
                                        {currentTaskId && taskAction === 'changeVlanName' ? 
                                          <Spinner as="span" animation="border" size="sm" /> : 
                                          "Save"
                                        }
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
                                      {vlanName}
                                      <Button 
                                        size="sm" 
                                        variant="outline-primary" 
                                        className="ms-2" 
                                        onClick={() => handleVlanNameChange(vlanId, vlanName)} 
                                        disabled={!isReachable || !!currentTaskId}
                                      >
                                        Edit
                                      </Button>
                                    </div>
                                  )}
                                </td>
                                <td>
                                  <Button 
                                    size="sm" 
                                    variant="danger"
                                    onClick={() => {
                                      setVlanMemberToDelete(vlanId);
                                      setShowDeleteVlanMemberModal(true);
                                    }}
                                    disabled={vlanId === 1 || !isReachable || isDeletingVlanMember || !!currentTaskId}
                                  >
                                    Delete
                                  </Button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </Table>

                      {/* Bulk Delete Button */}
                      {selectedVlanMembers.length > 0 && (
                        <div className="mt-3">
                          <Button 
                            variant="danger" 
                            size="sm"
                            onClick={handleBulkDeleteVlanMembers}
                            disabled={!isReachable || isDeletingVlanMember || !!currentTaskId}
                          >
                            {isDeletingVlanMember ? (
                              <Spinner as="span" animation="border" size="sm" />
                            ) : (
                              `Delete (${selectedVlanMembers.length})`
                            )}
                          </Button>
                        </div>
                      )}
                    </>
                  ) : (
                    <Alert variant="info">No VLAN members configured. Add a VLAN ID above.</Alert>
                  )}
                </Card.Body>
              </Card>
            </Tab>
          </Tabs>
        </Tab>
        
        {/* Network Discovery Tab */}
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
                          <Spinner animation="border" role="status" />
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
                          <Spinner animation="border" role="status" />
                        </div>
                      ) : cdpNeighbors && cdpNeighbors.length > 0 ? (
                        <Table striped bordered hover responsive>
                          <thead>
                            <tr>
                              <th>Local Interface</th>
                              <th>Capabilities</th>
                              <th>Neighbor Name</th>
                              <th>Neighbor Platform</th>
                              <th>Neighbor Interface</th>
                            </tr>
                          </thead>
                          <tbody>
                            {cdpNeighbors.map((neighbor: any, index: number) => (
                              <tr key={index}>
                                <td>{neighbor.local_interface || "N/A"}</td>
                                <td>{neighbor.capabilities || "N/A"}</td>
                                <td>{neighbor.neighbor_name || "N/A"}</td>
                                <td>{neighbor.platform || "N/A"}</td>
                                <td>{neighbor.neighbor_interface || "N/A"}</td>
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
                          <Spinner animation="border" role="status" />
                        </div>
                      ) : lldpNeighbors && lldpNeighbors.length > 0 ? (
                        <Table striped bordered hover responsive>
                          <thead>
                            <tr>
                              <th>Local Interface</th>
                              <th>Capabilities</th>
                              <th>Neighbor Name</th>
                              <th>Neighbor Interface</th>
                            </tr>
                          </thead>
                          <tbody>
                            {lldpNeighbors.map((neighbor: any, index: number) => (
                              <tr key={index}>
                                <td>{neighbor.local_interface || "N/A"}</td>
                                <td>{neighbor.capabilities || "N/A"}</td>
                                <td>{neighbor.neighbor_name || "N/A"}</td>
                                <td>{neighbor.neighbor_interface || "N/A"}</td>
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
        
        {/* Commands Tab */}
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
      
      {/* Delete VLAN Member Confirmation Modal */}
      <Modal show={showDeleteVlanMemberModal} onHide={() => setShowDeleteVlanMemberModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm VLAN Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete VLAN {vlanMemberToDelete}? This action cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteVlanMemberModal(false)} disabled={isDeletingVlanMember || !!currentTaskId}>
            Cancel
          </Button>
          <Button variant="danger" onClick={() => vlanMemberToDelete && handleDeleteVlanMember(vlanMemberToDelete)} disabled={isDeletingVlanMember || !!currentTaskId}>
            {isDeletingVlanMember ? <Spinner as="span" animation="border" size="sm" /> : 'Delete'}
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