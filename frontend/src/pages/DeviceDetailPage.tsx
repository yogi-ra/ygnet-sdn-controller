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

  useEffect(() => {
    const fetchDeviceDetails = async () => {
      if (!token) {
        setError("No authentication token found. Please log in.");
        logout();
        navigate("/login");
        return;
      }

      try {
        const response = await fetch(`/api/devices/${id}`, {
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
          throw new Error(
            `Failed to fetch device details: ${response.statusText}`,
          );
        }

        const data: DeviceDetail = await response.json();
        setDevice(data);
      } catch (err: any) {
        console.error("Error fetching device details:", err);
        setError(err.message || "Failed to load device details.");
      } finally {
        setLoading(false);
      }
    };

    fetchDeviceDetails();
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
            <Card.Body>
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
            <Card.Body>
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

      
    </Container>
  );
};

export default DeviceDetailPage;
