import React from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import { Container, Spinner, Alert } from "react-bootstrap";
import CiscoIosRouterDetailPage from "./device-types/CiscoIosRouterDetailPage";
import CiscoIosSwitchDetailPage from "./device-types/CiscoIosSwitchDetailPage";

// A simple component to fetch device type
const useDeviceType = (deviceId: string | undefined) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  return useQuery<string, Error>({
    queryKey: ["deviceType", deviceId],
    queryFn: async () => {
      if (!token || !deviceId) {
        throw new Error("Missing token or device ID");
      }

      const response = await fetch(`/api/devices/${deviceId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        logout();
        navigate("/login");
        throw new Error("Unauthorized");
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch device: ${response.statusText}`);
      }

      const data = await response.json();
      return data.device_type;
    },
    enabled: !!deviceId && !!token,
  });
};

const DeviceDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const { data: deviceType, isLoading, error } = useDeviceType(id);

  if (isLoading) {
    return (
      <Container fluid className="mt-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p>Loading device type...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="danger">
          Error: {error.message}. Please try again later.
        </Alert>
      </Container>
    );
  }

  // Render the appropriate component based on device type
  switch (deviceType) {
    case "cisco_ios_router":
      return <CiscoIosRouterDetailPage />;
    case "cisco_ios_switch":
      return <CiscoIosSwitchDetailPage />;
    default:
      // For unsupported device types, show a generic message
      return (
        <Container fluid className="mt-4">
          <Alert variant="warning">
            <Alert.Heading>Device Type Not Supported</Alert.Heading>
            <p>
              The device type "{deviceType}" is not currently supported with a specific view.
              Please contact the development team to request support for this device type.
            </p>
          </Alert>
        </Container>
      );
  }
};

export default DeviceDetailPage;