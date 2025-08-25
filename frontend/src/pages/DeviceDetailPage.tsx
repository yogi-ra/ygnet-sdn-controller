import { useState } from "react";
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
} from "react-bootstrap";
import { useAuth } from "../hooks/useAuth";
import { useDeviceDetails } from "../hooks/useDeviceDetails";

const DeviceDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const { device, loading, errors } = useDeviceDetails(id);

  const [command, setCommand] = useState("");
  const [isConfigCommand, setIsConfigCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);
  const [deviceLevel, setDeviceLevel] = useState<string | null>(null);
  const [executingCommand, setExecutingCommand] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);

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

  const renderCard = (title: string, dataKey: keyof typeof device, render: (data: any) => JSX.Element) => (
    <Col md={6} className="mb-4">
      <Card>
        <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
          <Card.Title as="h2">{title}</Card.Title>
          {errors[dataKey] ? (
            <Alert variant="warning">Could not load {title.toLowerCase()}: {errors[dataKey]}</Alert>
          ) : device[dataKey] && (Array.isArray(device[dataKey]) ? (device[dataKey] as any[]).length > 0 : device[dataKey]) ? (
            render(device[dataKey])
          ) : (
            <Card.Text>No {title.toLowerCase()} information available.</Card.Text>
          )}
        </Card.Body>
      </Card>
    </Col>
  );

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
                <strong>Hostname:</strong> {errors.hostname ? <span className="text-danger">Error</span> : device.hostname || "N/A"}
                <br />
                <strong>Clock:</strong> {errors.clock ? <span className="text-danger">Error</span> : device.clock || "N/A"}
              </Card.Text>
              <Button variant="secondary" onClick={() => navigate(-1)}>
                Back to Devices
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        {renderCard("Interfaces", "interfaces", (data) => (
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

        <Col md={6} className="mb-4">
          <Card>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
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
                  {executingCommand ? <Spinner as="span" animation="border" size="sm" /> : "Execute"}
                </Button>
              </Form>
              {commandError && <Alert variant="danger" className="mt-3">{commandError}</Alert>}
              {commandOutput && (
                <div className="mt-3 p-3 bg-light rounded" style={{ whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
                  {deviceLevel && <><strong>Device Level:</strong> {deviceLevel}<br /></>}
                  <strong>Output:</strong><br />
                  {commandOutput}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        {renderCard("Active Users", "activeUsers", (data) => (
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
                  <td>{user.username}</td>
                  <td>{user.line}</td>
                  <td>{user.idle}</td>
                  <td>{user.location}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        ))}

        {renderCard("Local Users", "localUsers", (data) => (
          <ListGroup>
            {data.map((user: any, index: number) => (
              <ListGroup.Item key={index} className="d-flex justify-content-between align-items-center">
                <span className="text-monospace small">{user.line}</span>
                {user.privilege && <Badge bg="info">Privilege: {user.privilege}</Badge>}
              </ListGroup.Item>
            ))}
          </ListGroup>
        ))}
        
      </Row>
    </Container>
  );
};

export default DeviceDetailPage;
