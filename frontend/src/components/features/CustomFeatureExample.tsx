import React from 'react';
import { Form, Button, Alert } from 'react-bootstrap';
import { FeatureSchema } from '../../types/featureTypes';

interface CustomFeatureExampleProps {
    feature: FeatureSchema;
    deviceId: string;
    disabled?: boolean;
    onDependencyChange?: (featureName: string, value: any) => void;
}

const CustomFeatureExample: React.FC<CustomFeatureExampleProps> = ({ 
    feature, 
    deviceId,
    disabled = false,
    onDependencyChange
}) => {
    const [value, setValue] = React.useState(feature.default_value || '');
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [result, setResult] = React.useState<{success?: string; error?: string} | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setResult(null);

        try {
            const response = await fetch(`/api/devices/${deviceId}/features/${feature.name}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ value }),
            });

            if (!response.ok) {
                throw new Error(`Failed to execute feature: ${response.statusText}`);
            }

            const data = await response.json();
            setResult({ success: data.message || 'Feature executed successfully' });
            
            // Notify parent of value change for dependency tracking
            if (onDependencyChange) {
                onDependencyChange(feature.name, value);
            }
        } catch (error: any) {
            setResult({ error: error.message || 'An unknown error occurred' });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
                <Form.Label>{feature.label}</Form.Label>
                <Form.Control
                    type="text"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    placeholder={feature.placeholder || "Enter value"}
                    disabled={disabled || isSubmitting}
                />
                {feature.description && (
                    <Form.Text className="text-muted">
                        {feature.description}
                    </Form.Text>
                )}
            </Form.Group>
            
            <Button 
                variant="primary" 
                type="submit" 
                disabled={disabled || isSubmitting}
            >
                {isSubmitting ? 'Executing...' : 'Execute'}
            </Button>
            
            {result?.success && (
                <Alert variant="success" className="mt-3">
                    {result.success}
                </Alert>
            )}
            
            {result?.error && (
                <Alert variant="danger" className="mt-3">
                    {result.error}
                </Alert>
            )}
        </Form>
    );
};

export default CustomFeatureExample;