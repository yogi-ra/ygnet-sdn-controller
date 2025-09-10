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
  Toast,
} from 'react-bootstrap';
import { useAssignPortToVlan, useChangeVlanName, useCreateVlan } from '../api/vlans';

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

/**
 * VLAN Configuration Component
 * 
 * This component displays VLAN information and allows configuration of VLANs and interfaces.
 * It receives interface data from its parent component to avoid duplicate API calls.
 */
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
  const [vlanNameEdits, setVlanNameEdits] = useState<{ [key: string]: string }>({});
  const [newVlanId, setNewVlanId] = useState<string>('');
  const [newVlanName, setNewVlanName] = useState<string>('');
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastVariant, setToastVariant] = useState<'success' | 'danger'>('success');
  
  const assignPortToVlan = useAssignPortToVlan(deviceId);
  const changeVlanName = useChangeVlanName(deviceId);
  const createVlan = useCreateVlan(deviceId);

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
      setToastMessage(`Successfully assigned port ${port} to VLAN ${vlanId}`);
      setToastVariant('success');
      setShowToast(true);
    } catch (err: any) {
      console.error("Error assigning port to VLAN:", err);
      setToastMessage(`Error assigning port to VLAN: ${err.message || "Unknown error"}`);
      setToastVariant('danger');
      setShowToast(true);
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

  const handleVlanNameChange = (vlanId: string, newName: string) => {
    setVlanNameEdits(prev => {
      // If the new name is empty, we still want to update the state
      // This allows users to clear the field completely
      return {
        ...prev,
        [vlanId]: newName
      };
    });
  };

  const handleSaveVlanName = async (vlanId: string) => {
    const newName = vlanNameEdits[vlanId];
    if (!deviceId || newName === undefined) return; // Allow empty string but not undefined

    try {
      await changeVlanName.mutateAsync({ vlanId, newName });
      // Clear the edit field after successful save
      setVlanNameEdits(prev => {
        const newState = { ...prev };
        delete newState[vlanId];
        return newState;
      });
      setToastMessage(`Successfully changed VLAN ${vlanId} name to ${newName || "(empty)"}`);
      setToastVariant('success');
      setShowToast(true);
    } catch (err: any) {
      console.error("Error changing VLAN name:", err);
      setToastMessage(`Error changing VLAN name: ${err.message || "Unknown error"}`);
      setToastVariant('danger');
      setShowToast(true);
    }
  };

  const handleCreateVlan = async () => {
    if (!deviceId || !newVlanId) return;

    try {
      const vlanId = parseInt(newVlanId);
      if (isNaN(vlanId)) {
        throw new Error("VLAN ID must be a number");
      }
      
      await createVlan.mutateAsync({ vlan_id: vlanId, name: newVlanName || undefined });
      setNewVlanId('');
      setNewVlanName('');
      setToastMessage(`Successfully created VLAN ${vlanId}${newVlanName ? ` with name ${newVlanName}` : ''}`);
      setToastVariant('success');
      setShowToast(true);
    } catch (err: any) {
      console.error("Error creating VLAN:", err);
      setToastMessage(`Error creating VLAN: ${err.message || "Unknown error"}`);
      setToastVariant('danger');
      setShowToast(true);
    }
  };

  const isLoading = vlanLoading || interfacesLoading;
  const error = vlanError || interfacesError;

  return (
    <Card>
      <Card.Body>
        <Card.Title as="h2">VLAN Configuration</Card.Title>
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
            <Card className="mb-4">
              <Card.Body>
                <Card.Title as="h3">Create New VLAN</Card.Title>
                <Form>
                  <Row>
                    <Col md={3}>
                      <Form.Group controlId="new-vlan-id">
                        <Form.Label>VLAN ID</Form.Label>
                        <Form.Control
                          type="text"
                          placeholder="Enter VLAN ID"
                          value={newVlanId}
                          onChange={(e) => setNewVlanId(e.target.value)}
                          disabled={!deviceReachable}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={4}>
                      <Form.Group controlId="new-vlan-name">
                        <Form.Label>VLAN Name (Optional)</Form.Label>
                        <Form.Control
                          type="text"
                          placeholder="Enter VLAN Name"
                          value={newVlanName}
                          onChange={(e) => setNewVlanName(e.target.value)}
                          disabled={!deviceReachable}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={2} className="d-flex align-items-end">
                      <Button
                        variant="primary"
                        onClick={handleCreateVlan}
                        disabled={!newVlanId || !deviceReachable}
                      >
                        Create VLAN
                      </Button>
                    </Col>
                  </Row>
                </Form>
              </Card.Body>
            </Card>

            <Card>
              <Card.Body>
                <Card.Title as="h3">VLAN Information</Card.Title>
                <h4>Existing VLANs</h4>
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
                      {vlanInfo.map((vlan: any, index: number) => {
                        const vlanId = vlan.vlan_id || vlan.id || "N/A";
                        const currentName = vlan.vlan_name || "N/A";
                        const isEditing = vlanNameEdits.hasOwnProperty(vlanId);
                        const editedName = vlanNameEdits[vlanId] || currentName;

                        return (
                          <tr key={index}>
                            <td>{vlanId}</td>
                            <td>
                              {isEditing ? (
                                <InputGroup>
                                  <Form.Control
                                    type="text"
                                    size="sm"
                                    value={editedName}
                                    onChange={(e) => handleVlanNameChange(vlanId, e.target.value)}
                                    disabled={!deviceReachable}
                                  />
                                  <Button
                                    size="sm"
                                    variant="success"
                                    onClick={() => handleSaveVlanName(vlanId)}
                                    disabled={!deviceReachable}
                                  >
                                    Save
                                  </Button>
                                </InputGroup>
                              ) : (
                                <div>
                                  {currentName}
                                  <Button
                                    size="sm"
                                    variant="outline-primary"
                                    className="ms-2"
                                    onClick={() => handleVlanNameChange(vlanId, currentName)}
                                    disabled={!deviceReachable}
                                  >
                                    Edit
                                  </Button>
                                </div>
                              )}
                            </td>
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
                              <Form.Group controlId={`vlan-${vlanId}-port`}>
                                <InputGroup>
                                  <Form.Select
                                    aria-label="Select port"
                                    size="sm"
                                    value={selectedPorts[vlanId] || ''}
                                    onChange={(e) => handlePortSelection(vlanId, e.target.value)}
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
                                    onClick={() => handleAssignPort(vlanId)}
                                    disabled={!selectedPorts[vlanId] || !deviceReachable}
                                  >
                                    +
                                  </Button>
                                </InputGroup>
                              </Form.Group>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </Table>
                ) : (
                  <Alert variant="info">No VLAN information available.</Alert>
                )}

                <h4 className="mt-4">Interface VLAN Configuration</h4>
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
              </Card.Body>
            </Card>
            
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
          </>
        )}
      </Card.Body>
    </Card>
  );
};

export default VlanConfiguration;