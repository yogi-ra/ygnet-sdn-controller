import { useState } from "react";
import { Container, Alert, Row, Col, Card } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import DeviceForm from "../components/DeviceForm";

const AddDevicePage = () => {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  const handleAddDevice = async (formData: any) => {
    setError(null);
    setSuccess(null);

    if (!token) {
      setError("No authentication token found. Please log in.");
      logout();
      navigate("/login");
      return;
    }

    try {
      const response = await fetch("/api/devices/", {
        method: "POST",
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
        throw new Error(errorData.detail || "Failed to add device");
      }

      setSuccess("Device added successfully!");
      navigate("/devices"); // Navigate back to device list after successful addition

    } catch (err: any) {
      console.error("Error adding device:", err);
      setError(err.message || "Failed to add device. Please check your input.");
    }
  };

  return (
    <Container fluid className="mt-4">
      <Row className="justify-content-md-center">
        <Col md={8}>
          <Card>
            <Card.Body>
              <Card.Title as="h1" className="mb-4">Add New Device</Card.Title>
              {error && <Alert variant="danger">{error}</Alert>}
              {success && <Alert variant="success">{success}</Alert>}
              <DeviceForm onSubmit={handleAddDevice} />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default AddDevicePage;