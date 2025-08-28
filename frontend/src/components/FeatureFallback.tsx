import React from 'react';
import { Card, Alert, Button } from 'react-bootstrap';
import { type FeatureSchema } from '../types/featureTypes';

interface FeatureFallbackProps {
    feature: FeatureSchema;
    error: Error;
    resetErrorBoundary: () => void;
}

const FeatureFallback: React.FC<FeatureFallbackProps> = ({ feature, error, resetErrorBoundary }) => {
    // Check if it's a device offline error
    const isDeviceOffline = error.message.includes("Device is currently offline") || 
                           error.message.includes("503") ||
                           error.message.includes("Connection failed") ||
                           error.message.includes("Authentication failed") ||
                           error.message.includes("timed out");
    
    return (
        <Card className="mb-4 border-danger">
            <Card.Body>
                <Card.Title as="h3" className="text-danger">{feature.label}</Card.Title>
                <Alert variant={isDeviceOffline ? "warning" : "danger"}>
                    <Alert.Heading>{isDeviceOffline ? "Device Offline" : "Feature Error"}</Alert.Heading>
                    <p>
                        {isDeviceOffline 
                            ? "The device is currently offline or unreachable. Please check the device's network connectivity and try again later."
                            : `An error occurred while rendering the "${feature.label}" feature:`
                        }
                    </p>
                    {!isDeviceOffline && (
                        <p className="mb-0">
                            <strong>{error.message}</strong>
                        </p>
                    )}
                </Alert>
                <Button 
                    type="button" 
                    variant="outline-primary"
                    onClick={resetErrorBoundary}
                >
                    Try again
                </Button>
            </Card.Body>
        </Card>
    );
};

export default FeatureFallback;