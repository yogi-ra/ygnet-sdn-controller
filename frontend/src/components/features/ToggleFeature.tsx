import React, { useState } from 'react';
import { Form, Spinner, Alert } from 'react-bootstrap';
import { type FeatureSchema } from '../../types/featureTypes';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { performFeatureAction } from '../../api';

interface ToggleFeatureProps {
    feature: FeatureSchema;
    deviceId: string;
    featureState: { [key: string]: any };
    setFeatureState: React.Dispatch<React.SetStateAction<{ [key: string]: any }>>;
}

const ToggleFeature: React.FC<ToggleFeatureProps> = ({ feature, deviceId, featureState, setFeatureState }) => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const isChecked = featureState[feature.name] || false;

    const handleToggleChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = event.target.checked;
        setFeatureState(prevState => ({ ...prevState, [feature.name]: newValue })); // Optimistic update
        setLoading(true);
        setError(null);
        setSuccess(null);

        const actionRequest: any = {
            feature_name: feature.name,
            value: newValue,
        };

        try {
            // Perform the action using our API function
            await performFeatureAction(deviceId, actionRequest, token);
            
            setSuccess('Action performed successfully!');
            
            // Invalidate and refetch the feature data immediately
            await queryClient.invalidateQueries({ queryKey: ['device-feature', deviceId, feature.name] });
            await queryClient.refetchQueries({ queryKey: ['device-feature', deviceId, feature.name] });
        } catch (err: any) {
            setError(err.message || 'An unknown error occurred.');
            setFeatureState(prevState => ({ ...prevState, [feature.name]: !newValue })); // Revert on error
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <Form.Check
                type="switch"
                id={`toggle-${feature.name}`}
                label={feature.label}
                checked={isChecked}
                onChange={handleToggleChange}
                disabled={loading || feature.read_only}
            />
            {loading && <Spinner animation="border" size="sm" className="ms-2" />}
            {error && <Alert variant="danger" className="mt-2">{error}</Alert>}
            {success && <Alert variant="success" className="mt-2">{success}</Alert>}
            {feature.read_only && <Alert variant="info" className="mt-2">Read-only feature.</Alert>}
        </div>
    );
};

export default ToggleFeature;