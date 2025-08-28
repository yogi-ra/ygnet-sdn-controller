import React from 'react';
import { Table, Spinner, Alert } from 'react-bootstrap';
import { type FeatureSchema, FeatureType } from '../../types/featureTypes';
import { useFeatureData } from '../../hooks/useFeatureData';

interface DisplayTableFeatureProps {
    feature: FeatureSchema;
    deviceId: string;
}

const DisplayTableFeature: React.FC<DisplayTableFeatureProps> = ({ feature, deviceId }) => {
    const { data, isLoading: loading, isError, error } = useFeatureData(deviceId, feature.name);
    

    if (loading) {
        console.log(`Loading data for ${feature.name}...`); // Add this line
        return (
            <div className="text-center">
                <Spinner animation="border" size="sm" /> Loading {feature.label.toLowerCase()}...
            </div>
        );
    }

    if (error) {
        return <Alert variant="danger">Error: {error}</Alert>;
    }

    // Ensure data is an array for mapping
    const tableData = Array.isArray(data) ? data : (data ? [data] : []);

    // Ensure data is an array and its first element is a valid object before getting keys
    const headers = (tableData.length > 0 && typeof tableData[0] === 'object' && tableData[0] !== null)
        ? Object.keys(tableData[0])
        : []; // Return an empty array if tableData[0] is not a valid object

    if (tableData.length === 0) { // Check if tableData is empty after potential conversion
        return <Alert variant="info">No {feature.label.toLowerCase()} information available.</Alert>;
    }

    return (
        <div className="table-responsive" style={{ maxHeight: "300px", overflowY: "auto" }}>
            <Table striped bordered hover size="sm">
                <thead>
                    <tr>
                        {headers.map((header) => (
                            <th key={header}>{header.replace(/_/g, ' ').toUpperCase()}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {tableData.map((row, rowIndex) => ( // Use tableData here
                        <tr key={rowIndex}>
                            {headers.map((header, colIndex) => (
                                <td key={`${rowIndex}-${colIndex}`}>
                                    {Array.isArray(row[header]) ? row[header].join(', ') : row[header]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </Table>
        </div>
    );
};

export default DisplayTableFeature;
