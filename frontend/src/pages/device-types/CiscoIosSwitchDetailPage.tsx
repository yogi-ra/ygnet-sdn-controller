import React, { useState, useEffect } from "react";
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
} from "react-bootstrap";
import { useAuth } from "../../hooks/useAuth";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAssignPortToVlan } from '../../api/vlans';
import VlanConfiguration from '../../components/VlanConfiguration';

// Separate hook for system information with lazy loading
const useSystemInfo = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean, deviceData: any) => {
  // Return the version information from the passed device data instead of making another request
  return {
    data: deviceData?.version || {},
    isLoading: false,
    error: null
  };
};

// Separate hook for clock information
const useClockInfo = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<string, Error>({
    queryKey: ["clockInfo", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
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
      return data.clock || "N/A";
    },
    enabled: enabled && isDeviceReachable, // Controlled by the enabled parameter and device reachability
  });
};

// Separate hook for interfaces with lazy loading - fetch once for both interfaces and VLANs tabs
// to avoid duplicate API calls to the same endpoint
const useInterfaces = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<any[], Error>({
    queryKey: ["interfacesBrief", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
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
      // Ensure we return an array
      return Array.isArray(data) ? data : [];
    },
    enabled: enabled && isDeviceReachable, // Controlled by the enabled parameter and device reachability
    staleTime: 1000 * 60 * 5, // Keep data fresh for 5 minutes
  });
};

// Separate hook for VLAN information with lazy loading
const useVlanInfo = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<any[], Error>({
    queryKey: ["vlanInfo", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
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
      // Ensure we return an array
      return Array.isArray(data) ? data : [];
    },
    enabled: enabled && isDeviceReachable, // Controlled by the enabled parameter and device reachability
  });
};

// Separate hook for ARP table
const useArpTable = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<any[], Error>({
    queryKey: ["arpTable", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
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
      // Ensure we return an array
      return Array.isArray(data) ? data : [];
    },
    enabled: enabled && isDeviceReachable, // Controlled by the enabled parameter and device reachability
  });
};

// Separate hook for CDP neighbors
const useCdpNeighbors = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<any[], Error>({
    queryKey: ["cdpNeighbors", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
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
      // Ensure we return an array
      return Array.isArray(data) ? data : [];
    },
    enabled: enabled && isDeviceReachable, // Controlled by the enabled parameter and device reachability
  });
};

// Separate hook for LLDP neighbors
const useLldpNeighbors = (deviceId: string | undefined, enabled: boolean, isDeviceReachable: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<any[], Error>({
    queryKey: ["lldpNeighbors", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
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
      // Ensure we return an array
      return Array.isArray(data) ? data : [];
    },
    enabled: enabled && isDeviceReachable, // Controlled by the enabled parameter and device reachability
  });
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
  const assignPortToVlan = useAssignPortToVlan(id);
  
  // Tab state
  const [activeTab, setActiveTab] = useState("overview");
  
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
  
  // Fetch interfaces once for both interfaces and VLANs tabs to avoid duplicate API calls
  const { data: interfaces, isLoading: interfacesLoading, error: interfacesError, refetch: refetchInterfaces } = useInterfaces(id, activeTab === "interfaces" || activeTab === "vlans", isReachable);
  
  // Lazy load data based on active tab
  const { data: systemInfo, isLoading: systemLoading, error: systemError } = useSystemInfo(id, activeTab === "overview", isReachable, device);
  const { data: clockInfo, isLoading: clockLoading, error: clockError } = useClockInfo(id, activeTab === "overview", isReachable);
  const { data: vlanInfo, isLoading: vlanLoading, error: vlanError } = useVlanInfo(id, activeTab === "vlans", isReachable);
  const { data: arpTable, isLoading: arpLoading, error: arpError } = useArpTable(id, activeTab === "discovery", isReachable);
  const { data: cdpNeighbors, isLoading: cdpLoading, error: cdpError } = useCdpNeighbors(id, activeTab === "discovery", isReachable);
  const { data: lldpNeighbors, isLoading: lldpLoading, error: lldpError } = useLldpNeighbors(id, activeTab === "discovery", isReachable);
  
  // Track if we're switching to the overview tab to show loading state properly
  const [isSwitchingToOverview, setIsSwitchingToOverview] = useState(false);
  
  // When switching to overview tab, set switching state
  useEffect(() => {
    if (activeTab === "overview") {
      setIsSwitchingToOverview(true);
      // Reset after a short delay to allow data to load
      const timer = setTimeout(() => {
        setIsSwitchingToOverview(false);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [activeTab]);
  
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

  // Handle tab changes
  const handleTabSelect = (tabKey: string | null) => {
    if (tabKey) {
      setActiveTab(tabKey);
    }
  };

  // Handle interface toggle
  const handleToggleInterface = async (interfaceName: string, currentState: string) => {
    if (!id || !token) return;
    
    // Set loading state for this interface
    setTogglingInterfaces(prev => ({ ...prev, [interfaceName]: true }));
    
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
      
      // Clear device cache to ensure we get fresh data from the device
      await fetch(`/api/devices/${id}/cache/clear`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      
      // Invalidate all relevant queries to force refresh
      queryClient.invalidateQueries({ queryKey: ["interfacesBrief", id] });
      
      // Show success toast
      setToastMessage(`Successfully ${newState ? 'enabled' : 'disabled'} interface ${interfaceName}`);
      setToastVariant('success');
      setShowToast(true);
    } catch (err: any) {
      console.error("Error toggling interface:", err);
      // Show error toast
      setToastMessage(`Error toggling interface: ${err.message || "Unknown error"}`);
      setToastVariant('danger');
      setShowToast(true);
    } finally {
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
      await assignPortToVlan.mutateAsync({ vlanId, port });
    } catch (err: any) {
      console.error("Error assigning port to VLAN:", err);
      alert(`Error assigning port to VLAN: ${err.message || "Unknown error"}`);
    }
  };

  const handleExecuteCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    setExecutingCommand(true);
    setCommandOutput(null);
    setCommandError(null);

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

      setCommandOutput(data.output);
      setDeviceLevel(data.device_level || null);
    } catch (err: any) {
      setCommandError(err.message || "An unknown error occurred.");
    }
    finally {
      setExecutingCommand(false);
      setCommand("");
    }
  };

  const handleClearCache = async () => {
    if (!id) return;

    const endpoint = `/api/devices/${id}/cache/clear`;

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        logout();
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to clear cache");
      }

      // Invalidate all queries for this device to force refresh
      queryClient.invalidateQueries({ queryKey: ["deviceDetail", id] });
      queryClient.invalidateQueries({ queryKey: ["systemInfo", id] });
      queryClient.invalidateQueries({ queryKey: ["clockInfo", id] });
      queryClient.invalidateQueries({ queryKey: ["interfacesBrief", id] });
      queryClient.invalidateQueries({ queryKey: ["vlanInfo", id] });
      queryClient.invalidateQueries({ queryKey: ["deviceReachability", id] });
      queryClient.invalidateQueries({ queryKey: ["arpTable", id] });
      queryClient.invalidateQueries({ queryKey: ["cdpNeighbors", id] });
      queryClient.invalidateQueries({ queryKey: ["lldpNeighbors", id] });
    } catch (err: any) {
      console.error("Error clearing cache:", err);
    }
  };

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
                  <Button variant="outline-primary" onClick={handleClearCache}>
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
                  ) : (systemLoading || clockLoading) || isSwitchingToOverview ? (
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
                                disabled={!device?.is_reachable || togglingInterfaces[iface.interface || iface.intf || ""]}
                              >
                                {togglingInterfaces[iface.interface || iface.intf || ""] ? (
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
          <Row className="mb-4">
            <Col>
              <VlanConfiguration
                deviceId={id}
                vlanInfo={vlanInfo}
                vlanLoading={vlanLoading}
                vlanError={vlanError}
                interfaces={interfaces}
                interfacesLoading={interfacesLoading}
                interfacesError={interfacesError}
                deviceReachable={isReachable}
              />
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="discovery" title="Network Discovery">
          <Row className="mb-4">
            <Col md={12}>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">ARP Table</Card.Title>
                  {arpError ? (
                    <Alert variant="danger">
                      Error: {arpError.message}. Please try again later.
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
                            <td>{entry.address || "N/A"}</td>
                            <td>{entry.mac || entry.hardware || "N/A"}</td>
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
          
          <Row className="mb-4">
            <Col md={6}>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">CDP Neighbors</Card.Title>
                  {cdpError ? (
                    <Alert variant="danger">
                      Error: {cdpError.message}. Please try again later.
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
            
            <Col md={6}>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">LLDP Neighbors</Card.Title>
                  {lldpError ? (
                    <Alert variant="danger">
                      Error: {lldpError.message}. Please try again later.
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
                      />
                    </Form.Group>
                    <Button
                      variant="primary"
                      type="submit"
                      disabled={executingCommand}
                    >
                      {executingCommand ? (
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