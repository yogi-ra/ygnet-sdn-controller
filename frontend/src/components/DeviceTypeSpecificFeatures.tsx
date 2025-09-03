import React from 'react';

// Component to render device type specific features at a given position
// This is a placeholder component since we've removed the dynamic features
export const DeviceTypeSpecificFeatureRenderer: React.FC<{ 
  deviceType: string; 
  position: 'header' | 'sidebar' | 'tab' | 'footer';
  deviceId: string;
}> = ({ deviceType, position, deviceId }) => {
  // This component doesn't render anything since we've removed dynamic features
  return null;
};