import React, { useState, useEffect } from 'react';
import { type FeatureSchema, FeatureType } from '../types/featureTypes';
import { Card, Alert } from 'react-bootstrap';
import ErrorBoundary from './ErrorBoundary';
import FeatureFallback from './FeatureFallback';
import { useFeatureComponentRegistry } from './FeatureComponentRegistry';

interface DynamicFeatureRendererProps {
    feature: FeatureSchema;
    deviceId: string;
    featureDependencies?: Record<string, any>; // Current values of other features for dependency checking
    onDependencyChange?: (featureName: string, value: any) => void;
}

const DynamicFeatureRenderer: React.FC<DynamicFeatureRendererProps> = ({ 
    feature, 
    deviceId,
    featureDependencies = {},
    onDependencyChange
}) => {
    const { getComponent } = useFeatureComponentRegistry();
    const [isVisible, setIsVisible] = useState(true);
    const [isEnabled, setIsEnabled] = useState(true);

    // Check feature dependencies
    useEffect(() => {
        if (!feature.dependencies || feature.dependencies.length === 0) {
            setIsVisible(true);
            setIsEnabled(true);
            return;
        }

        let visible = true;
        let enabled = true;

        for (const dependency of feature.dependencies) {
            const dependentValue = featureDependencies[dependency.feature_name];
            
            if (dependentValue === undefined) {
                // If dependency value is not available, we might hide or disable based on requirement
                visible = false;
                enabled = false;
                break;
            }

            switch (dependency.operator) {
                case "equals":
                    if (dependentValue !== dependency.value) {
                        visible = false;
                        enabled = false;
                    }
                    break;
                case "not_equals":
                    if (dependentValue === dependency.value) {
                        visible = false;
                        enabled = false;
                    }
                    break;
                default:
                    // Unknown operator, assume feature should be hidden/disabled
                    visible = false;
                    enabled = false;
            }
        }

        setIsVisible(visible);
        setIsEnabled(enabled);
    }, [feature.dependencies, featureDependencies]);

    if (!isVisible) {
        return null; // Don't render if not visible based on dependencies
    }

    const Component = getComponent(feature.type);

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

    // Render with dependency-aware props and error boundary
    return (
        <ErrorBoundary fallback={(props) => <FeatureFallback feature={feature} {...props} />}>
            <Card className="mb-4" style={{ opacity: isEnabled ? 1 : 0.6 }}>
                <Card.Body>
                    <Card.Title as="h3">{feature.label}</Card.Title>
                    {feature.description && <Card.Text>{feature.description}</Card.Text>}
                    <Component 
                        feature={feature} 
                        deviceId={deviceId} 
                        disabled={!isEnabled}
                        onDependencyChange={onDependencyChange}
                    />
                </Card.Body>
            </Card>
        </ErrorBoundary>
    );
};

export default DynamicFeatureRenderer;