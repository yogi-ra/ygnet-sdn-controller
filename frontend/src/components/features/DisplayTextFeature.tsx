import React from 'react';
import { Spinner, Alert } from 'react-bootstrap';
import { type FeatureSchema } from '../../types/featureTypes';
import { useFeatureData } from '../../hooks/useFeatureData';

interface DisplayTextFeatureProps {
    feature: FeatureSchema;
    deviceId: string;
}

const DisplayTextFeature: React.FC<DisplayTextFeatureProps> = ({ feature, deviceId }) => {
    const { data, isLoading: loading, isError, error } = useFeatureData(deviceId, feature.name);
    

    if (loading) {
        console.log(`Loading data for ${feature.name}...`); // Add this line
        return (
            <div className="text-center">
                <Spinner animation="border" size="sm" /> Loading {feature.label.toLowerCase()}...
            </div>
        );
    }

    if (error) {
        return <Alert variant="danger">Error: {error}</Alert>;
    }

    if (!data) {
        return <Alert variant="info">No {feature.label.toLowerCase()} information available.</Alert>;
    }

    let displayData: string;
    if (typeof data === 'object' && data !== null) {
        displayData = JSON.stringify(data, null, 2);
    } else {
        displayData = String(data); // Ensure it's a string
    }

    return (
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '300px', overflowY: 'auto', backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '5px' }}>
            {displayData}
        </pre>
    );
};

export default DisplayTextFeature;
