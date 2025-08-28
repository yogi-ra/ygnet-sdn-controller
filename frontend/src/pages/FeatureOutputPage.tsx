import { Container, Alert } from "react-bootstrap";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchFeature } from "../api";
import { useAuth } from "../hooks/useAuth";

const FeatureOutputPage = () => {
  const { deviceId, featureName } = useParams<{ deviceId: string; featureName: string }>();
  const { token } = useAuth();

  const { data, isLoading, isError, error } = useQuery(
    ["feature", deviceId, featureName],
    () => fetchFeature(deviceId!, featureName!, token),
    {
      enabled: !!deviceId && !!featureName && !!token,
    }
  );

  return (
    <Container fluid className="mt-4">
      <h1 className="mb-4">{featureName}</h1>
      {isLoading && <Alert variant="info">Loading...</Alert>}
      {isError && <Alert variant="danger">{error.message}</Alert>}
      {data && (
        <pre>
          <code>{JSON.stringify(data, null, 2)}</code>
        </pre>
      )}
    </Container>
  );
};

export default FeatureOutputPage;
