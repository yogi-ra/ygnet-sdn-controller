import React, { useState } from "react";
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
} from "react-bootstrap";
import { useAuth } from "../../hooks/useAuth";
import { useQuery, useQueryClient } from "@tanstack/react-query";

// Separate hook for system information with lazy loading
const useSystemInfo = (deviceId: string | undefined, enabled: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<any, Error>({
    queryKey: ["systemInfo", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
      }

      const response = await fetch(`/api/devices/${deviceId}`, {
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
        throw new Error(`Failed to fetch device details: ${response.statusText}`);
      }
      
      const deviceData = await response.json();
      return deviceData.version || {};
    },
    enabled, // Controlled by the enabled parameter
  });
};

// Separate hook for clock information
const useClockInfo = (deviceId: string | undefined, enabled: boolean) => {
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
    enabled, // Controlled by the enabled parameter
  });
};

// Separate hook for interfaces with lazy loading
const useInterfaces = (deviceId: string | undefined, enabled: boolean) => {
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
    enabled, // Controlled by the enabled parameter
  });
};

// Separate hook for routing information with lazy loading
const useRoutingInfo = (deviceId: string | undefined, enabled: boolean) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<any[], Error>({
    queryKey: ["routingInfo", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
      }
      
      // Placeholder for routing information endpoint
      // In a real implementation, this would fetch actual routing data
      return [];
    },
    enabled, // Controlled by the enabled parameter
  });
};

const CiscoIosRouterDetailPage = ({ device }: { device: any }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const queryClient = useQueryClient();
  
  // Tab state
  const [activeTab, setActiveTab] = useState("overview");
  
  // Lazy load data based on active tab
  const { data: systemInfo, isLoading: systemLoading, error: systemError } = useSystemInfo(id, activeTab === "overview");
  const { data: clockInfo, isLoading: clockLoading, error: clockError } = useClockInfo(id, activeTab === "overview");
  const { data: interfaces, isLoading: interfacesLoading, error: interfacesError } = useInterfaces(id, activeTab === "interfaces");
  const { data: routingInfo, isLoading: routingLoading, error: routingError } = useRoutingInfo(id, activeTab === "routing");
  
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
    enabled: !!id,
    initialData: device?.is_reachable, // Use initial data from passed device object
    refetchInterval: 5000, // Poll reachability every 5 seconds
  });
  
  // Command execution state
  const [command, setCommand] = useState("");
  const [isConfigCommand, setIsConfigCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);
  const [deviceLevel, setDeviceLevel] = useState<string | null>(null);
  const [executingCommand, setExecutingCommand] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);

  // Handle tab changes
  const handleTabSelect = (tabKey: string | null) => {
    if (tabKey) {
      setActiveTab(tabKey);
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
    } finally {
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
      queryClient.invalidateQueries({ queryKey: ["routingInfo", id] });
      queryClient.invalidateQueries({ queryKey: ["deviceReachability", id] });
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
                    Device ID: {device?.id} | IP: {device?.ip_address} | Type: Cisco IOS Router
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
                  {systemError || clockError ? (
                    <Alert variant="danger">
                      Error: {systemError?.message || clockError?.message}. Please try again later.
                    </Alert>
                  ) : systemLoading || clockLoading ? (
                    <div className="text-center">
                      <Spinner animation="border" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </Spinner>
                    </div>
                  ) : systemInfo ? (
                    <Table striped bordered hover>
                      <tbody>
                        <tr>
                          <td><strong>Hostname:</strong></td>
                          <td>{systemInfo.hostname || "N/A"}</td>
                        </tr>
                        <tr>
                          <td><strong>Version:</strong></td>
                          <td>{systemInfo.version || "N/A"}</td>
                        </tr>
                        <tr>
                          <td><strong>Uptime:</strong></td>
                          <td>{systemInfo.uptime || "N/A"}</td>
                        </tr>
                        <tr>
                          <td><strong>Clock:</strong></td>
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
                        </tr>
                      </thead>
                      <tbody>
                        {interfaces.map((iface: any, index: number) => (
                          <tr key={index}>
                            <td>{iface.interface || iface.intf || "N/A"}</td>
                            <td>{iface.ip_address || iface.ip || "N/A"}</td>
                            <td>{iface.status || "N/A"}</td>
                            <td>{iface.proto || "N/A"}</td>
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
        
        <Tab eventKey="routing" title="Routing">
          <Row className="mb-4">
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">Routing Information</Card.Title>
                  {routingError ? (
                    <Alert variant="danger">
                      Error: {routingError.message}. Please try again later.
                    </Alert>
                  ) : routingLoading ? (
                    <div className="text-center">
                      <Spinner animation="border" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </Spinner>
                    </div>
                  ) : routingInfo ? (
                    <Alert variant="info">
                      Routing information would be displayed here for Cisco IOS routers.
                    </Alert>
                  ) : (
                    <Alert variant="info">No routing information available.</Alert>
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
    </Container>
  );
};

export default CiscoIosRouterDetailPage;