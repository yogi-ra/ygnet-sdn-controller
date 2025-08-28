import React, { createContext, useContext, ReactNode } from 'react';
import { FeatureType } from '../types/featureTypes';
import ToggleFeature from './features/ToggleFeature';
import TextInputFeature from './features/TextInputFeature';
import DisplayTableFeature from './features/DisplayTableFeature';
import DisplayTextFeature from './features/DisplayTextFeature';
import SelectOptionFeature from './features/SelectOptionFeature';
import ButtonFeature from './features/ButtonFeature';

// Define the structure for feature component registration
interface FeatureComponentRegistration {
  type: FeatureType;
  component: React.ComponentType<any>;
  name: string;
}

// Create context for feature component registry
interface FeatureComponentRegistryContextType {
  components: Record<string, FeatureComponentRegistration>;
  getComponent: (featureType: FeatureType) => React.ComponentType<any> | undefined;
  registerComponent: (registration: FeatureComponentRegistration) => void;
}

const FeatureComponentRegistryContext = createContext<FeatureComponentRegistryContextType | undefined>(undefined);

// Provider component
export const FeatureComponentRegistryProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Initial feature component registrations
  const initialComponents: Record<string, FeatureComponentRegistration> = {
    [FeatureType.TOGGLE]: {
      type: FeatureType.TOGGLE,
      component: ToggleFeature,
      name: 'ToggleFeature'
    },
    [FeatureType.INPUT_TEXT]: {
      type: FeatureType.INPUT_TEXT,
      component: TextInputFeature,
      name: 'TextInputFeature'
    },
    [FeatureType.DISPLAY_TABLE]: {
      type: FeatureType.DISPLAY_TABLE,
      component: DisplayTableFeature,
      name: 'DisplayTableFeature'
    },
    [FeatureType.DISPLAY_TEXT]: {
      type: FeatureType.DISPLAY_TEXT,
      component: DisplayTextFeature,
      name: 'DisplayTextFeature'
    },
    [FeatureType.SELECT_OPTION]: {
      type: FeatureType.SELECT_OPTION,
      component: SelectOptionFeature,
      name: 'SelectOptionFeature'
    },
    [FeatureType.BUTTON]: {
      type: FeatureType.BUTTON,
      component: ButtonFeature,
      name: 'ButtonFeature'
    },
  };

  // State for components
  const [components, setComponents] = React.useState<Record<string, FeatureComponentRegistration>>(initialComponents);

  // Get component for a feature type
  const getComponent = (featureType: FeatureType): React.ComponentType<any> | undefined => {
    return components[featureType]?.component;
  };

  // Register a new feature component
  const registerComponent = (registration: FeatureComponentRegistration) => {
    setComponents(prev => ({
      ...prev,
      [registration.type]: registration
    }));
  };

  return (
    <FeatureComponentRegistryContext.Provider value={{ 
      components, 
      getComponent, 
      registerComponent 
    }}>
      {children}
    </FeatureComponentRegistryContext.Provider>
  );
};

// Hook to use the feature component registry
export const useFeatureComponentRegistry = () => {
  const context = useContext(FeatureComponentRegistryContext);
  if (!context) {
    throw new Error('useFeatureComponentRegistry must be used within a FeatureComponentRegistryProvider');
  }
  return context;
};

// Component to register a new feature component
export const RegisterFeatureComponent: React.FC<{ 
  registration: FeatureComponentRegistration 
}> = ({ registration }) => {
  const { registerComponent } = useFeatureComponentRegistry();
  
  React.useEffect(() => {
    registerComponent(registration);
  }, [registration, registerComponent]);
  
  return null; // This component doesn't render anything
};