import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchDeviceTypes } from '../api';
import type { DeviceTypeInfo } from '../types/deviceTypes';
import { useAuth } from '../hooks/useAuth';

interface ConfigContextType {
  deviceTypes: DeviceTypeInfo[] | null;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export const ConfigProvider: React.FC = ({ children }) => {
  const [deviceTypes, setDeviceTypes] = useState<DeviceTypeInfo[] | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    if (token) {
      // Fetch device types
      fetchDeviceTypes(token)
        .then(data => setDeviceTypes(data))
        .catch(error => {
          console.error("Failed to fetch device types:", error);
          setDeviceTypes([]); // Set to empty array on error
        });
    }
  }, [token]);

  return (
    <ConfigContext.Provider value={{ deviceTypes }}>
      {children}
    </ConfigContext.Provider>
  );
};

export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};