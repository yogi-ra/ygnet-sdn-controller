import React, { createContext, useContext, ReactNode } from 'react';

// Define theme configuration
interface ThemeConfig {
  name: string;
  primaryColor: string;
  secondaryColor: string;
  backgroundColor: string;
  textColor: string;
  borderColor: string;
  buttonStyle: 'primary' | 'secondary' | 'outline';
  cardStyle: 'light' | 'dark' | 'custom';
}

// Create context for theme management
interface FeatureThemeContextType {
  themes: Record<string, ThemeConfig>;
  getTheme: (themeName: string) => ThemeConfig | undefined;
  applyTheme: (themeName: string, element: HTMLElement) => void;
}

const FeatureThemeContext = createContext<FeatureThemeContextType | undefined>(undefined);

// Provider component
export const FeatureThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Initial theme configurations
  const initialThemes: Record<string, ThemeConfig> = {
    'default': {
      name: 'default',
      primaryColor: '#007bff',
      secondaryColor: '#6c757d',
      backgroundColor: '#ffffff',
      textColor: '#212529',
      borderColor: '#dee2e6',
      buttonStyle: 'primary',
      cardStyle: 'light',
    },
    'cisco': {
      name: 'cisco',
      primaryColor: '#00bceb',
      secondaryColor: '#6c757d',
      backgroundColor: '#f8f9fa',
      textColor: '#212529',
      borderColor: '#00bceb',
      buttonStyle: 'primary',
      cardStyle: 'light',
    },
    'dark': {
      name: 'dark',
      primaryColor: '#0d6efd',
      secondaryColor: '#6c757d',
      backgroundColor: '#212529',
      textColor: '#f8f9fa',
      borderColor: '#495057',
      buttonStyle: 'outline',
      cardStyle: 'dark',
    },
  };

  // State for themes
  const [themes] = React.useState<Record<string, ThemeConfig>>(initialThemes);

  // Get theme configuration
  const getTheme = (themeName: string): ThemeConfig | undefined => {
    return themes[themeName];
  };

  // Apply theme to an element
  const applyTheme = (themeName: string, element: HTMLElement) => {
    const theme = getTheme(themeName);
    if (!theme) return;

    element.style.setProperty('--bs-primary', theme.primaryColor);
    element.style.setProperty('--bs-secondary', theme.secondaryColor);
    element.style.setProperty('--bs-body-bg', theme.backgroundColor);
    element.style.setProperty('--bs-body-color', theme.textColor);
    element.style.setProperty('--bs-border-color', theme.borderColor);
  };

  return (
    <FeatureThemeContext.Provider value={{ themes, getTheme, applyTheme }}>
      {children}
    </FeatureThemeContext.Provider>
  );
};

// Hook to use the feature theme
export const useFeatureTheme = () => {
  const context = useContext(FeatureThemeContext);
  if (!context) {
    throw new Error('useFeatureTheme must be used within a FeatureThemeProvider');
  }
  return context;
};

// Component to apply theme to a specific element
export const ApplyTheme: React.FC<{ themeName: string; children: ReactNode }> = ({ 
  themeName, 
  children 
}) => {
  const { applyTheme } = useFeatureTheme();
  const elementRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (elementRef.current) {
      applyTheme(themeName, elementRef.current);
    }
  }, [themeName, applyTheme]);

  return <div ref={elementRef}>{children}</div>;
};