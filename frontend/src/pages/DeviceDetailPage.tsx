import { useEffect, useState } from "react";
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
} from "react-bootstrap";
import { useAuth } from "../hooks/useAuth";

interface Device {
  id: string;
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
}

interface DeviceDetail extends Device {
  version: string;
  interfaces: {
    interface: string;
    ip_address: string;
    status: string;
    proto: string;
  }[];
  hostname?: string;
  activeUsers?: any[];
  localUsers?: any[];
  clock?: string;
  vlanDetails?: any[];
  vtpStatus?: any[];
  spanningTreeSummary?: any[];
  interfacesTrunk?: any[];
  lineConfig?: string[];
  banners?: { [key: string]: string };
  ntpConfig?: any[];
  snmpConfig?: any[];
  loggingConfig?: any[];
  acls?: any[];
  aaaConfig?: any[];
  cdpNeighbors?: any[];
  ospfNeighbors?: any[];
  eigrpNeighbors?: any[];
  routingProtocolConfig?: any[];
  natConfig?: any[];
  vpnConfig?: any[];
  lldpNeighbors?: any[];
  portSecurity?: any[];
  etherchannelSummary?: any[];
  vlanConfig?: any[];
  interfaceVlanMembership?: any[];
}

const DeviceDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const [device, setDevice] = useState<DeviceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [command, setCommand] = useState("");
  const [isConfigCommand, setIsConfigCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);
  const [deviceLevel, setDeviceLevel] = useState<string | null>(null);
  const [multilineCommands, setMultilineCommands] = useState<
    { id: number; command: string; pattern: string }[]
  >([{ id: Date.now(), command: "", pattern: "" }]);
  const [executingCommand, setExecutingCommand] = useState(false);

  // New states for additional device details
  const [hostname, setHostname] = useState<string | null>(null);
  const [activeUsers, setActiveUsers] = useState<any[] | null>(null);
  const [localUsers, setLocalUsers] = useState<any[] | null>(null);
  const [clock, setClock] = useState<string | null>(null);
  const [vlanDetails, setVlanDetails] = useState<any[] | null>(null);
  const [vtpStatus, setVtpStatus] = useState<any[] | null>(null);
  const [spanningTreeSummary, setSpanningTreeSummary] = useState<any[] | null>(null);
  const [interfacesTrunk, setInterfacesTrunk] = useState<any[] | null>(null);
  const [lineConfig, setLineConfig] = useState<string[] | null>(null);
  const [banners, setBanners] = useState<{[key: string]: string} | null>(null);
  const [ntpConfig, setNtpConfig] = useState<any[] | null>(null);
  const [snmpConfig, setSnmpConfig] = useState<any[] | null>(null);
  const [loggingConfig, setLoggingConfig] = useState<any[] | null>(null);
  const [acls, setAcls] = useState<any[] | null>(null);
  const [aaaConfig, setAaaConfig] = useState<any[] | null>(null);
  const [cdpNeighbors, setCdpNeighbors] = useState<any[] | null>(null);
  const [ospfNeighbors, setOspfNeighbors] = useState<any[] | null>(null);
  const [eigrpNeighbors, setEigrpNeighbors] = useState<any[] | null>(null);
  const [routingProtocolConfig, setRoutingProtocolConfig] = useState<any[] | null>(null);
  const [natConfig, setNatConfig] = useState<any[] | null>(null);
  const [vpnConfig, setVpnConfig] = useState<any[] | null>(null);
  const [lldpNeighbors, setLldpNeighbors] = useState<any[] | null>(null);
  const [portSecurity, setPortSecurity] = useState<any[] | null>(null);
  const [etherchannelSummary, setEtherchannelSummary] = useState<any[] | null>(null);
  const [vlanConfig, setVlanConfig] = useState<any[] | null>(null);
  const [interfaceVlanMembership, setInterfaceVlanMembership] = useState<any[] | null>(null);

  useEffect(() => {
    const fetchAllDeviceDetails = async () => {
      if (!token) {
        setError("No authentication token found. Please log in.");
        logout();
        navigate("/login");
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Fetch basic device details (already includes version and interfaces)
        const deviceResponse = await fetch(`/api/devices/${id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (deviceResponse.status === 401) {
          setError("Session expired or unauthorized. Please log in again.");
          logout();
          navigate("/login");
          return;
        }

        if (!deviceResponse.ok) {
          throw new Error(
            `Failed to fetch device details: ${deviceResponse.statusText}`,
          );
        }
        const deviceData: DeviceDetail = await deviceResponse.json();
        setDevice(deviceData);

        // Fetch additional details using new cached APIs
        const fetchDetail = async (url: string, setter: Function) => {
          try {
            const response = await fetch(url, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            });
            if (response.status === 401) {
              setError("Session expired or unauthorized. Please log in again.");
              logout();
              navigate("/login");
              return;
            }
            if (!response.ok) {
              throw new Error(`Failed to fetch ${url}: ${response.statusText}`);
            }
            const data = await response.json();
            setter(data);
          } catch (err: any) {
            console.error(`Error fetching ${url}:`, err);
            // Don't set global error for individual detail fetches, just log
          }
        };

        await Promise.all([
          fetchDetail(`/api/devices/${id}/hostname`, setHostname),
          fetchDetail(`/api/devices/${id}/active-users`, setActiveUsers),
          fetchDetail(`/api/devices/${id}/local-users`, setLocalUsers),
          fetchDetail(`/api/devices/${id}/clock`, setClock),
          fetchDetail(`/api/devices/${id}/vlan-details`, setVlanDetails),
          fetchDetail(`/api/devices/${id}/vtp-status`, setVtpStatus),
          fetchDetail(`/api/devices/${id}/spanning-tree-summary`, setSpanningTreeSummary),
          fetchDetail(`/api/devices/${id}/interfaces-trunk`, setInterfacesTrunk),
          fetchDetail(`/api/devices/${id}/line-config`, setLineConfig),
          fetchDetail(`/api/devices/${id}/banners`, setBanners),
          fetchDetail(`/api/devices/${id}/ntp-config`, setNtpConfig),
          fetchDetail(`/api/devices/${id}/snmp-config`, setSnmpConfig),
          fetchDetail(`/api/devices/${id}/logging-config`, setLoggingConfig),
          fetchDetail(`/api/devices/${id}/acls`, setAcls),
          fetchDetail(`/api/devices/${id}/aaa-config`, setAaaConfig),
          fetchDetail(`/api/devices/${id}/cdp-neighbors`, setCdpNeighbors),
          fetchDetail(`/api/devices/${id}/ospf-neighbors`, setOspfNeighbors),
          fetchDetail(`/api/devices/${id}/eigrp-neighbors`, setEigrpNeighbors),
          fetchDetail(`/api/devices/${id}/routing-protocol-config`, setRoutingProtocolConfig),
          fetchDetail(`/api/devices/${id}/nat-config`, setNatConfig),
          fetchDetail(`/api/devices/${id}/vpn-config`, setVpnConfig),
          fetchDetail(`/api/devices/${id}/lldp-neighbors`, setLldpNeighbors),
          fetchDetail(`/api/devices/${id}/port-security`, setPortSecurity),
          fetchDetail(`/api/devices/${id}/etherchannel-summary`, setEtherchannelSummary),
          fetchDetail(`/api/devices/${id}/vlan-config`, setVlanConfig),
          fetchDetail(`/api/devices/${id}/interface-vlan-membership`, setInterfaceVlanMembership),
        ]);

      } catch (err: any) {
        console.error("Error fetching all device details:", err);
        setError(err.message || "Failed to load device details.");
      } finally {
        setLoading(false);
      }
    };

    fetchAllDeviceDetails();
  }, [id, token, navigate, logout]);

  const handleExecuteCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    setExecutingCommand(true);
    setCommandOutput(null);
    setError(null);

    let commandsToExecute: { command: string; pattern: string }[] = [];

    // Clear the command input immediately after it's captured
    setCommand("");

    let endpoint = "";
    let payload: any = {};

    // Check if the command contains actual newlines (not just a trailing one)
    const containsMultipleLines = command.trim().includes("\n");

    console.log("--- handleExecuteCommand Debug ---");
    console.log("command:", command);
    console.log("containsMultipleLines:", containsMultipleLines);
    console.log("multilineCommands:", multilineCommands);

    const trimmedCommand = command.trim().toLowerCase();

    if (command.trim() !== "") { // Check if command is not empty first
      if (containsMultipleLines) {
        console.log("Branch: containsMultipleLines");
        if (isConfigCommand) { // If it's a multi-line config command
          endpoint = `/api/devices/${id}/execute-command`; // Send to execute-command
          const configCommands = command.split('\n').map(line => line.trim()).filter(line => line.length > 0);
          payload = { command: configCommands, is_config: true };
          commandsToExecute = configCommands.map((line) => ({
            command: line,
            pattern: "",
          }));
        } else { // If it's a multi-line non-config command (e.g., for send_multiline)
          endpoint = `/api/devices/${id}/execute-multiline-command`;
          const singleCommandLines = command
            .trim()
            .split("\n")
            .filter((line) => line.trim() !== "");
          payload = {
            commands: singleCommandLines.map((line) => [line, ""]),
          };
          commandsToExecute = singleCommandLines.map((line) => ({
            command: line,
            pattern: "",
          }));
        }
      } else { // Single line command
        console.log("Branch: Single Command");

        // Special handling for "conf t" and "configure terminal" to use multiline endpoint
        const isSpecialConfigEntry = trimmedCommand === "conf t" || trimmedCommand === "configure terminal";

        if (isSpecialConfigEntry) {
          endpoint = `/api/devices/${id}/execute-multiline-command`;
          payload = { commands: [[command.trim(), ""]] };
          commandsToExecute = [{ command: command.trim(), pattern: "" }];
        } else {
          endpoint = `/api/devices/${id}/execute-command`;
          payload = { command: command, is_config: isConfigCommand }; // Use the new flag
          commandsToExecute = [{ command: command, pattern: "" }];
        }
      }
    } else if (multilineCommands.some((pair) => pair.command.trim() !== "")) {
      console.log("Branch: Separate Multiline Input");
      endpoint = `/api/devices/${id}/execute-multiline-command`;
      payload = {
        commands: multilineCommands.map((pair) => [
          pair.command,
          pair.pattern,
        ]),
      };
      commandsToExecute = multilineCommands;
    } else {
      setError("Please enter a command or multiline commands to execute.");
      setExecutingCommand(false);
      return;
    }

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
        setError("Session expired or unauthorized. Please log in again.");
        logout();
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to execute command");
      }

      const data = await response.json();
      setCommandOutput(data.output);

      const newDeviceLevel = data.device_level || null;

      setDeviceLevel(newDeviceLevel);
    } catch (err: any) {
      console.error("Error executing command:", err);
      setError(err.message || "Failed to execute command.");
    } finally {
      setExecutingCommand(false);
    }
  };

  const handleCommandChange = (
    id: number,
    field: "command" | "pattern",
    value: string,
  ) => {
    setMultilineCommands((prev) =>
      prev.map((pair) => (pair.id === id ? { ...pair, [field]: value } : pair)),
    );
  };

  const handleAddCommandPair = () => {
    setMultilineCommands((prev) => [
      ...prev,
      { id: Date.now(), command: "", pattern: "" },
    ]);
  };

  const handleRemoveCommandPair = (id: number) => {
    setMultilineCommands((prev) => prev.filter((pair) => pair.id !== id));
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

  if (error) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="danger">{error}</Alert>
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

  return (
    <Container fluid className="mt-4">
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title as="h1" className="mb-3">
                {device.name} ({device.ip_address})
              </Card.Title>
              <Card.Subtitle className="mb-2 text-muted">
                {device.device_type}
              </Card.Subtitle>
              <Card.Text>
                <strong>IP Address:</strong> {device.ip_address}
                <br />
                <strong>Port:</strong> {device.port}
                <br />
                <strong>Username:</strong> {device.username}
                <br />
                <strong>Version:</strong> {device.version || "N/A"}
                <br />
                <strong>Hostname:</strong> {hostname || "N/A"}
                <br />
                <strong>Clock:</strong> {clock || "N/A"}
              </Card.Text>
              <Button variant="secondary" onClick={() => navigate(-1)}>
                Back to Devices
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Interfaces</Card.Title>
              {device.interfaces && device.interfaces.length > 0 ? (
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
                      {device.interfaces.map((iface, index) => (
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
              ) : (
                <Card.Text>No interface information available.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Execute Command</Card.Title>
              <Form onSubmit={handleExecuteCommand}>
                <Form.Group className="mb-3" controlId="commandInput">
                  <Form.Label>Command</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    placeholder="Enter command to execute (e.g., show version)"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    required
                  />
                </Form.Group>
                <Form.Group className="mb-3" controlId="isConfigCommandCheckbox">
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
                    <Spinner animation="border" size="sm" />
                  ) : (
                    "Execute"
                  )}
                </Button>
              </Form>
              {commandOutput && (
                <div
                  className="mt-3 p-3 bg-light rounded"
                  style={{ whiteSpace: "pre-wrap", fontFamily: "monospace" }}
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
              {error && !commandOutput && (
                <Alert variant="danger" className="mt-3">
                  {error}
                </Alert>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Users</Card.Title>
              {activeUsers && activeUsers.length > 0 ? (
                <>
                  <h5>Active Users</h5>
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
                      {activeUsers.map((user, index) => (
                        <tr key={index}>
                          <td>{user.username}</td>
                          <td>{user.line}</td>
                          <td>{user.idle}</td>
                          <td>{user.location}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No active users found.</Card.Text>
              )}

              {localUsers && localUsers.length > 0 ? (
                <>
                  <h5 className="mt-3">Local Users</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Username</th>
                        <th>Privilege</th>
                      </tr>
                    </thead>
                    <tbody>
                      {localUsers.map((user, index) => (
                        <tr key={index}>
                          <td>{user.username}</td>
                          <td>{user.privilege}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No local users found.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">VLANs</Card.Title>
              {vlanDetails && vlanDetails.length > 0 ? (
                <>
                  <h5>VLAN Details</h5>
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
                      {vlanDetails.map((vlan, index) => (
                        <tr key={index}>
                          <td>{vlan.vlan_id}</td>
                          <td>{vlan.name}</td>
                          <td>{vlan.status}</td>
                          <td>{vlan.ports}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No VLAN details available.</Card.Text>
              )}

              {vtpStatus && vtpStatus.length > 0 ? (
                <>
                  <h5 className="mt-3">VTP Status</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Domain</th>
                        <th>Mode</th>
                        <th>Revision</th>
                      </tr>
                    </thead>
                    <tbody>
                      {vtpStatus.map((vtp, index) => (
                        <tr key={index}>
                          <td>{vtp.domain}</td>
                          <td>{vtp.mode}</td>
                          <td>{vtp.revision}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No VTP status available.</Card.Text>
              )}

              {vlanConfig && vlanConfig.length > 0 ? (
                <>
                  <h5 className="mt-3">VLAN Configuration</h5>
                  <ListGroup>
                    {vlanConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No VLAN configuration available.</Card.Text>
              )}

              {interfaceVlanMembership && interfaceVlanMembership.length > 0 ? (
                <>
                  <h5 className="mt-3">Interface VLAN Membership</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Interface</th>
                        <th>VLAN</th>
                        <th>Mode</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {interfaceVlanMembership.map((item, index) => (
                        <tr key={index}>
                          <td>{item.interface}</td>
                          <td>{item.vlan}</td>
                          <td>{item.mode}</td>
                          <td>{item.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No interface VLAN membership available.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Spanning Tree</Card.Title>
              {spanningTreeSummary && spanningTreeSummary.length > 0 ? (
                <Table striped bordered hover size="sm">
                  <thead>
                    <tr>
                      <th>VLAN</th>
                      <th>Root ID</th>
                      <th>Bridge ID</th>
                      <th>Interfaces</th>
                    </tr>
                  </thead>
                  <tbody>
                    {spanningTreeSummary.map((stp, index) => (
                      <tr key={index}>
                        <td>{stp.vlan}</td>
                        <td>{stp.root_id}</td>
                        <td>{stp.bridge_id}</td>
                        <td>{stp.interfaces}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              ) : (
                <Card.Text>No Spanning Tree summary available.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Routing</Card.Title>
              {routingProtocolConfig && routingProtocolConfig.length > 0 ? (
                <>
                  <h5>Routing Protocol Configuration</h5>
                  <ListGroup>
                    {routingProtocolConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No routing protocol configuration available.</Card.Text>
              )}

              {ospfNeighbors && ospfNeighbors.length > 0 ? (
                <>
                  <h5 className="mt-3">OSPF Neighbors</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Neighbor ID</th>
                        <th>State</th>
                        <th>Address</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ospfNeighbors.map((neighbor, index) => (
                        <tr key={index}>
                          <td>{neighbor.neighbor_id}</td>
                          <td>{neighbor.state}</td>
                          <td>{neighbor.address}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No OSPF neighbors found.</Card.Text>
              )}

              {eigrpNeighbors && eigrpNeighbors.length > 0 ? (
                <>
                  <h5 className="mt-3">EIGRP Neighbors</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>AS</th>
                        <th>Address</th>
                        <th>Hold Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {eigrpNeighbors.map((neighbor, index) => (
                        <tr key={index}>
                          <td>{neighbor.as}</td>
                          <td>{neighbor.address}</td>
                          <td>{neighbor.hold_time}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No EIGRP neighbors found.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Security</Card.Title>
              {acls && acls.length > 0 ? (
                <>
                  <h5>Access Control Lists (ACLs)</h5>
                  <ListGroup>
                    {acls.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No ACLs available.</Card.Text>
              )}

              {aaaConfig && aaaConfig.length > 0 ? (
                <>
                  <h5 className="mt-3">AAA Configuration</h5>
                  <ListGroup>
                    {aaaConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No AAA configuration available.</Card.Text>
              )}

              {portSecurity && portSecurity.length > 0 ? (
                <>
                  <h5 className="mt-3">Port Security</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Interface</th>
                        <th>Status</th>
                        <th>Violation Mode</th>
                        <th>Max MACs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {portSecurity.map((ps, index) => (
                        <tr key={index}>
                          <td>{ps.interface}</td>
                          <td>{ps.status}</td>
                          <td>{ps.violation_mode}</td>
                          <td>{ps.max_macs}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No port security information available.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Network Services</Card.Title>
              {ntpConfig && ntpConfig.length > 0 ? (
                <>
                  <h5>NTP Configuration</h5>
                  <ListGroup>
                    {ntpConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No NTP configuration available.</Card.Text>
              )}

              {snmpConfig && snmpConfig.length > 0 ? (
                <>
                  <h5 className="mt-3">SNMP Configuration</h5>
                  <ListGroup>
                    {snmpConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No SNMP configuration available.</Card.Text>
              )}

              {loggingConfig && loggingConfig.length > 0 ? (
                <>
                  <h5 className="mt-3">Logging Configuration</h5>
                  <ListGroup>
                    {loggingConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No logging configuration available.</Card.Text>
              )}

              {natConfig && natConfig.length > 0 ? (
                <>
                  <h5 className="mt-3">NAT Configuration</h5>
                  <ListGroup>
                    {natConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No NAT configuration available.</Card.Text>
              )}

              {vpnConfig && vpnConfig.length > 0 ? (
                <>
                  <h5 className="mt-3">VPN Configuration</h5>
                  <ListGroup>
                    {vpnConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No VPN configuration available.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Neighbors</Card.Title>
              {cdpNeighbors && cdpNeighbors.length > 0 ? (
                <>
                  <h5>CDP Neighbors</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Device ID</th>
                        <th>Local Interface</th>
                        <th>Holdtime</th>
                        <th>Capability</th>
                        <th>Platform</th>
                        <th>Port ID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cdpNeighbors.map((neighbor, index) => (
                        <tr key={index}>
                          <td>{neighbor.device_id}</td>
                          <td>{neighbor.local_interface}</td>
                          <td>{neighbor.holdtime}</td>
                          <td>{neighbor.capability}</td>
                          <td>{neighbor.platform}</td>
                          <td>{neighbor.port_id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No CDP neighbors found.</Card.Text>
              )}

              {lldpNeighbors && lldpNeighbors.length > 0 ? (
                <>
                  <h5 className="mt-3">LLDP Neighbors</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Chassis ID</th>
                        <th>Port ID</th>
                        <th>Port Description</th>
                        <th>System Name</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lldpNeighbors.map((neighbor, index) => (
                        <tr key={index}>
                          <td>{neighbor.chassis_id}</td>
                          <td>{neighbor.port_id}</td>
                          <td>{neighbor.port_description}</td>
                          <td>{neighbor.system_name}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No LLDP neighbors found.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Card.Title as="h2">Other Configuration</Card.Title>
              {lineConfig && lineConfig.length > 0 ? (
                <>
                  <h5>Line Configuration</h5>
                  <ListGroup>
                    {lineConfig.map((line, index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        {line}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No line configuration available.</Card.Text>
              )}

              {banners && Object.keys(banners).length > 0 ? (
                <>
                  <h5 className="mt-3">Banners</h5>
                  <ListGroup>
                    {Object.entries(banners).map(([type, text], index) => (
                      <ListGroup.Item key={index} className="text-monospace small">
                        <strong>{type}:</strong> {text}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              ) : (
                <Card.Text>No banners available.</Card.Text>
              )}

              {etherchannelSummary && etherchannelSummary.length > 0 ? (
                <>
                  <h5 className="mt-3">EtherChannel Summary</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Group</th>
                        <th>Port-channel</th>
                        <th>Type</th>
                        <th>Protocol</th>
                        <th>Ports</th>
                      </tr>
                    </thead>
                    <tbody>
                      {etherchannelSummary.map((ec, index) => (
                        <tr key={index}>
                          <td>{ec.group}</td>
                          <td>{ec.port_channel}</td>
                          <td>{ec.type}</td>
                          <td>{ec.protocol}</td>
                          <td>{ec.ports}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No EtherChannel summary available.</Card.Text>
              )}

              {interfacesTrunk && interfacesTrunk.length > 0 ? (
                <>
                  <h5 className="mt-3">Trunk Interfaces</h5>
                  <Table striped bordered hover size="sm">
                    <thead>
                      <tr>
                        <th>Interface</th>
                        <th>Mode</th>
                        <th>Encapsulation</th>
                        <th>Status</th>
                        <th>Native VLAN</th>
                      </tr>
                    </thead>
                    <tbody>
                      {interfacesTrunk.map((trunk, index) => (
                        <tr key={index}>
                          <td>{trunk.interface}</td>
                          <td>{trunk.mode}</td>
                          <td>{trunk.encapsulation}</td>
                          <td>{trunk.status}</td>
                          <td>{trunk.native_vlan}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </>
              ) : (
                <Card.Text>No trunk interfaces available.</Card.Text>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default DeviceDetailPage;
