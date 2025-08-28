import React, { useState, useEffect } from 'react';
import { Form, Button, Spinner, Alert } from 'react-bootstrap';
import { type FeatureSchema, type FeatureActionRequest } from '../../types/featureTypes';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

interface TextInputFeatureProps {
    feature: FeatureSchema;
    deviceId: string;
}

const TextInputFeature: React.FC<TextInputFeatureProps> = ({ feature, deviceId }) => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const [inputValue, setInputValue] = useState<string>(feature.default_value || '');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Effect to update the input state if the default_value changes (e.g., live data update)
    useEffect(() => {
        if (feature.default_value !== undefined) {
            setInputValue(feature.default_value);
        }
    }, [feature.default_value]);

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        const actionRequest: FeatureActionRequest = {
            feature_name: feature.name,
            value: inputValue,
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
        <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
                <Form.Label>{feature.label}</Form.Label>
                <Form.Control
                    type="text"
                    placeholder={feature.placeholder || `Enter ${feature.label.toLowerCase()}`}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    disabled={loading || feature.read_only}
                />
            </Form.Group>
            {!feature.read_only && (
                <Button variant="primary" type="submit" disabled={loading}>
                    {loading ? <Spinner animation="border" size="sm" /> : 'Set'}
                </Button>
            )}
            {loading && <Spinner animation="border" size="sm" className="ms-2" />}
            {error && <Alert variant="danger" className="mt-2">{error}</Alert>}
            {success && <Alert variant="success" className="mt-2">{success}</Alert>}
            {feature.read_only && <Alert variant="info" className="mt-2">Read-only feature.</Alert>}
        </Form>
    );
};

export default TextInputFeature;
