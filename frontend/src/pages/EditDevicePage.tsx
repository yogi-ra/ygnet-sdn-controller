import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Container, Card, Row, Col, Alert, Spinner } from "react-bootstrap";
import { useAuth } from "../hooks/useAuth";
import DeviceForm from "../components/DeviceForm";

interface Device {
  id: string;
  name: string;
  device_type: string;
  ip_address: string;
  port: number;
  username: string;
}

const EditDevicePage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();
  const [device, setDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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
          throw new Error(`Failed to fetch device details: ${response.statusText}`);
        }

        const data: Device = await response.json();
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
      const response = await fetch(`/api/devices/${id}`, {
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
