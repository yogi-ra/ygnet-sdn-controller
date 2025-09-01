import React, { useState } from 'react';
import { Form, Button, Spinner, Alert } from 'react-bootstrap';
import { type FeatureSchema } from '../../types/featureTypes';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { performFeatureAction } from '../../api';

interface SelectOptionFeatureProps {
    feature: FeatureSchema;
    deviceId: string;
    featureState: { [key: string]: any };
    setFeatureState: React.Dispatch<React.SetStateAction<{ [key: string]: any }>>;
}

const SelectOptionFeature: React.FC<SelectOptionFeatureProps> = ({ feature, deviceId, featureState, setFeatureState }) => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [localValue, setLocalValue] = useState<string>(featureState[feature.name] || feature.default_value || '');

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        const actionRequest = {
            feature_name: feature.name,
            value: localValue,
        };

        try {
            // Perform the action using our API function
            await performFeatureAction(deviceId, actionRequest, token);
            
            setSuccess('Action performed successfully!');
            setFeatureState(prevState => ({ ...prevState, [feature.name]: localValue }));
            
            // Invalidate and refetch the feature data immediately
            await queryClient.invalidateQueries({ queryKey: ['device-feature', deviceId, feature.name] });
            await queryClient.refetchQueries({ queryKey: ['device-feature', deviceId, feature.name] });
        } catch (err: any) {
            setError(err.message || 'An unknown error occurred.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <Form onSubmit={handleSubmit}>
                <Form.Group controlId={`select-${feature.name}`}>
                    <Form.Label>{feature.label}</Form.Label>
                    <Form.Control
                        as="select"
                        value={localValue}
                        onChange={(e) => setLocalValue(e.target.value)}
                        disabled={loading || feature.read_only}
                    >
                        {feature.options?.map((option) => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </Form.Control>
                </Form.Group>
                <Button 
                    variant="primary" 
                    type="submit" 
                    className="mt-2"
                    disabled={loading || feature.read_only}
                >
                    Apply
                    {loading && <Spinner animation="border" size="sm" className="ms-2" />}
                </Button>
            </Form>
            {error && <Alert variant="danger" className="mt-2">{error}</Alert>}
            {success && <Alert variant="success" className="mt-2">{success}</Alert>}
            {feature.read_only && <Alert variant="info" className="mt-2">Read-only feature.</Alert>}
        </div>
    );
};

export default SelectOptionFeature;