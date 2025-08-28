import React, { useState } from 'react';
import { Button, Spinner, Alert } from 'react-bootstrap';
import { type FeatureSchema, type FeatureActionRequest } from '../../types/featureTypes';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

interface ButtonFeatureProps {
    feature: FeatureSchema;
    deviceId: string;
}

const ButtonFeature: React.FC<ButtonFeatureProps> = ({ feature, deviceId }) => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const handleClick = async () => {
        setLoading(true);
        setError(null);
        setSuccess(null);

        const actionRequest: FeatureActionRequest = {
            feature_name: feature.name,
            value: null, // Buttons typically don't have a value
        };

        try {
            const response = await fetch(`/api/devices/${deviceId}/action`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(actionRequest),
            });

            if (response.status === 401) {
                logout();
                navigate('/login');
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to perform action');
            }
            setSuccess('Action performed successfully!');
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
                disabled={loading || feature.read_only}
            >
                {loading ? <Spinner animation="border" size="sm" /> : feature.label}
            </Button>
            {loading && <Spinner animation="border" size="sm" className="ms-2" />}
            {error && <Alert variant="danger" className="mt-2">{error}</Alert>}
            {success && <Alert variant="success" className="mt-2">{success}</Alert>}
            {feature.read_only && <Alert variant="info" className="mt-2">Read-only feature.</Alert>}
        </div>
    );
};

export default ButtonFeature;
