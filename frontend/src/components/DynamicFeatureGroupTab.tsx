import React, { useState } from 'react';
import { type FeatureSchema } from '../types/featureTypes';
import DynamicFeatureRenderer from './DynamicFeatureRenderer';
import { Alert, Form, InputGroup } from 'react-bootstrap';

interface DynamicFeatureGroupTabProps {
    features: FeatureSchema[];
    deviceId: string;
}

const DynamicFeatureGroupTab: React.FC<DynamicFeatureGroupTabProps> = ({ features, deviceId }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [featureValues, setFeatureValues] = useState<Record<string, any>>({});

    if (features.length === 0) {
        return <Alert variant="info">No features available in this category.</Alert>;
    }

    // Filter features based on search term
    const filteredFeatures = features.filter(feature => 
        feature.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (feature.description && feature.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // Handle feature value changes for dependency tracking
    const handleFeatureValueChange = (featureName: string, value: any) => {
        setFeatureValues(prev => ({
            ...prev,
            [featureName]: value
        }));
    };

    return (
        <div>
            {/* Search bar for filtering features */}
            <InputGroup className="mb-3">
                <Form.Control
                    placeholder="Search features..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </InputGroup>
            
            {filteredFeatures.length === 0 ? (
                <Alert variant="info">No features match your search criteria.</Alert>
            ) : (
                <div className="d-flex flex-wrap">
                    {filteredFeatures.map((feature) => (
                        <DynamicFeatureRenderer 
                            key={feature.name} 
                            feature={feature} 
                            deviceId={deviceId}
                            featureDependencies={featureValues}
                            onDependencyChange={handleFeatureValueChange}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export default DynamicFeatureGroupTab;