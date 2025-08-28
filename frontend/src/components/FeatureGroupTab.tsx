import React from 'react';
import { type FeatureSchema } from '../types/featureTypes';
import FeatureRenderer from './FeatureRenderer';
import { Alert } from 'react-bootstrap';

interface FeatureGroupTabProps {
    features: FeatureSchema[];
    deviceId: string;
}

const FeatureGroupTab: React.FC<FeatureGroupTabProps> = ({ features, deviceId }) => {
    if (features.length === 0) {
        return <Alert variant="info">No features available in this category.</Alert>;
    }

    return (
        <div className="d-flex flex-wrap">
            {features.map((feature) => (
                <FeatureRenderer key={feature.name} feature={feature} deviceId={deviceId} />
            ))}
        </div>
    );
};

export default FeatureGroupTab;
