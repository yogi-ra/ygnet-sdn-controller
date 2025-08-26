import { Container, Table, Button, Alert } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface Device {
  id: string;
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
  is_reachable?: boolean; // Add is_reachable to the interface
}

import { useState } from "react";
const DeviceListPage = () => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const fetchDevices = async (): Promise<Device[]> => {
    if (!token) {
      logout();
      navigate("/login");
      throw new Error("No authentication token found. Please log in.");
    }

    const response = await fetch("/api/devices/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 401) {
      logout();
      navigate("/login");
      throw new Error("Session expired or unauthorized. Please log in again.");
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch devices: ${response.statusText}`);
    }

    return response.json();
  };

  const {
    data: devices,
    isLoading,
    isError,
    error,
  } = useQuery<Device[], Error>({
    queryKey: ["devices"],
    queryFn: fetchDevices,
    refetchInterval: 5000, // Refetch every 5 seconds
    onError: (err) => {
      console.error("Error fetching devices:", err);
      if (err.message.includes("Authentication failed") || err.message.includes("Session expired")) {
        logout();
        navigate("/login");
      }
    },
  });

  const handleAddDevice = () => {
    navigate("/devices/add");
  };

  const queryClient = useQueryClient();

  const deleteDeviceMutation = useMutation({
    mutationFn: async (deviceId: string) => {
      if (!token) {
        logout();
        navigate("/login");
        throw new Error("No authentication token found. Please log in.");
      }

      const response = await fetch(`/api/devices/${deviceId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Session expired or unauthorized. Please log in again.");
      }

      if (!response.ok) {
        throw new Error(`Failed to delete device: ${response.statusText}`);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      alert("Device deleted successfully!");
    },
    onError: (err: any) => {
      console.error("Error deleting device:", err);
      setDeleteError(err.message || "Failed to delete device. Please try again.");
      if (err.message.includes("Authentication failed") || err.message.includes("Session expired")) {
        logout();
        navigate("/login");
      }
    },
  });

  const handleDeleteDevice = (deviceId: string) => {
    if (window.confirm("Are you sure you want to delete this device?")) {
      deleteDeviceMutation.mutate(deviceId);
    }
  };

  return (
    <Container fluid className="mt-4">
      <h1 className="mb-4">Devices</h1>
      {deleteError && <Alert variant="danger">{deleteError}</Alert>}
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
