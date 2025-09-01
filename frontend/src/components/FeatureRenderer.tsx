import React from 'react';
import { type FeatureSchema, ViewFeatureType, ActionFeatureType } from '../types/featureTypes';
import ToggleFeature from './features/ToggleFeature';
import TextInputFeature from './features/TextInputFeature';
import DisplayTableFeature from './features/DisplayTableFeature';
import DisplayTextFeature from './features/DisplayTextFeature';
import SelectOptionFeature from './features/SelectOptionFeature';
import ButtonFeature from './features/ButtonFeature';
import TextAreaFeature from './features/TextAreaFeature';
import { Card } from 'react-bootstrap';
import { useFeatureState } from '../context/FeatureStateContext';

interface FeatureRendererProps {
    feature: FeatureSchema;
    deviceId: string;
}

const featureComponentMap: Record<ViewFeatureType | ActionFeatureType, React.FC<any>> = {
    [ViewFeatureType.DISPLAY_TABLE]: DisplayTableFeature,
    [ViewFeatureType.DISPLAY_TEXT]: DisplayTextFeature,
    [ActionFeatureType.TOGGLE]: ToggleFeature,
    [ActionFeatureType.INPUT_TEXT]: TextInputFeature,
    [ActionFeatureType.SELECT_OPTION]: SelectOptionFeature,
    [ActionFeatureType.BUTTON]: ButtonFeature,
    [ActionFeatureType.TEXT_AREA]: TextAreaFeature,
};

const FeatureRenderer: React.FC<FeatureRendererProps> = ({ feature, deviceId }) => {
    const Component = featureComponentMap[feature.type];
    const { featureState, setFeatureState } = useFeatureState();

    const areDependenciesMet = () => {
        if (!feature.dependencies || feature.dependencies.length === 0) {
            return true;
        }

        return feature.dependencies.every(dep => {
            const parentValue = featureState[dep.feature_name];

            switch (dep.operator) {
                case 'equals':
                    return parentValue === dep.value;
                case 'not_equals':
                    return parentValue !== dep.value;
                default:
                    return false;
            }
        });
    };

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

    if (!areDependenciesMet()) {
        return null;
    }

    return (
        <Card className="mb-4">
            <Card.Body>
                <Card.Title as="h3">{feature.label}</Card.Title>
                {feature.description && <Card.Text>{feature.description}</Card.Text>}
                <Component feature={feature} deviceId={deviceId} featureState={featureState} setFeatureState={setFeatureState} />
            </Card.Body>
        </Card>
    );
};

export default FeatureRenderer;