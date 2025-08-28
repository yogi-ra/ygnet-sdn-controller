import React from 'react';
import { type FeatureSchema, FeatureType } from '../types/featureTypes';
import ToggleFeature from './features/ToggleFeature'; // Dedicated component for toggle
import TextInputFeature from './features/TextInputFeature'; // Dedicated component for text input
import DisplayTableFeature from './features/DisplayTableFeature'; // Dedicated component for table display
import DisplayTextFeature from './features/DisplayTextFeature';
import SelectOptionFeature from './features/SelectOptionFeature';
import ButtonFeature from './features/ButtonFeature';
import { Card } from 'react-bootstrap'; // Import Card for consistent styling

interface FeatureRendererProps {
    feature: FeatureSchema;
    deviceId: string;
}

// Map FeatureType to a React component
const featureComponentMap: Record<FeatureType, React.FC<any>> = {
    [FeatureType.TOGGLE]: ToggleFeature,
    [FeatureType.INPUT_TEXT]: TextInputFeature,
    [FeatureType.DISPLAY_TABLE]: DisplayTableFeature,
    [FeatureType.DISPLAY_TEXT]: DisplayTextFeature,
    [FeatureType.SELECT_OPTION]: SelectOptionFeature,
    [FeatureType.BUTTON]: ButtonFeature,
    // Add other feature types as needed
};

const FeatureRenderer: React.FC<FeatureRendererProps> = ({ feature, deviceId }) => {
    const Component = featureComponentMap[feature.type];

    if (!Component) {
        console.warn(`No component found for feature type: ${feature.type}`);
        return (
            <Card className="mb-4">
                <Card.Body>
                    <Card.Title>{feature.label}</Card.Title>
                    <Card.Text className="text-danger">
                        Error: No renderer found for feature type "{feature.type}".
                    </Card.Text>
                </Card.Body>
            </Card>
        );
    }

    // You would also implement dependency checking here to conditionally render or disable
    // based on `feature.dependencies` and the current state of other features.
    // For now, we'll just render the component.

    return (
        <Card className="mb-4">
            <Card.Body>
                <Card.Title as="h3">{feature.label}</Card.Title>
                {feature.description && <Card.Text>{feature.description}</Card.Text>}
                <Component feature={feature} deviceId={deviceId} />
            </Card.Body>
        </Card>
    );
};

export default FeatureRenderer;
