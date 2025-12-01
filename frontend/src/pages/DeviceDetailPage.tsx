import React, { useEffect } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../hooks/useAuth";
import { Container, Spinner, Alert } from "react-bootstrap";
import OfflineBanner from "../components/OfflineBanner";
import CiscoIosRouterDetailPage from "./device-types/CiscoIosRouterDetailPage";
import CiscoIosSwitchDetailPage from "./device-types/CiscoIosSwitchDetailPage";
import { API_BASE_URL } from "../api";

const DeviceDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  // Get device data passed from the device list page
  const deviceData = location.state?.device;

  // Check if device is explicitly marked as offline from the list navigation
  const isDeviceOfflineFromList = deviceData && deviceData.is_reachable === false;

  // If we don't have device data, fetch it
  const { data: device, isLoading, error, refetch } = useQuery<any, Error>({
    queryKey: ["deviceDetail", id],
    queryFn: async () => {
      if (!token || !id) {
        throw new Error("Missing token or device ID");
      }

      const response = await fetch(`${API_BASE_URL}/devices/${id}`, {
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

      return response.json();
    },
    enabled: !!id && !!token && !isDeviceOfflineFromList,
    initialData: deviceData,
  });

  // Continuously check device reachability even when it's offline
  const { data: isReachable } = useQuery<boolean, Error>({
    queryKey: ["deviceReachabilityCheck", id],
    queryFn: async () => {
      if (!token || !id) {
        throw new Error("Missing token or device ID");
      }

      const response = await fetch(`${API_BASE_URL}/devices/${id}/check-reachability`, {
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
        return false; // Treat any error as unreachable
      }

      return response.json();
    },
    enabled: !!id && !!token && (isDeviceOfflineFromList || (device && device.is_reachable === false)),
    refetchInterval: 5000, // Check every 5 seconds
    refetchIntervalInBackground: true, // Continue checking even when tab is not active
  });

  // When device becomes reachable, refetch device details
  useEffect(() => {
    if (isReachable) {
      refetch();
    }
  }, [isReachable, refetch]);

  // If the device is offline and we got this information from the list, display a banner
  // but continue checking for reachability
  if (isDeviceOfflineFromList) {
    if (isReachable) {
      // Device is now reachable, show the device details
      if (isLoading) {
        return (
          <Container fluid className="mt-4 text-center">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
            <p>Loading device details...</p>
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
      switch (deviceData.device_type) {
        case "cisco_ios_router":
          return <CiscoIosRouterDetailPage device={deviceData} />;
        case "cisco_ios_switch":
          return <CiscoIosSwitchDetailPage device={deviceData} />;
        default:
          // For unsupported device types, show a generic message
          return (
            <Container fluid className="mt-4">
              <Alert variant="warning">
                <Alert.Heading>Device Type Not Supported</Alert.Heading>
                <p>
                  The device type "{deviceData.device_type}" is not currently supported with a specific view.
                  Please contact the development team to request support for this device type.
                </p>
              </Alert>
            </Container>
          );
      }
    }
    
    return (
      <Container fluid className="mt-4">
        <OfflineBanner deviceName={deviceData?.name} />
        <div className="text-center mt-3">
          <small className="text-muted">
            Checking device reachability every 5 seconds...
          </small>
        </div>
      </Container>
    );
  }

  // Check if device is offline based on fetched data
  const isDeviceOffline = device && device.is_reachable === false;

  if (isDeviceOffline) {
    if (isReachable) {
      // Device is now reachable, show the device details
      if (isLoading) {
        return (
          <Container fluid className="mt-4 text-center">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
            <p>Loading device details...</p>
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
      switch (device.device_type) {
        case "cisco_ios_router":
          return <CiscoIosRouterDetailPage device={device} />;
        case "cisco_ios_switch":
          return <CiscoIosSwitchDetailPage device={device} />;
        default:
          // For unsupported device types, show a generic message
          return (
            <Container fluid className="mt-4">
              <Alert variant="warning">
                <Alert.Heading>Device Type Not Supported</Alert.Heading>
                <p>
                  The device type "{device.device_type}" is not currently supported with a specific view.
                  Please contact the development team to request support for this device type.
                </p>
              </Alert>
            </Container>
          );
      }
    }
    
    return (
      <Container fluid className="mt-4">
        <OfflineBanner deviceName={device?.name} />
        <div className="text-center mt-3">
          <small className="text-muted">
            Checking device reachability every 5 seconds...
          </small>
        </div>
      </Container>
    );
  }

  if (isLoading) {
    return (
      <Container fluid className="mt-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p>Loading device details...</p>
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

  // Render the appropriate component based on device type, passing device data
  switch (device.device_type) {
    case "cisco_ios_router":
      return <CiscoIosRouterDetailPage device={device} />;
    case "cisco_ios_switch":
      return <CiscoIosSwitchDetailPage device={device} />;
    default:
      // For unsupported device types, show a generic message
      return (
        <Container fluid className="mt-4">
          <Alert variant="warning">
            <Alert.Heading>Device Type Not Supported</Alert.Heading>
            <p>
              The device type "{device.device_type}" is not currently supported with a specific view.
              Please contact the development team to request support for this device type.
            </p>
          </Alert>
        </Container>
      );
  }
};

export default DeviceDetailPage;