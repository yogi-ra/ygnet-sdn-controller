import React, { createContext, useContext, ReactNode } from 'react';
import { useDeviceTypeRegistry } from './DeviceTypeRegistry';

// Define the structure for device type specific features
interface DeviceTypeSpecificFeature {
  name: string;
  component: React.ComponentType<any>;
  position: 'header' | 'sidebar' | 'tab' | 'footer';
  order: number;
}

// Create context for device type specific features
interface DeviceTypeSpecificFeaturesContextType {
  features: Record<string, DeviceTypeSpecificFeature[]>;
  getFeaturesForDeviceType: (deviceType: string) => DeviceTypeSpecificFeature[];
  registerFeature: (deviceType: string, feature: DeviceTypeSpecificFeature) => void;
}

const DeviceTypeSpecificFeaturesContext = createContext<DeviceTypeSpecificFeaturesContextType | undefined>(undefined);

// Provider component
export const DeviceTypeSpecificFeaturesProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Initial device type specific features
  const initialFeatures: Record<string, DeviceTypeSpecificFeature[]> = {
    // Example features for Cisco IOS devices
    'cisco_ios_router': [
      // Add router-specific features here
    ],
    'cisco_ios_switch': [
      // Add switch-specific features here
    ],
  };

  // State for features
  const [features, setFeatures] = React.useState<Record<string, DeviceTypeSpecificFeature[]>>(initialFeatures);

  // Get features for a specific device type
  const getFeaturesForDeviceType = (deviceType: string): DeviceTypeSpecificFeature[] => {
    return features[deviceType] || [];
  };

  // Register a new feature for a device type
  const registerFeature = (deviceType: string, feature: DeviceTypeSpecificFeature) => {
    setFeatures(prev => {
      const deviceFeatures = prev[deviceType] || [];
      return {
        ...prev,
        [deviceType]: [...deviceFeatures, feature]
      };
    });
  };

  return (
    <DeviceTypeSpecificFeaturesContext.Provider value={{ 
      features, 
      getFeaturesForDeviceType, 
      registerFeature 
    }}>
      {children}
    </DeviceTypeSpecificFeaturesContext.Provider>
  );
};

// Hook to use the device type specific features
export const useDeviceTypeSpecificFeatures = () => {
  const context = useContext(DeviceTypeSpecificFeaturesContext);
  if (!context) {
    throw new Error('useDeviceTypeSpecificFeatures must be used within a DeviceTypeSpecificFeaturesProvider');
  }
  return context;
};

// Component to register a new device type specific feature
export const RegisterDeviceTypeFeature: React.FC<{ 
  deviceType: string; 
  feature: DeviceTypeSpecificFeature 
}> = ({ deviceType, feature }) => {
  const { registerFeature } = useDeviceTypeSpecificFeatures();
  
  React.useEffect(() => {
    registerFeature(deviceType, feature);
  }, [deviceType, feature, registerFeature]);
  
  return null; // This component doesn't render anything
};

// Component to render device type specific features at a given position
export const DeviceTypeSpecificFeatureRenderer: React.FC<{ 
  deviceType: string; 
  position: 'header' | 'sidebar' | 'tab' | 'footer';
  deviceId: string;
}> = ({ deviceType, position, deviceId }) => {
  const { getDeviceTypeConfig } = useDeviceTypeRegistry();
  const { getFeaturesForDeviceType } = useDeviceTypeSpecificFeatures();
  
  // Get device type config
  const deviceTypeConfig = getDeviceTypeConfig(deviceType);
  
  // Get features for this device type and position
  const features = getFeaturesForDeviceType(deviceType)
    .filter(feature => feature.position === position)
    .sort((a, b) => a.order - b.order);
  
  if (features.length === 0) {
    return null;
  }

  return (
    <div className={`device-type-specific-features device-type-${deviceType} position-${position}`}>
      {features.map((feature, index) => {
        const Component = feature.component;
        return <Component key={index} deviceId={deviceId} />;
      })}
    </div>
  );
};