import React, { createContext, useContext, ReactNode } from 'react';

// Define the structure for device type configurations
interface DeviceTypeConfig {
  name: string;
  displayName: string;
  icon?: string;
  theme?: string;
  customComponents?: Record<string, React.ComponentType<any>>;
}

// Create context for device type registry
interface DeviceTypeRegistryContextType {
  deviceTypes: Record<string, DeviceTypeConfig>;
  getDeviceTypeConfig: (deviceType: string) => DeviceTypeConfig | undefined;
  registerDeviceType: (deviceType: string, config: DeviceTypeConfig) => void;
}

const DeviceTypeRegistryContext = createContext<DeviceTypeRegistryContextType | undefined>(undefined);

// Provider component
export const DeviceTypeRegistryProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Initial device type configurations
  const initialDeviceTypes: Record<string, DeviceTypeConfig> = {
    'cisco_ios_router': {
      name: 'cisco_ios_router',
      displayName: 'Cisco IOS Router',
      icon: 'router',
      theme: 'cisco',
    },
    'cisco_ios_switch': {
      name: 'cisco_ios_switch',
      displayName: 'Cisco IOS Switch',
      icon: 'switch',
      theme: 'cisco',
    },
    'ubiquiti_edgerouter': {
      name: 'ubiquiti_edgerouter',
      displayName: 'Ubiquiti EdgeRouter',
      icon: 'router',
      theme: 'ubiquiti',
    },
    'ubiquiti_edgeswitch': {
      name: 'ubiquiti_edgeswitch',
      displayName: 'Ubiquiti EdgeSwitch',
      icon: 'switch',
      theme: 'ubiquiti',
    },
    'ubiquiti_unifiswitch': {
      name: 'ubiquiti_unifiswitch',
      displayName: 'Ubiquiti UniFi Switch',
      icon: 'switch',
      theme: 'ubiquiti',
    },
  };

  // State for device types
  const [deviceTypes, setDeviceTypes] = React.useState<Record<string, DeviceTypeConfig>>(initialDeviceTypes);

  // Get configuration for a specific device type
  const getDeviceTypeConfig = (deviceType: string): DeviceTypeConfig | undefined => {
    return deviceTypes[deviceType];
  };

  // Register a new device type
  const registerDeviceType = (deviceType: string, config: DeviceTypeConfig) => {
    setDeviceTypes(prev => ({
      ...prev,
      [deviceType]: config
    }));
  };

  return (
    <DeviceTypeRegistryContext.Provider value={{ 
      deviceTypes, 
      getDeviceTypeConfig, 
      registerDeviceType 
    }}>
      {children}
    </DeviceTypeRegistryContext.Provider>
  );
};

// Hook to use the device type registry
export const useDeviceTypeRegistry = () => {
  const context = useContext(DeviceTypeRegistryContext);
  if (!context) {
    throw new Error('useDeviceTypeRegistry must be used within a DeviceTypeRegistryProvider');
  }
  return context;
};

// Component to register a new device type
export const RegisterDeviceType: React.FC<{ deviceType: string; config: DeviceTypeConfig }> = ({ 
  deviceType, 
  config 
}) => {
  const { registerDeviceType } = useDeviceTypeRegistry();
  
  React.useEffect(() => {
    registerDeviceType(deviceType, config);
  }, [deviceType, config, registerDeviceType]);
  
  return null; // This component doesn't render anything
};