import { Container, Card, Row, Col } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import { useAuth } from '../hooks/useAuth'; // Import useAuth

const DashboardPage = () => {
  const [totalDevices, setTotalDevices] = useState(0);
  const [activeDevicesCount, setActiveDevicesCount] = useState(0); // New state for active devices
  const [inactiveDevicesCount, setinactiveDevicesCount] = useState(0); // New state for active devices
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth(); // Get the token from useAuth
  const navigate = useNavigate(); // Get the navigate function

  // Placeholder for API Version - in a real app, this might come from a /version endpoint
  const apiVersion = "N/A"; 

  useEffect(() => {
    const fetchDevicesAndReachability = async () => {
      if (!token) {
        navigate('/login'); // Redirect to login page
        return;
      }

      try {
        // Fetch all devices
        const devicesResponse = await fetch('/api/devices/stats', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        if (!devicesResponse.ok) {
          const errorData = await devicesResponse.json();
          throw new Error(errorData.detail || `HTTP error! status: ${devicesResponse.status}`);
        }
        const devices = await devicesResponse.json();
        setTotalDevices(devices.total_devices);
        setActiveDevicesCount(devices.active_devices);
        setinactiveDevicesCount(devices.inactive_devices)

      } catch (e: any) {
        if (e.message && e.message.includes("Could not validate credentials")) {
          navigate('/login');
        } else {
          setError(e.message);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDevicesAndReachability();
  }, [token]);

  if (loading) {
    return <Container fluid className="mt-4"><p>Loading dashboard data...</p></Container>;
  }

  if (error) {
    return <Container fluid className="mt-4"><p className="text-danger">Error loading data: {error}</p></Container>;
  }

  return (
    <Container fluid className="mt-4">
      <Row>
        <Col md={12}>
          <Card className="mb-4">
            <Card.Body>
              <Card.Title as="h1">Dashboard</Card.Title>
              <Card.Text>
                Welcome to your {import.meta.env.VITE_PROJECT_NAME} dashboard. You are successfully logged in.
              </Card.Text>
              <Card.Text>
                Use the navigation bar above to manage your network devices.
              </Card.Text>
              <Card.Text className="text-muted">
                API Version: {apiVersion}
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col md={6} lg={4}>
          <Card className="text-center bg-primary text-white mb-4">
            <Card.Body>
              <Card.Title as="h2">{totalDevices}</Card.Title>
              <Card.Text>Total Devices</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6} lg={4}>
          <Card className="text-center bg-success text-white mb-4">
            <Card.Body>
              <Card.Title as="h2">{activeDevicesCount}</Card.Title>
              <Card.Text>Active Devices</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6} lg={4}>
          <Card className="text-center bg-info text-white mb-4">
            <Card.Body>
              <Card.Title as="h2">{inactiveDevicesCount}</Card.Title>
              <Card.Text>Inactive Devices</Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col md={12}>
          <Card>
            <Card.Body>
              <Card.Title as="h2">Quick Actions</Card.Title>
              <Card.Text>
                Here you can find quick links to common tasks:
              </Card.Text>
              <ul>
                <li><a href="/devices/add">Add New Device</a></li>
                <li><a href="/devices">View All Devices</a></li>
                {/* Add more quick actions as needed */}
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default DashboardPage;
