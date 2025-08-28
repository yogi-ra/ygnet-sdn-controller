import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { useAuthQueryClient } from '../hooks/useAuthQueryClient';

interface AuthQueryClientProviderWrapperProps {
  children: React.ReactNode;
}

const AuthQueryClientProviderWrapper: React.FC<AuthQueryClientProviderWrapperProps> = ({ children }) => {
  const queryClient = useAuthQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

export default AuthQueryClientProviderWrapper;
