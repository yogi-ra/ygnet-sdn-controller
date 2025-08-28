import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchSupportedFeatures } from '../api';
import { useAuth } from '../hooks/useAuth';

interface ConfigContextType {
  supportedFeatures: Record<string, string[]> | null;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export const ConfigProvider: React.FC = ({ children }) => {
  const [supportedFeatures, setSupportedFeatures] = useState<Record<string, string[]> | null>(null);
  const { token } = useAuth();

  useEffect(() => {
    if (token) {
      fetchSupportedFeatures(token)
        .then(data => setSupportedFeatures(data))
        .catch(error => console.error("Failed to fetch supported features:", error));
    }
  }, [token]);

  return (
    <ConfigContext.Provider value={{ supportedFeatures }}>
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