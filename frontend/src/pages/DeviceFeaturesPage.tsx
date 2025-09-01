import React from "react";
import { Container, Alert } from "react-bootstrap";
import { useParams } from "react-router-dom";
import { useDeviceFeatures } from "../hooks/useDeviceFeatures";
import FeatureRenderer from "../components/FeatureRenderer";

const DeviceFeaturesPage = () => {
  const { deviceId } = useParams<{ deviceId: string }>();
  const { features, isLoading, isError, error } = useDeviceFeatures(deviceId);

  if (isLoading) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="info">Loading features...</Alert>
      </Container>
    );
  }

  if (isError) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="danger">Error loading features: {error?.message}</Alert>
      </Container>
    );
  }

  if (!features || features.length === 0) {
    return (
      <Container fluid className="mt-4">
        <Alert variant="info">No features available for this device.</Alert>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <h1 className="mb-4">Device Features</h1>
      <div className="d-flex flex-wrap">
        {features.map((feature) => (
            <FeatureRenderer key={feature.name} feature={feature} deviceId={deviceId} />
          ))}
      </div>
    </Container>
  );
};

export default DeviceFeaturesPage;