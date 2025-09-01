import React, { useState } from 'react';
import { Form, Spinner, Alert } from 'react-bootstrap';
import { type TableAction } from '../../types/featureTypes';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { performFeatureAction } from '../../api';

interface TableRowActionProps {
    action: TableAction;
    deviceId: string;
    rowIdentifier: string;
    rowIdentifierValue: any;
    initialState: boolean;
    featureName: string;
}

const TableRowAction: React.FC<TableRowActionProps> = ({ 
    action, 
    deviceId, 
    rowIdentifier, 
    rowIdentifierValue, 
    initialState,
    featureName
}) => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [isChecked, setIsChecked] = useState<boolean>(!!initialState);

    const handleToggleChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = event.target.checked;
        setIsChecked(newValue); // Optimistic update
        setLoading(true);
        setError(null);
        setSuccess(null);

        const actionRequest = {
            feature_name: action.feature_name,
            backend_method: action.backend_method,
            data: {
                interface_name: rowIdentifierValue,
                enabled: newValue,
            },
        };

        try {
            // Perform the action using our API function
            await performFeatureAction(deviceId, actionRequest, token);
            
            setSuccess('Action performed successfully!');
            
            // Invalidate and refetch the feature data immediately
            await queryClient.invalidateQueries({ queryKey: ['device-feature', deviceId, featureName] });
            await queryClient.refetchQueries({ queryKey: ['device-feature', deviceId, featureName] });
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
                id={`toggle-${action.feature_name}-${rowIdentifierValue}`}
                checked={isChecked}
                onChange={handleToggleChange}
                disabled={loading}
            />
            {loading && <Spinner animation="border" size="sm" className="ms-2" />}
            {error && <Alert variant="danger" className="mt-2">{error}</Alert>}
            {success && <Alert variant="success" className="mt-2">{success}</Alert>}
        </div>
    );
};

export default TableRowAction;