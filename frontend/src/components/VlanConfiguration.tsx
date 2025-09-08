import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Alert,
  Spinner,
  Form,
  Button,
  Row,
  Col,
  InputGroup,
} from 'react-bootstrap';
import { useAssignPortToVlan } from '../api/vlans';

interface InterfaceConfig {
  mode: 'access' | 'trunk';
  accessVlan?: string;
  allowedVlans?: string;
  nativeVlan?: string;
}

interface VlanConfigurationProps {
  deviceId: string | undefined;
  vlanInfo: any[];
  vlanLoading: boolean;
  vlanError: Error | null;
  interfaces: any[];
  interfacesLoading: boolean;
  interfacesError: Error | null;
  deviceReachable: boolean;
}

const VlanConfiguration: React.FC<VlanConfigurationProps> = ({
  deviceId,
  vlanInfo,
  vlanLoading,
  vlanError,
  interfaces,
  interfacesLoading,
  interfacesError,
  deviceReachable,
}) => {
  const [selectedPorts, setSelectedPorts] = useState<{ [key: string]: string }>({});
  const [interfaceConfigs, setInterfaceConfigs] = useState<{ [key: string]: InterfaceConfig }>({});
  const assignPortToVlan = useAssignPortToVlan(deviceId);

  useEffect(() => {
    if (interfaces && interfaces.length > 0) {
      const initialConfigs: { [key: string]: InterfaceConfig } = {};
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

  const handlePortSelection = (vlanId: string, port: string) => {
    setSelectedPorts(prev => ({
      ...prev,
      [vlanId]: port
    }));
  };

  const handleAssignPort = async (vlanId: string) => {
    const port = selectedPorts[vlanId];
    if (!deviceId || !port) return;

    try {
      await assignPortToVlan.mutateAsync({ vlanId, port });
    } catch (err: any) {
      console.error("Error assigning port to VLAN:", err);
      alert(`Error assigning port to VLAN: ${err.message || "Unknown error"}`);
    }
  };

  const handleInterfaceConfigChange = (ifaceName: string, field: keyof InterfaceConfig, value: string) => {
    setInterfaceConfigs(prev => ({
      ...prev,
      [ifaceName]: {
        ...prev[ifaceName],
        [field]: value,
      },
    }));
  };

  const isLoading = vlanLoading || interfacesLoading;
  const error = vlanError || interfacesError;

  return (
    <Card>
      <Card.Body>
        <Card.Title as="h2">VLAN Information</Card.Title>
        {error ? (
          <Alert variant="danger">
            Error: {error.message}. Please try again later.
          </Alert>
        ) : isLoading ? (
          <div className="text-center">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
          </div>
        ) : (
          <>
            <h3>Existing VLANs</h3>
            {vlanInfo && vlanInfo.length > 0 ? (
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>VLAN ID</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Ports</th>
                    <th>Assign Port</th>
                  </tr>
                </thead>
                <tbody>
                  {vlanInfo.map((vlan: any, index: number) => (
                    <tr key={index}>
                      <td>{vlan.vlan_id || vlan.id || "N/A"}</td>
                      <td>{vlan.vlan_name || "N/A"}</td>
                      <td>{vlan.status || "N/A"}</td>
                      <td>
                        {vlan.ports
                          ? Array.isArray(vlan.ports)
                            ? vlan.ports.join(', ')
                            : typeof vlan.ports === 'string'
                              ? vlan.ports.split(' ').join(', ')
                              : vlan.ports
                          : vlan.interfaces
                            ? Array.isArray(vlan.interfaces)
                              ? vlan.interfaces.join(', ')
                              : typeof vlan.interfaces === 'string'
                                ? vlan.interfaces.split(' ').join(', ')
                                : vlan.interfaces
                            : "N/A"}
                      </td>
                      <td>
                        <Form.Group controlId={`vlan-${vlan.vlan_id}-port`}>
                          <InputGroup>
                            <Form.Select
                              aria-label="Select port"
                              size="sm"
                              value={selectedPorts[vlan.vlan_id] || ''}
                              onChange={(e) => handlePortSelection(vlan.vlan_id, e.target.value)}
                            >
                              <option value="">Select Port</option>
                              {interfaces?.map((iface: any, i: number) => (
                                <option key={i} value={iface.interface || iface.intf}>
                                  {iface.interface || iface.intf}
                                </option>
                              ))}
                            </Form.Select>
                            <Button
                              size="sm"
                              variant="primary"
                              onClick={() => handleAssignPort(vlan.vlan_id)}
                              disabled={!selectedPorts[vlan.vlan_id] || !deviceReachable}
                            >
                              +
                            </Button>
                          </InputGroup>
                        </Form.Group>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            ) : (
              <Alert variant="info">No VLAN information available.</Alert>
            )}

            <h3 className="mt-4">Interface VLAN Configuration</h3>
            {interfaces && interfaces.length > 0 ? (
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
                  {interfaces.map((iface: any, index: number) => {
                    const ifaceName = iface.interface || iface.intf;
                    const config = interfaceConfigs[ifaceName];
                    if (!config) return null; // Should not happen with useEffect initialization

                    return (
                      <tr key={index}>
                        <td>{ifaceName}</td>
                        <td>
                          <Form.Select
                            size="sm"
                            value={config.mode}
                            onChange={(e) =>
                              handleInterfaceConfigChange(ifaceName, 'mode', e.target.value as 'access' | 'trunk')
                            }
                            disabled={!deviceReachable}
                          >
                            <option value="access">Access</option>
                            <option value="trunk">Trunk</option>
                          </Form.Select>
                        </td>
                        <td>
                          {config.mode === 'access' ? (
                            <Form.Control
                              type="text"
                              size="sm"
                              placeholder="VLAN ID"
                              value={config.accessVlan}
                              onChange={(e) =>
                                handleInterfaceConfigChange(ifaceName, 'accessVlan', e.target.value)
                              }
                              disabled={!deviceReachable}
                            />
                          ) : (
                            <Form.Control
                              type="text"
                              size="sm"
                              placeholder="Allowed VLANs (e.g., 10,20,30-40)"
                              value={config.allowedVlans}
                              onChange={(e) =>
                                handleInterfaceConfigChange(ifaceName, 'allowedVlans', e.target.value)
                              }
                              disabled={!deviceReachable}
                            />
                          )}
                        </td>
                        <td>
                          {config.mode === 'trunk' && (
                            <Form.Control
                              type="text"
                              size="sm"
                              placeholder="Native VLAN ID"
                              value={config.nativeVlan}
                              onChange={(e) =>
                                handleInterfaceConfigChange(ifaceName, 'nativeVlan', e.target.value)
                              }
                              disabled={!deviceReachable}
                            />
                          )}
                        </td>
                        <td>
                          <Button size="sm" variant="success" disabled={!deviceReachable} /* Add onClick for apply */>
                            Apply
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
          </>
        )}
      </Card.Body>
    </Card>
  );
};

export default VlanConfiguration;
