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
} from "react-bootstrap";
import { useAuth } from "../../hooks/useAuth";
import { useStaticDeviceDetails } from "../../hooks/useStaticDeviceDetails";

const CiscoIosRouterDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const { systemInfo, interfaces, isReachable, loading, errors } = useStaticDeviceDetails(id);

  const [command, setCommand] = useState("");
  const [isConfigCommand, setIsConfigCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);
  const [deviceLevel, setDeviceLevel] = useState<string | null>(null);
  const [executingCommand, setExecutingCommand] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);

  const [clearingCache, setClearingCache] = useState(false);
  const [cacheClearSuccess, setCacheClearSuccess] = useState<string | null>(null);
  const [cacheClearError, setCacheClearError] = useState<string | null>(null);

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
      "details",
      "system",
      "interfaces",
      "routing",
      "acls",
      "snmp",
      "logging",
      "ntp",
      "aaa",
      "active_users",
      "local_users",
      "clock",
      "lldp",
      "ip_arp",
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

  if (errors.system || errors.interfaces) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="danger">
          Error: {errors.system || errors.interfaces}. Please try again later.
        </Alert>
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
                {systemInfo?.hostname || "N/A"} ({systemInfo?.version || "N/A"})
                <Badge bg={isReachable ? "success" : "danger"} className="ms-2">
                  {isReachable ? "Online" : "Offline"}
                </Badge>
              </Card.Title>
              <Card.Subtitle className="mb-2 text-muted">
                Device ID: {id} (Cisco IOS Router)
              </Card.Subtitle>
              <Card.Text>
                <strong>Uptime:</strong> {systemInfo?.uptime || "N/A"}
              </Card.Text>
              <Card.Text>
                <strong>Clock:</strong> {systemInfo?.clock || "N/A"}
              </Card.Text>
              <Button variant="secondary" onClick={() => navigate(-1)}>
                Back to Devices
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Router-specific features */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title as="h2">Routing Information</Card.Title>
              <Alert variant="info">
                Routing information would be displayed here for Cisco IOS routers.
              </Alert>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title as="h2">Interfaces</Card.Title>
              {interfaces && interfaces.length > 0 ? (
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
                    {interfaces.map((iface, index) => (
                      <tr key={index}>
                        <td>{iface.interface}</td>
                        <td>{iface.ip_address || "N/A"}</td>
                        <td>{iface.status}</td>
                        <td>{iface.protocol}</td>
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
    </Container>
  );
};

export default CiscoIosRouterDetailPage;