import React, { useEffect } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../hooks/useAuthQueryClient'; // Import the global queryClient
import { useAuth } from '../hooks/useAuth';
import { UnauthorizedError } from '../api';
import { useNavigate } from 'react-router-dom';

interface AuthQueryClientProviderWrapperProps {
  children: React.ReactNode;
}

const AuthQueryClientProviderWrapper: React.FC<AuthQueryClientProviderWrapperProps> = ({ children }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const unsubscribeQueryError = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'queryError' && event.query.state.error instanceof UnauthorizedError) {
        logout();
        navigate("/login");
      }
    });

    const unsubscribeMutationError = queryClient.getMutationCache().subscribe((event) => {
      if (event.type === 'mutationError' && event.mutation.state.error instanceof UnauthorizedError) {
        logout();
        navigate("/login");
      }
    });

    return () => {
      unsubscribeQueryError();
      unsubscribeMutationError();
    };
  }, [logout, navigate]);

  console.log('AuthQueryClientProviderWrapper - queryClient:', queryClient);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

export default AuthQueryClientProviderWrapper;
