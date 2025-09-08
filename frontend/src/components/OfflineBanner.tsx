import React from 'react';
import { Alert } from 'react-bootstrap';
import { WifiOff } from 'react-bootstrap-icons'; // Assuming you have react-bootstrap-icons installed

interface OfflineBannerProps {
  deviceName?: string;
}

const OfflineBanner: React.FC<OfflineBannerProps> = ({ deviceName }) => {
  return (
    <Alert variant="danger" className="text-center d-flex align-items-center justify-content-center p-3 my-3 shadow-sm rounded">
      <WifiOff size={30} className="me-3" />
      <div>
        <Alert.Heading className="mb-1">Device Offline</Alert.Heading>
        <p className="mb-0">
          {deviceName ? `The device "${deviceName}" is currently offline.` : "This device is currently offline."} Its details cannot be fetched.
        </p>
      </div>
    </Alert>
  );
};

export default OfflineBanner;