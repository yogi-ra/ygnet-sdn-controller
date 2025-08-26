import { useState, useEffect } from "react";
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
  ListGroup,
  Table,
  Badge,
  Tabs,
  Tab,
} from "react-bootstrap";
import { useAuth } from "../hooks/useAuth";
import { useDeviceDetails } from "../hooks/useDeviceDetails";

const DeviceDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  // Destructure fetchFeature from the hook
  const { device, loading, errors, fetchFeature } = useDeviceDetails(id);

  const [command, setCommand] = useState("");
  const [isConfigCommand, setIsConfigCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);
  const [deviceLevel, setDeviceLevel] = useState<string | null>(null);
  const [executingCommand, setExecutingCommand] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);

  const [clearingCache, setClearingCache] = useState(false);
  const [cacheClearSuccess, setCacheClearSuccess] = useState<string | null>(null);
  const [cacheClearError, setCacheClearError] = useState<string | null>(null);

  const [key, setKey] = useState("general");

  // --- New State Variables for Lazy Loaded Data ---
  const [interfacesData, setInterfacesData] = useState<any[] | null>(null);
  const [loadingInterfaces, setLoadingInterfaces] = useState(false);
  const [interfacesError, setInterfacesError] = useState<string | null>(null);

  const [interfacesTrunkData, setInterfacesTrunkData] = useState<any[] | null>(null);
  const [loadingInterfacesTrunk, setLoadingInterfacesTrunk] = useState(false);
  const [interfacesTrunkError, setInterfacesTrunkError] = useState<string | null>(null);

  const [activeUsersData, setActiveUsersData] = useState<any[] | null>(null);
  const [loadingActiveUsers, setLoadingActiveUsers] = useState(false);
  const [activeUsersError, setActiveUsersError] = useState<string | null>(null);

  const [localUsersData, setLocalUsersData] = useState<any[] | null>(null);
  const [loadingLocalUsers, setLoadingLocalUsers] = useState(false);
  const [localUsersError, setLocalUsersError] = useState<string | null>(null);

  const [vlanBriefData, setVlanBriefData] = useState<any[] | null>(null);
  const [loadingVlanBrief, setLoadingVlanBrief] = useState(false);
  const [vlanBriefError, setVlanBriefError] = useState<string | null>(null);

  const [routingTableData, setRoutingTableData] = useState<any[] | null>(null);
  const [loadingRoutingTable, setLoadingRoutingTable] = useState(false);
  const [routingTableError, setRoutingTableError] = useState<string | null>(null);

  const [aclsData, setAclsData] = useState<any[] | null>(null);
  const [loadingAcls, setLoadingAcls] = useState(false);
  const [aclsError, setAclsError] = useState<string | null>(null);

  const [aaaConfigData, setAaaConfigData] = useState<any[] | null>(null);
  const [loadingAaaConfig, setLoadingAaaConfig] = useState(false);
  const [aaaConfigError, setAaaConfigError] = useState<string | null>(null);

  const [loggingConfigData, setLoggingConfigData] = useState<any[] | null>(null);
  const [loadingLoggingConfig, setLoadingLoggingConfig] = useState(false);
  const [loggingConfigError, setLoggingConfigError] = useState<string | null>(null);

  const [snmpConfigData, setSnmpConfigData] = useState<any[] | null>(null);
  const [loadingSnmpConfig, setLoadingSnmpConfig] = useState(false);
  const [snmpConfigError, setSnmpConfigError] = useState<string | null>(null);

  const [ntpConfigData, setNtpConfigData] = useState<any[] | null>(null);
  const [loadingNtpConfig, setLoadingNtpConfig] = useState(false);
  const [ntpConfigError, setNtpConfigError] = useState<string | null>(null);

  const [clockData, setClockData] = useState<string | null>(null);
  const [loadingClock, setLoadingClock] = useState(false);
  const [clockError, setClockError] = useState<string | null>(null);

  // --- useEffects for Lazy Loading ---

  // Interfaces Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "interfaces" && id && !interfacesData && !loadingInterfaces) {
      setLoadingInterfaces(true);
      setInterfacesError(null);
      fetchFeature("interfaces", "interfaces")
        .then((data) => {
          setInterfacesData(data);
        })
        .catch((err) => {
          setInterfacesError(err.message || "Failed to load interfaces.");
        })
        .finally(() => {
          setLoadingInterfaces(false);
        });

      setLoadingInterfacesTrunk(true);
      setInterfacesTrunkError(null);
      fetchFeature("interfaces_trunk", "interfacesTrunk") // Assuming a new feature endpoint for trunk
        .then((data) => {
          setInterfacesTrunkData(data);
        })
        .catch((err) => {
          setInterfacesTrunkError(err.message || "Failed to load interfaces trunk.");
        })
        .finally(() => {
          setLoadingInterfacesTrunk(false);
        });
    }
  }, [key, id, fetchFeature, interfacesData, loadingInterfaces, interfacesTrunkData, loadingInterfacesTrunk, device?.is_reachable]);

  // Users Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "users" && id && !activeUsersData && !loadingActiveUsers) {
      setLoadingActiveUsers(true);
      setActiveUsersError(null);
      fetchFeature("active_users", "active_users")
        .then((data) => {
          setActiveUsersData(data);
        })
        .catch((err) => {
          setActiveUsersError(err.message || "Failed to load active users.");
        })
        .finally(() => {
          setLoadingActiveUsers(false);
        });
    }
    if (key === "users" && id && !localUsersData && !loadingLocalUsers) {
      setLoadingLocalUsers(true);
      setLocalUsersError(null);
      fetchFeature("local_users", "local_users")
        .then((data) => {
          setLocalUsersData(data);
        })
        .catch((err) => {
          setLocalUsersError(err.message || "Failed to load local users.");
        })
        .finally(() => {
          setLoadingLocalUsers(false);
        });
    }
  }, [key, id, fetchFeature, activeUsersData, loadingActiveUsers, localUsersData, loadingLocalUsers, device?.is_reachable]);

  // VLANs Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "vlans" && id && !vlanBriefData && !loadingVlanBrief) {
      setLoadingVlanBrief(true);
      setVlanBriefError(null);
      fetchFeature("vlans", "vlan_brief")
        .then((data) => {
          setVlanBriefData(data);
        })
        .catch((err) => {
          setVlanBriefError(err.message || "Failed to load VLANs.");
        })
        .finally(() => {
          setLoadingVlanBrief(false);
        });
    }
  }, [key, id, fetchFeature, vlanBriefData, loadingVlanBrief, device?.is_reachable]);

  // Routing Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "routing" && id && !routingTableData && !loadingRoutingTable) {
      setLoadingRoutingTable(true);
      setRoutingTableError(null);
      fetchFeature("routing", "routing_table")
        .then((data) => {
          setRoutingTableData(data);
        })
        .catch((err) => {
          setRoutingTableError(err.message || "Failed to load routing table.");
        })
        .finally(() => {
          setLoadingRoutingTable(false);
        });
    }
  }, [key, id, fetchFeature, routingTableData, loadingRoutingTable, device?.is_reachable]);

  // Security Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "security" && id && !aclsData && !loadingAcls) {
      setLoadingAcls(true);
      setAclsError(null);
      fetchFeature("acls", "acls_data")
        .then((data) => {
          setAclsData(data);
        })
        .catch((err) => {
          setAclsError(err.message || "Failed to load ACLs.");
        })
        .finally(() => {
          setLoadingAcls(false);
        });
    }
    if (key === "security" && id && !aaaConfigData && !loadingAaaConfig) {
      setLoadingAaaConfig(true);
      setAaaConfigError(null);
      fetchFeature("aaa", "aaa_config_data")
        .then((data) => {
          setAaaConfigData(data);
        })
        .catch((err) => {
          setAaaConfigError(err.message || "Failed to load AAA config.");
        })
        .finally(() => {
          setLoadingAaaConfig(false);
        });
    }
  }, [key, id, fetchFeature, aclsData, loadingAcls, aaaConfigData, loadingAaaConfig, device?.is_reachable]);

  // Logging Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "logging" && id && !loggingConfigData && !loadingLoggingConfig) {
      setLoadingLoggingConfig(true);
      setLoggingConfigError(null);
      fetchFeature("logging", "logging_config_data")
        .then((data) => {
          setLoggingConfigData(data);
        })
        .catch((err) => {
          setLoggingConfigError(err.message || "Failed to load logging config.");
        })
        .finally(() => {
          setLoadingLoggingConfig(false);
        });
    }
  }, [key, id, fetchFeature, loggingConfigData, loadingLoggingConfig, device?.is_reachable]);

  // SNMP Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "snmp" && id && !snmpConfigData && !loadingSnmpConfig) {
      setLoadingSnmpConfig(true);
      setSnmpConfigError(null);
      fetchFeature("snmp", "snmp_config_data")
        .then((data) => {
          setSnmpConfigData(data);
        })
        .catch((err) => {
          setSnmpConfigError(err.message || "Failed to load SNMP config.");
        })
        .finally(() => {
          setLoadingSnmpConfig(false);
        });
    }
  }, [key, id, fetchFeature, snmpConfigData, loadingSnmpConfig, device?.is_reachable]);

  // NTP Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "ntp" && id && !ntpConfigData && !loadingNtpConfig) {
      setLoadingNtpConfig(true);
      setNtpConfigError(null);
      fetchFeature("ntp", "ntp_config_data")
        .then((data) => {
          setNtpConfigData(data);
        })
        .catch((err) => {
          setNtpConfigError(err.message || "Failed to load NTP config.");
        })
        .finally(() => {
          setLoadingNtpConfig(false);
        });
    }
  }, [key, id, fetchFeature, ntpConfigData, loadingNtpConfig, device?.is_reachable]);

  // Clock for General Tab
  useEffect(() => {
    if (!device?.is_reachable) return; // Do not fetch if device is offline
    if (key === "general" && id && !clockData && !loadingClock) {
      setLoadingClock(true);
      setClockError(null);
      fetchFeature("clock", "current_clock")
        .then((data) => {
          setClockData(data);
        })
        .catch((err) => {
          setClockError(err.message || "Failed to load clock.");
        })
        .finally(() => {
          setLoadingClock(false);
        });
    }
  }, [key, id, fetchFeature, clockData, loadingClock, device?.is_reachable]);

  // ... rest of the component
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

    setClearingCache(true);
    setCacheClearSuccess(null);
    setCacheClearError(null);

    const endpoint = `/api/devices/${id}/cache/clear`;
    const prefixesToClear = [
      "details", // Clear specific device details cache
      "system",
      "interfaces",
      "vlans",
      "routing",
      "acls",
      "snmp",
      "logging",
      "ntp",
      "aaa",
      "active_users",
      "local_users",
      "clock",
    ];

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ prefixes: prefixesToClear }),
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

      setCacheClearSuccess("Cache cleared successfully!");
      // For now, just clear the local state of fetched data to force re-fetch on tab switch
      setInterfacesData(null);
      setInterfacesTrunkData(null);
      setActiveUsersData(null);
      setLocalUsersData(null);
      setVlanBriefData(null);
      setRoutingTableData(null);
      setAclsData(null);
      setAaaConfigData(null);
      setLoggingConfigData(null);
      setSnmpConfigData(null);
      setNtpConfigData(null);
      setClockData(null);
    } catch (err: any) {
      setCacheClearError(err.message || "An unknown error occurred while clearing cache.");
    } finally {
      setClearingCache(false);
    }
  };

  if (loading) {
    return (
      <Container fluid className="mt-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p>Loading device details...</p>
      </Container>
    );
  }

  if (errors.primary) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="danger">
          Error: {errors.primary}. Please try again later.
        </Alert>
      </Container>
    );
  }

  if (!device) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="warning">Device not found.</Alert>
      </Container>
    );
  }

  // Modified renderCard to accept loading and error states
  const renderCard = (
    title: string,
    data: any[] | null, // Now accepts specific data
    loadingState: boolean, // New loading state
    errorState: string | null, // New error state
    render: (data: any) => JSX.Element,
  ) => (
    <Card className="mb-4">
      <Card.Body style={{ maxHeight: "400px", overflowY: "auto" }}>
        <Card.Title as="h2">{title}</Card.Title>
        {loadingState ? (
          <div className="text-center">
            <Spinner animation="border" size="sm" /> Loading {title.toLowerCase()}...
          </div>
        ) : errorState ? (
          <Alert variant="warning">
            Could not load {title.toLowerCase()}: {errorState}
          </Alert>
        ) : data && (Array.isArray(data) ? data.length > 0 : data) ? (
          render(data)
        ) : (
          <Card.Text>No {title.toLowerCase()} information available.</Card.Text>
        )}
      </Card.Body>
    </Card>
  );

  return (
    <Container fluid className="mt-4">
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title as="h1" className="mb-3">
                {device.name} ({device.ip_address})
                <Badge bg={device.is_reachable ? "success" : "danger"} className="ms-2">
                  {device.is_reachable ? "Online" : "Offline"}
                </Badge>
              </Card.Title>
              <Card.Subtitle className="mb-2 text-muted">
                {device.device_type}
              </Card.Subtitle>
              <Button variant="secondary" onClick={() => navigate(-1)}>
                Back to Devices
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Tabs
        id="device-details-tabs"
        activeKey={key}
        onSelect={(k) => setKey(k!)}
        className="mb-3"
      >
        <Tab eventKey="general" title="General Information">
          <Row className="mt-3">
            <Col md={6}>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">Basic Details</Card.Title>
                  <Card.Text>
                    <strong>IP Address:</strong> {device.ip_address}
                    <br />
                    <strong>Port:</strong> {device.port}
                    <br />
                    <strong>Username:</strong> {device.username}
                    <br />
                    <strong>Version:</strong> {device.version?.software_image} {device.version?.version || "N/A"}
                    <br />
                    <strong>Hostname:</strong> {device.version?.hostname || "N/A"}
                    <br />
                    <strong>Clock:</strong>{" "}
                    {loadingClock ? (
                      <Spinner animation="border" size="sm" />
                    ) : clockError ? (
                      <span className="text-danger">Error: {clockError}</span>
                    ) : (
                      clockData || "N/A"
                    )}
                  </Card.Text>
                </Card.Body>
              </Card>
            </Col>
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
                      {commandOutput}
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
            <Col md={6}>
              <Card>
                <Card.Body>
                  <Card.Title as="h2">Cache Management</Card.Title>
                  <Button
                    variant="warning"
                    onClick={handleClearCache}
                    disabled={clearingCache}
                    className="mt-3"
                  >
                    {clearingCache ? (
                      <Spinner as="span" animation="border" size="sm" />
                    ) : (
                      "Clear Device Cache"
                    )}
                  </Button>
                  {cacheClearSuccess && (
                    <Alert variant="success" className="mt-3">
                      {cacheClearSuccess}
                    </Alert>
                  )}
                  {cacheClearError && (
                    <Alert variant="danger" className="mt-3">
                      {cacheClearError}
                    </Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>

        <Tab eventKey="interfaces" title="Interfaces">
          {device.is_reachable ? (
            <Row className="mt-3">
              <Col md={12}>
                {renderCard("Interfaces", interfacesData, loadingInterfaces, interfacesError, (data) => (
                  <div className="table-responsive">
                    <Table striped bordered hover size="sm">
                      <thead>
                        <tr>
                          <th>Interface</th>
                          <th>IP Address</th>
                          <th>Status</th>
                          <th>Protocol</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.map((iface: any, index: number) => (
                          <tr key={index}>
                            <td>{iface.interface}</td>
                            <td>{iface.ip_address || "Unassigned"}</td>
                            <td>{iface.status}</td>
                            <td>{iface.proto}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                ))}
              </Col>
              <Col md={12}>
                {renderCard("Interfaces Trunk", interfacesTrunkData, loadingInterfacesTrunk, interfacesTrunkError, (data) => (
                  <div className="table-responsive">
                    <Table striped bordered hover size="sm">
                      <thead>
                        <tr>
                          <th>Port</th>
                          <th>Mode</th>
                          <th>Encapsulation</th>
                          <th>Status</th>
                          <th>VLANs Allowed</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.map((trunk: any, index: number) => (
                          <tr key={index}>
                            <td>{trunk.port}</td>
                            <td>{trunk.mode}</td>
                            <td>{trunk.encapsulation}</td>
                            <td>{trunk.status}</td>
                            <td>{trunk.vlans_allowed}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                ))}
              </Col>
            </Row>
          ) : (
            <Alert variant="info" className="mt-3">
              Device is offline. Feature details are not available.
            </Alert>
          )}
        </Tab>

        <Tab eventKey="users" title="Users">
          {device.is_reachable ? (
            <Row className="mt-3">
              <Col md={6}>
                {renderCard("Active Users", activeUsersData, loadingActiveUsers, activeUsersError, (data) => (
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Username</th>
                        <th>Line</th>
                        <th>Idle</th>
                        <th>Location</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.map((user: any, index: number) => (
                        <tr key={index}>
                          <td>{user.user}</td>
                          <td>{user.line}</td>
                          <td>{user.idle}</td>
                          <td>{user.location}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                ))}
              </Col>
              <Col md={6}>
                {renderCard("Local Users", localUsersData, loadingLocalUsers, localUsersError, (data) => (
                  <ListGroup>
                    {data.map((user: any, index: number) => (
                      <ListGroup.Item
                        key={index}
                        className="d-flex justify-content-between align-items-center"
                      >
                        <span className="text-monospace small">
                          {user.username}
                        </span>
                        {user.privilege && (
                          <Badge bg="info">Privilege: {user.privilege}</Badge>
                        )}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                ))}
              </Col>
            </Row>
          ) : (
            <Alert variant="info" className="mt-3">
              Device is offline. Feature details are not available.
            </Alert>
          )}
        </Tab>

        <Tab eventKey="vlans" title="VLANs">
          {device.is_reachable ? (
            <Row className="mt-3">
              <Col md={12}>
                {renderCard("VLAN Brief", vlanBriefData, loadingVlanBrief, vlanBriefError, (data) => (
                  <div className="table-responsive">
                    <Table striped bordered hover size="sm">
                      <thead>
                        <tr>
                          <th>VLAN ID</th>
                          <th>Name</th>
                          <th>Status</th>
                          <th>Ports</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.map((vlan: any, index: number) => (
                          <tr key={index}>
                            <td>{vlan.vlan_id}</td>
                            <td>{vlan.vlan_name}</td>
                            <td>{vlan.status}</td>
                            <td>{Array.isArray(vlan.interfaces) ? vlan.interfaces.join(", ") : vlan.interfaces}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                ))}
              </Col>
            </Row>
          ) : (
            <Alert variant="info" className="mt-3">
              Device is offline. Feature details are not available.
            </Alert>
          )}
        </Tab>

        <Tab eventKey="routing" title="Routing">
          {device.is_reachable ? (
            <Row className="mt-3">
              <Col md={12}>
                {renderCard("Routing Table", routingTableData, loadingRoutingTable, routingTableError, (data) => (
                  <div className="table-responsive">
                    <Table striped bordered hover size="sm">
                      <thead>
                        <tr>
                          <th>Protocol</th>
                          <th>VRF</th>
                          <th>Type</th>
                          <th>Network</th>
                          <th>Prefix Length</th>
                          <th>Distance</th>
                          <th>Metric</th>
                          <th>Next Hop IP</th>
                          <th>Next Hop VRF</th>
                          <th>Next Hop Interface</th>
                          <th>Uptime</th>
                          <th>Flag</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.map((route: any, index: number) => (
                          <tr key={index}>
                            <td>{route.protocol}</td>
                            <td>{route.vrf || "N/A"}</td>
                            <td>{route.type || "N/A"}</td>
                            <td>{route.network}</td>
                            <td>{route.prefix_length || "N/A"}</td>
                            <td>{route.distance || "N/A"}</td>
                            <td>{route.metric || "N/A"}</td>
                            <td>{route.nexthop_ip || "N/A"}</td>
                            <td>{route.nexthop_vrf || "N/A"}</td>
                            <td>{route.nexthop_if || "N/A"}</td>
                            <td>{route.uptime || "N/A"}</td>
                            <td>{route.flag || "N/A"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                ))}
              </Col>
            </Row>
          ) : (
            <Alert variant="info" className="mt-3">
              Device is offline. Feature details are not available.
            </Alert>
          )}
        </Tab>

        <Tab eventKey="security" title="Security">
          {device.is_reachable ? (
            <Row className="mt-3">
              <Col md={12}>
                {renderCard("ACLs", aclsData, loadingAcls, aclsError, (data) => (
                  <ListGroup>
                    {data.map((acl: any, index: number) => (
                      <ListGroup.Item key={index}>
                        <strong>{acl.line}</strong>{acl.rules?.join("; ") ?? ""}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                ))}
              </Col>
              <Col md={12}>
                {renderCard("AAA Config", aaaConfigData, loadingAaaConfig, aaaConfigError, (data) => (
                  <ListGroup>
                    {data.map((config: any, index: number) => (
                      <ListGroup.Item key={index}>{config.line}</ListGroup.Item>
                    ))}
                  </ListGroup>
                ))}
              </Col>
            </Row>
          ) : (
            <Alert variant="info" className="mt-3">
              Device is offline. Feature details are not available.
            </Alert>
          )}
        </Tab>

        <Tab eventKey="logging" title="Logging">
          {device.is_reachable ? (
            <Row className="mt-3">
              <Col md={12}>
                {renderCard("Logging Config", loggingConfigData, loadingLoggingConfig, loggingConfigError, (data) => (
                  <ListGroup>
                    {data.map((config: any, index: number) => (
                      <ListGroup.Item key={index}>{config.line}</ListGroup.Item>
                    ))}
                  </ListGroup>
                ))}
              </Col>
            </Row>
          ) : (
            <Alert variant="info" className="mt-3">
              Device is offline. Feature details are not available.
            </Alert>
          )}
        </Tab>

        <Tab eventKey="snmp" title="SNMP">
          {device.is_reachable ? (
            <Row className="mt-3">
              <Col md={12}>
                {renderCard("SNMP Config", snmpConfigData, loadingSnmpConfig, snmpConfigError, (data) => (
                  <ListGroup>
                    {data.map((config: any, index: number) => (
                      <ListGroup.Item key={index}>{config.line}</ListGroup.Item>
                    ))}
                  </ListGroup>
                ))}
              </Col>
            </Row>
          ) : (
            <Alert variant="info" className="mt-3">
              Device is offline. Feature details are not available.
            </Alert>
          )}
        </Tab>

        <Tab eventKey="ntp" title="NTP">
          {device.is_reachable ? (
            <Row className="mt-3">
              <Col md={12}>
                {renderCard("NTP Config", ntpConfigData, loadingNtpConfig, ntpConfigError, (data) => (
                  <ListGroup>
                    {data.map((config: any, index: number) => (
                      <ListGroup.Item key={index}>{config.line}</ListGroup.Item>
                    ))}
                  </ListGroup>
                ))}
              </Col>
            </Row>
          ) : (
            <Alert variant="info" className="mt-3">
              Device is offline. Feature details are not available.
            </Alert>
          )}
        </Tab>
      </Tabs>
    </Container>
  );
};

export default DeviceDetailPage;