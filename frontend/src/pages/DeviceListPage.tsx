import { useEffect, useState } from "react";
import { Container, Table, Button, Alert } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

interface Device {
  id: string;
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
  is_reachable?: boolean; // Add is_reachable to the interface
}

const DeviceListPage = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDevices = async () => {
      setIsLoading(true); // Set loading to true when fetching starts
      if (!token) {
        setError("No authentication token found. Please log in.");
        logout();
        navigate("/login");
        setIsLoading(false); // Set loading to false if no token
        return;
      }

      try {
        const response = await fetch("/api/devices/", {
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
          throw new Error(`Failed to fetch devices: ${response.statusText}`);
        }

        const data: Device[] = await response.json();
        setDevices(data);
      } catch (err: any) {
        console.error("Error fetching devices:", err);
        if (err.message && err.message.includes("Could not validate credentials")) {
          setError("Authentication failed. Please log in again.");
          logout();
          navigate("/login");
        } else {
          setError("Failed to load devices. Please try again later.");
        }
      } finally {
        setIsLoading(false); // Always set loading to false when fetch completes
      }
    };

    fetchDevices();
  }, [token, navigate, logout]);

  const handleAddDevice = () => {
    navigate("/devices/add");
  };

  const handleDeleteDevice = async (deviceId: string) => {
    if (!window.confirm("Are you sure you want to delete this device?")) {
      return;
    }

    if (!token) {
      setError("No authentication token found. Please log in.");
      logout();
      navigate("/login");
      return;
    }

    try {
      const response = await fetch(`/api/devices/${deviceId}`, {
        method: "DELETE",
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
        throw new Error(`Failed to delete device: ${response.statusText}`);
      }

      setDevices(devices.filter((device) => device.id !== deviceId));
      alert("Device deleted successfully!");
    } catch (err: any) {
      console.error("Error deleting device:", err);
      if (err.message && err.message.includes("Could not validate credentials")) {
        setError("Authentication failed. Please log in again.");
        logout();
        navigate("/login");
      } else {
        setError(err.message || "Failed to delete device. Please try again.");
      }
    }
  };

  return (
    <Container fluid className="mt-4">
      <h1 className="mb-4">Devices</h1>
      {error && <Alert variant="danger">{error}</Alert>}
      <Button variant="primary" onClick={handleAddDevice} className="mb-3">
        Add New Device
      </Button>
      {isLoading ? (
        <Alert variant="info">
          Loading devices...
        </Alert>
      ) : devices.length === 0 ? (
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
                <th>Status</th> {/* New Status Header */}
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((device) => (
                <tr key={device.id}>
                  <td>{device.name}</td>
                  <td>{device.device_type}</td>
                  <td>{device.ip_address}</td>
                  <td>{device.port}</td>
                  <td>{device.username}</td>
                  <td> {/* New Status Data */}
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
                    >
                      View
                    </Button>
                    <Button
                      variant="warning"
                      size="sm"
                      className="me-2"
                      onClick={() => navigate(`/devices/edit/${device.id}`)}
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
