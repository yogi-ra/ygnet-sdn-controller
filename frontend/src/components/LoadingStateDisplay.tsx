import React from 'react';
import { Spinner, ProgressBar } from 'react-bootstrap';

interface LoadingStateDisplayProps {
  message?: string;
  showProgressBar?: boolean;
  progress?: number;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info' | 'light' | 'dark';
}

const LoadingStateDisplay: React.FC<LoadingStateDisplayProps> = ({
  message = 'Loading...',
  showProgressBar = false,
  progress = 0,
  variant = 'primary'
}) => {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center p-4">
      <Spinner 
        animation="border" 
        role="status" 
        variant={variant}
        className="mb-3"
      >
        <span className="visually-hidden">{message}</span>
      </Spinner>
      <p className="mb-0 text-center">{message}</p>
      {showProgressBar && (
        <div className="w-100 mt-3">
          <ProgressBar 
            now={progress} 
            variant={variant}
            striped
            animated
          />
        </div>
      )}
    </div>
  );
};

export default LoadingStateDisplay;