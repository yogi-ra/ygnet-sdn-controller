import { Container, Card, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { fetchDevices, backupDevices, type Device } from '../api';

const BackupPage = () => {
  const { token } = useAuth();
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevices, setSelectedDevices] = useState<number[]>([]);
  const [backupResult, setBackupResult] = useState<{ message: string; results: Array<{ device?: string; status: string; message?: string }> } | null>(null);
  const [isBackupRunning, setIsBackupRunning] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const loadDevices = async () => {
      try {
        const response = await fetchDevices(token, 0, 100); // Fetch up to 100 devices
        setDevices(response.devices);
      } catch (error) {
        console.error('Failed to fetch devices:', error);
      }
    };

    loadDevices();
  }, [token]);

  const handleCheckboxChange = (deviceId: number) => {
    setSelectedDevices(prevSelected => {
      if (prevSelected.includes(deviceId)) {
        return prevSelected.filter(id => id !== deviceId);
      } else {
        return [...prevSelected, deviceId];
      }
    });
  };

  const handleBackup = async () => {
    console.log('Selected device IDs for backup:', selectedDevices);
    
    if (selectedDevices.length === 0) return;
    
    setIsBackupRunning(true);
    setBackupResult(null);
    
    try {
      const result = await backupDevices(selectedDevices, token);
      setBackupResult(result);
      console.log('Backup result:', result);
    } catch (error) {
      console.error('Failed to backup devices:', error);
      setBackupResult({
        message: 'Backup failed',
        results: selectedDevices.map(id => ({
          status: 'error',
          message: 'Failed to backup device'
        }))
      });
    } finally {
      setIsBackupRunning(false);
    }
  };

  return (
    <Container fluid className="mt-4">
      <Row>
        <Col md={12}>
          <Card className="mb-4">
            <Card.Body>
              <Card.Title as="h1">Backup Devices</Card.Title>
              <Card.Text>Select devices to backup:</Card.Text>
              
              <div className="d-flex justify-content-between mb-3">
                <Button 
                  variant="outline-primary" 
                  size="sm"
                  onClick={() => 
                    {
                      if (selectedDevices.length === devices.length) {
                      setSelectedDevices([]);
                      } else {
                      setSelectedDevices(devices.map(device => device.id));
                      }
                    } 
                } 
                >
                  {selectedDevices.length === devices.length ? 'Deselect All' : 'Select All'}
                </Button>
              </div>
              
              <Form>
                {devices.map(device => (
                  <Form.Check
                    key={device.id}
                    type="checkbox"
                    id={`device-${device.id}`}
                    label={`${device.name} (${device.ip_address})`}
                    checked={selectedDevices.includes(device.id)}
                    onChange={() => handleCheckboxChange(device.id)}
                  />
                ))}
              </Form>
              
              <div className="mt-3">
                <Button 
                  variant="primary" 
                  onClick={handleBackup}
                  disabled={selectedDevices.length === 0 || isBackupRunning}
                >
                  {isBackupRunning ? 'Backing up...' : 'Backup Selected Devices'}
                </Button>
              </div>
              
              {backupResult && (
                <div className="mt-4">
                  <Alert variant={backupResult.results.some(r => r.status === 'failed' || r.status === 'error') ? 'danger' : 'success'}>
                    <strong>Backup Result:</strong> {backupResult.message}
                  </Alert>
                  <div className="console-log" style={{ 
                    backgroundColor: '#f8f9fa', 
                    border: '1px solid #ccc', 
                    padding: '10px', 
                    height: '200px', 
                    overflowY: 'scroll',
                    fontFamily: 'monospace',
                    fontSize: '12px'
                  }}>
                    {backupResult.results.map((result, index) => (
                      <div key={index} style={{ 
                        color: result.status === 'success' ? 'green' : 'red',
                        marginBottom: '5px'
                      }}>
                        {result.device ? `${result.device}: ${result.status}` : `Result ${index + 1}: ${result.status}`}
                        {result.message && ` - ${result.message}`}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default BackupPage;
