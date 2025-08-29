import { Container, Table, Button, Alert } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useDevices } from "../hooks/useDevices";
import { useConfig } from "../context/ConfigContext";
import { findDeviceTypeDisplayName } from "../utils/deviceTypes";

const DeviceListPage = () => {
  const navigate = useNavigate();
  const { devices, isLoading, isError, error, deleteDevice } = useDevices();
  const { supportedFeatures, deviceTypes } = useConfig();

  const handleAddDevice = () => {
    navigate("/devices/add");
  };

  const handleDeleteDevice = (deviceId: string) => {
    if (window.confirm("Are you sure you want to delete this device?")) {
      deleteDevice(deviceId, {
        onSuccess: () => {
          alert("Device deleted successfully!");
        },
        onError: (err: any) => {
          console.error("Error deleting device:", err);
          alert("Failed to delete device. Please try again.");
        },
      });
    }
  };

  return (
    <Container fluid className="mt-4">
      <h1 className="mb-4">Devices</h1>
      <Button variant="primary" onClick={handleAddDevice} className="mb-3">
        Add New Device
      </Button>
      {isLoading ? (
        <Alert variant="info">
          Loading devices...
        </Alert>
      ) : !devices || devices.length === 0 ? (
        <Alert variant="info">
          No devices found. Click "Add New Device" to add one.
        </Alert>
      ) : (
        <div className="table-responsive">
          <Table striped bordered hover className="shadow-sm">
            <thead>
              <tr>
                <th>Name</th>
                <th>Device Type</th>
                <th>IP Address</th>
                <th>Port</th>
                <th>Username</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(devices) && devices.map((device) => (
                <tr key={device.id}>
                  <td>{device.name}</td>
                  <td>{findDeviceTypeDisplayName(deviceTypes || [], device.device_type)}</td>
                  <td>{device.ip_address}</td>
                  <td>{device.port}</td>
                  <td>{device.username}</td>
                  <td>
                    {device.is_reachable === true ? (
                      <span style={{ color: 'green', fontWeight: 'bold' }}>Online</span>
                    ) : (
                      <span style={{ color: 'red', fontWeight: 'bold' }}>Offline</span>
                    )}
                  </td>
                  <td>
                    <Button
                      variant="info"
                      size="sm"
                      className="me-2"
                      onClick={() => navigate(`/devices/${device.id}`)}
                      disabled={device.is_reachable === false}
                      style={device.is_reachable === false ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
                      title={device.is_reachable === false ? "Device is offline" : "View device details"}
                    >
                      View
                    </Button>
                    <Button
                      variant="warning"
                      size="sm"
                      className="me-2"
                      onClick={() => navigate(`/devices/edit/${device.id}`, { state: { device: { ...device, id: Number(device.id) } } })}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDeleteDevice(device.id)}
                    >
                      Delete
                    </Button>
                    
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}
    </Container>
  );
};

export default DeviceListPage;