import React, { useState, useEffect } from 'react';
import { Form, Spinner, Alert } from 'react-bootstrap';
import { type FeatureSchema, type FeatureActionRequest } from '../../types/featureTypes';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

interface ToggleFeatureProps {
    feature: FeatureSchema;
    deviceId: string;
}

const ToggleFeature: React.FC<ToggleFeatureProps> = ({ feature, deviceId }) => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const [isChecked, setIsChecked] = useState<boolean>(feature.default_value || false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Effect to update the toggle state if the default_value changes (e.g., live data update)
    useEffect(() => {
        if (feature.default_value !== undefined) {
            setIsChecked(feature.default_value);
        }
    }, [feature.default_value]);

    const handleToggleChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = event.target.checked;
        setIsChecked(newValue); // Optimistic update
        setLoading(true);
        setError(null);
        setSuccess(null);

        const actionRequest: FeatureActionRequest = {
            feature_name: feature.name,
            value: newValue,
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
            setIsChecked(!newValue); // Revert on error
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
