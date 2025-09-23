import React from 'react';
import { Card, Table, Spinner, Alert } from 'react-bootstrap';
import { useTaskPolling } from '../../../hooks/useTaskPolling';
import { fetchSystemVersion, fetchSystemHostname, fetchSystemUptime, fetchSystemClock } from '../../../api/deviceApi';

interface SystemInfoProps {
  deviceId: string;
  token: string | null;
  isReachable: boolean;
}

const SystemInfo: React.FC<SystemInfoProps> = ({ deviceId, token, isReachable }) => {
  // Fetch version info with task polling
  const { taskResult: versionTask, loading: versionLoading } = useTaskPolling<{ hostname: string; version: string; uptime: string }>(
    fetchSystemVersion(deviceId, token).then(res => res.task_id),
    { interval: 250 }
  );
  
  // Fetch hostname info with task polling
  const { taskResult: hostnameTask, loading: hostnameLoading } = useTaskPolling<string>(
    fetchSystemHostname(deviceId, token).then(res => res.task_id),
    { interval: 250 }
  );
  
  // Fetch uptime info with task polling
  const { taskResult: uptimeTask, loading: uptimeLoading } = useTaskPolling<string>(
    fetchSystemUptime(deviceId, token).then(res => res.task_id),
    { interval: 250 }
  );
  
  // Fetch clock info with task polling
  const { taskResult: clockTask, loading: clockLoading } = useTaskPolling<string>(
    fetchSystemClock(deviceId, token).then(res => res.task_id),
    { interval: 250 }
  );

  // Check for errors
  const hasError = versionTask?.status === 'FAILURE' || 
                   hostnameTask?.status === 'FAILURE' || 
                   uptimeTask?.status === 'FAILURE' || 
                   clockTask?.status === 'FAILURE';

  // Loading state
  const isLoading = versionLoading || hostnameLoading || uptimeLoading || clockLoading ||
                   versionTask?.status === 'PENDING' || versionTask?.status === 'PROCESSING' ||
                   hostnameTask?.status === 'PENDING' || hostnameTask?.status === 'PROCESSING' ||
                   uptimeTask?.status === 'PENDING' || uptimeTask?.status === 'PROCESSING' ||
                   clockTask?.status === 'PENDING' || clockTask?.status === 'PROCESSING';

  // Extract data when available
  const versionData = versionTask?.status === 'SUCCESS' ? versionTask.result : null;
  const hostnameData = hostnameTask?.status === 'SUCCESS' ? hostnameTask.result : null;
  const uptimeData = uptimeTask?.status === 'SUCCESS' ? uptimeTask.result : null;
  const clockData = clockTask?.status === 'SUCCESS' ? clockTask.result : null;

  return (
    <Card>
      <Card.Body>
        <Card.Title as="h2">System Information</Card.Title>
        {hasError ? (
          <Alert variant="danger">
            Error fetching system information. Please try again later.
          </Alert>
        ) : isLoading ? (
          <div className="text-center">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
          </div>
        ) : versionData || hostnameData || uptimeData || clockData ? (
          <Table striped bordered hover>
            <tbody>
              <tr>
                <td><strong>Hostname:</strong></td>
                <td>{hostnameData || versionData?.hostname || "N/A"}</td>
              </tr>
              <tr>
                <td><strong>Version:</strong></td>
                <td>{versionData?.version || "N/A"}</td>
              </tr>
              <tr>
                <td><strong>Uptime:</strong></td>
                <td>{uptimeData || versionData?.uptime || "N/A"}</td>
              </tr>
              <tr>
                <td><strong>Clock:</strong></td>
                <td>{clockData || "N/A"}</td>
              </tr>
            </tbody>
          </Table>
        ) : (
          <Alert variant="info">No system information available.</Alert>
        )}
      </Card.Body>
    </Card>
  );
};

export default SystemInfo;