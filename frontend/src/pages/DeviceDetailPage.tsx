import React, { useState, useMemo, lazy, Suspense, useCallback } from "react";
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
  Tabs,
  Tab,
} from "react-bootstrap";
import { useAuth } from "../hooks/useAuth";
import { useDeviceDetails } from "../hooks/useDeviceDetails";
import type { HeaderFieldSchema, ViewFeatureSchema, ActionFeatureSchema } from "../types/featureTypes";

import { FeatureStateProvider } from "../context/FeatureStateContext";

const LazyFeatureGroupTab = lazy(() => import("../components/FeatureGroupTab"));

const DeviceDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const { viewFeatures, actionFeatures, headerFields, loading, errors, isReachable } = useDeviceDetails(id);

  const [command, setCommand] = useState("");
  const [isConfigCommand, setIsConfigCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);
  const [deviceLevel, setDeviceLevel] = useState<string | null>(null);
  const [executingCommand, setExecutingCommand] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);

  const [clearingCache, setClearingCache] = useState(false);
  const [cacheClearSuccess, setCacheClearSuccess] = useState<string | null>(null);
  const [cacheClearError, setCacheClearError] = useState<string | null>(null);

  const [key, setKey] = useState("general"); // Default to 'general' tab

  const getHeaderFieldValue = useCallback((name: string) => {
    return headerFields.find(field => field.name === name)?.value;
  }, [headerFields]);

  const deviceName = getHeaderFieldValue("device_name") || getHeaderFieldValue("hostname") || "N/A";
  const ipAddress = getHeaderFieldValue("ip_address") || "N/A";
  const deviceType = getHeaderFieldValue("device_type") || "N/A";

  const groupedViewFeatures = useMemo(() => {
    const groups: { [key: string]: ViewFeatureSchema[] } = {};
    if (!viewFeatures || !Array.isArray(viewFeatures)) return {};

    viewFeatures.forEach((feature) => {
      const groupName = feature.group || "Other";
      if (!groups[groupName]) {
        groups[groupName] = [];
      }
      groups[groupName].push(feature);
    });

    const sortedGroupNames = Object.keys(groups).sort((a, b) => {
      if (a === "Other") return 1;
      if (b === "Other") return -1;
      return a.localeCompare(b);
    });

    const sortedGroups: { [key: string]: ViewFeatureSchema[] } = {};
    sortedGroupNames.forEach(name => {
      sortedGroups[name] = groups[name].sort((a, b) => (a.order || 0) - (b.order || 0));
    });

    return sortedGroups;
  }, [viewFeatures]);

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

  if (errors.primary) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="danger">
          Error: {errors.primary}. Please try again later.
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
                {deviceName} ({ipAddress})
                <Badge bg={isReachable ? "success" : "danger"} className="ms-2">
                  {isReachable ? "Online" : "Offline"}
                </Badge>
              </Card.Title>
              <Card.Subtitle className="mb-2 text-muted">
                {deviceType}
              </Card.Subtitle>
              {headerFields.filter(field => 
                !["hostname", "ip_address", "device_type", "is_reachable"].includes(field.name)
              ).map(field => (
                <Card.Text key={field.name}>
                  <strong>{field.label}:</strong> {field.value || "N/A"}
                </Card.Text>
              ))}
              <Button variant="secondary" onClick={() => navigate(-1)}>
                Back to Devices
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <FeatureStateProvider features={[...viewFeatures, ...actionFeatures]}>
        <Tabs
          id="device-detail-tabs"
          activeKey={key}
          onSelect={(k) => setKey(k!)}
          className="mb-3 mt-4"
          unmountOnExit={true}
        >
          {Object.entries(groupedViewFeatures).map(([groupName, groupFeatures]) => (
            <Tab eventKey={groupName} title={groupName} key={groupName}>
              <Row className="mt-3">
                <Col>
                  {loading ? (
                    <Alert variant="info">Loading features...</Alert>
                  ) : errors.primary ? (
                    <Alert variant="danger">Error loading features: {errors.primary}</Alert>
                  ) : (
                    <Suspense fallback={<Spinner animation="border" size="sm" />}>
                      <LazyFeatureGroupTab features={groupFeatures} deviceId={id!} />
                    </Suspense>
                  )}
                </Col>
              </Row>
            </Tab>
          ))}
          <Tab eventKey="configuration" title="Configuration">
            <Row className="mt-3">
              <Col>
                {loading ? (
                  <Alert variant="info">Loading features...</Alert>
                ) : errors.primary ? (
                  <Alert variant="danger">Error loading features: {errors.primary}</Alert>
                ) : (
                  <Suspense fallback={<Spinner animation="border" size="sm" />}>
                    <LazyFeatureGroupTab features={actionFeatures} deviceId={id!} />
                  </Suspense>
                )}
              </Col>
            </Row>
          </Tab>
          <Tab eventKey="tools" title="Tools">
            <Row className="mt-3">
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
        </Tabs>
      </FeatureStateProvider>
    </Container>
  );
};

export default DeviceDetailPage;