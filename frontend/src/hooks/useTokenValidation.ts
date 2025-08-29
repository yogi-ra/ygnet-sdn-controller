import { useEffect } from 'react';
import { useAuth } from './useAuth';
import { isTokenExpired } from '../utils/authUtils';

// Custom hook to validate token and logout if expired
const useTokenValidation = () => {
  const { token, logout } = useAuth();

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (token) {
      // Check token immediately
      if (isTokenExpired(token)) {
        logout();
      } else {
        // Set up interval to check token every minute
        intervalId = setInterval(() => {
          if (isTokenExpired(token)) {
            logout();
          }
        }, 60000); // Check every minute
      }
    }

    // Clean up interval on unmount or when token changes
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [token, logout]);

  return null;
};

export default useTokenValidation;
