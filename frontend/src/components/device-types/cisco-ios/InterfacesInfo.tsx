import React, { useState, useEffect } from 'react';
import { Card, Table, Alert, Button } from 'react-bootstrap';
import { useTaskPolling } from '../../../hooks/useTaskPolling';
import { fetchInterfacesBrief, setInterfaceState } from '../../../api/deviceApi';
import LoadingStateDisplay from '../../LoadingStateDisplay';

interface InterfacesInfoProps {
  deviceId: string;
  token: string | null;
  isReachable: boolean;
}

// Helper function to determine if interface is administratively up
const isInterfaceAdminUp = (status: string) => {
  return !status?.toLowerCase().includes("administratively down");
};

const InterfacesInfo: React.FC<InterfacesInfoProps> = ({ deviceId, token, isReachable }) => {
  // State for storing task ID
  const [interfacesTaskId, setInterfacesTaskId] = useState<string | null>(null);
  
  // Fetch interfaces brief with task polling
  useEffect(() => {
    if (deviceId && token && isReachable) {
      setInterfacesTaskId(null); // Reset task ID before new request
      fetchInterfacesBrief(deviceId, token)
        .then(res => {
          if (res && res.task_id) {
            setInterfacesTaskId(res.task_id);
          }
        })
        .catch(err => {
          console.error("Error starting interfaces fetch task:", err);
          setInterfacesTaskId(null);
        });
    }
  }, [deviceId, token, isReachable]);
  
  const { taskStatus: interfacesTask, loading: interfacesLoading } = useTaskPolling(interfacesTaskId, {
    interval: 250,
  });
  
  // State for interface toggling
  const [togglingInterfaces, setTogglingInterfaces] = useState<{ [key: string]: boolean }>({});
  
  // Check for errors
  const hasError = interfacesTask?.status === 'FAILURE';
  
  // Loading state based on task status
  const isLoading = interfacesLoading || (interfacesTask?.status === 'PENDING' || interfacesTask?.status === 'PROCESSING');
  
  // Extract data when available
  const interfacesData = interfacesTask?.status === 'SUCCESS' ? interfacesTask.result : null;
  
  // Handle interface toggle
  const handleToggleInterface = async (interfaceName: string, currentState: string) => {
    if (!token) return;
    
    // Set loading state for this interface
    setTogglingInterfaces(prev => ({ ...prev, [interfaceName]: true }));
    
    // Toggle based on administrative state, not operational state
    const newState = !isInterfaceAdminUp(currentState);
    
    try {
      const response = await setInterfaceState(deviceId, interfaceName, newState, token);
      
      // Show success message or handle as needed
      console.log(`Successfully ${newState ? 'enabled' : 'disabled'} interface ${interfaceName}`);
    } catch (err: any) {
      console.error("Error toggling interface:", err);
    } finally {
      // Reset loading state for this interface
      setTogglingInterfaces(prev => {
        const newState = { ...prev };
        delete newState[interfaceName];
        return newState;
      });
    }
  };

  return (
    <Card>
      <Card.Body>
        <Card.Title as="h2">Interfaces</Card.Title>
        {hasError ? (
          <Alert variant="danger">
            Error fetching interfaces information. Please try again later.
          </Alert>
        ) : isLoading ? (
          <LoadingStateDisplay message="Fetching interface information..." />
        ) : interfacesData && interfacesData.length > 0 ? (
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
              {interfacesData.map((iface: any, index: number) => (
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
                      disabled={!isReachable || togglingInterfaces[iface.interface || iface.intf || ""]}
                    >
                      {togglingInterfaces[iface.interface || iface.intf || ""] ? (
                        <>
                          <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
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
  );
};

export default InterfacesInfo;