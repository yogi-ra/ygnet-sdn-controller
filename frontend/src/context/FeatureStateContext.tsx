
import React, { createContext, useState, useContext, ReactNode } from 'react';
import { type FeatureSchema } from '../types/featureTypes';

type FeatureState = {
  [key: string]: any;
};

type FeatureStateContextType = {
  featureState: FeatureState;
  setFeatureState: React.Dispatch<React.SetStateAction<FeatureState>>;
};

const FeatureStateContext = createContext<FeatureStateContextType | undefined>(undefined);

export const FeatureStateProvider = ({ children, features }: { children: ReactNode, features: FeatureSchema[] }) => {
  const initial_state = features.reduce((acc, feature) => {
    acc[feature.name] = feature.default_value;
    return acc;
  }, {} as FeatureState);

  const [featureState, setFeatureState] = useState<FeatureState>(initial_state);

  return (
    <FeatureStateContext.Provider value={{ featureState, setFeatureState }}>
      {children}
    </FeatureStateContext.Provider>
  );
};

export const useFeatureState = () => {
  const context = useContext(FeatureStateContext);
  if (context === undefined) {
    throw new Error('useFeatureState must be used within a FeatureStateProvider');
  }
  return context;
};
