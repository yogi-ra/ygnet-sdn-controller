import { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { Container, Card, Row, Col, Alert, Spinner } from "react-bootstrap";
import { useAuth } from "../hooks/useAuth";
import DeviceForm from "../components/DeviceForm";
import { API_BASE_URL } from "../api";

interface Device {
  id: number; // Changed from string to number to match backend schema
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
}

const EditDevicePage = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const [device, setDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(false); // No longer need to fetch from server
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    // Get device data from location state (passed from DeviceListPage)
    const locationState = location.state as { device?: Device };
    
    if (locationState?.device && locationState.device.id.toString() === id) {
      // Use device data passed from DeviceListPage
      setDevice(locationState.device);
    } else {
      // Fallback: If no device data in location state, show error
      setError("Device data not available. Please go back and try again.");
    }
  }, [id, location.state]);

  const handleUpdateDevice = async (formData: any) => {
    setError(null);
    setSuccess(null);

    if (!token) {
      setError("No authentication token found. Please log in.");
      logout();
      navigate("/login");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/devices/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.status === 401) {
        setError("Session expired or unauthorized. Please log in again.");
        logout();
        navigate("/login");
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update device");
      }

      setSuccess("Device updated successfully!");
      navigate("/devices"); // Navigate back to device list after successful update

    } catch (err: any) {
      console.error("Error updating device:", err);
      setError(err.message || "Failed to update device. Please check your input.");
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

  if (error && !device) { // Only show error if device couldn't be loaded at all
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
      <Row className="justify-content-md-center">
        <Col md={8}>
          <Card>
            <Card.Body>
              <Card.Title as="h1" className="mb-4">Edit Device: {device.name}</Card.Title>
              {error && <Alert variant="danger">{error}</Alert>}
              {success && <Alert variant="success">{success}</Alert>}
              <DeviceForm initialData={device} onSubmit={handleUpdateDevice} isEditMode={true} />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default EditDevicePage;