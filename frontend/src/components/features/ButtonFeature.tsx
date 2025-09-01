import React, { useState } from 'react';
import { Button, Spinner, Alert } from 'react-bootstrap';
import { type FeatureSchema } from '../../types/featureTypes';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { performFeatureAction } from '../../api';

interface ButtonFeatureProps {
    feature: FeatureSchema;
    deviceId: string;
}

const ButtonFeature: React.FC<ButtonFeatureProps> = ({ feature, deviceId }) => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const handleClick = async () => {
        setLoading(true);
        setError(null);
        setSuccess(null);

        const actionRequest = {
            feature_name: feature.name,
            backend_method: feature.backend_method,
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
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <Button 
                variant="primary" 
                onClick={handleClick} 
                disabled={loading}
            >
                {feature.label}
                {loading && <Spinner animation="border" size="sm" className="ms-2" />}
            </Button>
            {error && <Alert variant="danger" className="mt-2">{error}</Alert>}
            {success && <Alert variant="success" className="mt-2">{success}</Alert>}
        </div>
    );
};

export default ButtonFeature;