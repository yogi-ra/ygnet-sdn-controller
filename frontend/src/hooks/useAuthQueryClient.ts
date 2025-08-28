import { QueryClient } from "@tanstack/react-query";
import { useAuth } from "./useAuth";
import { UnauthorizedError } from "../api";
import { useNavigate } from "react-router-dom";

export const useAuthQueryClient = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        onError: (error) => {
          if (error instanceof UnauthorizedError) {
            logout();
            navigate("/login");
          }
        },
      },
      mutations: {
        onError: (error) => {
          if (error instanceof UnauthorizedError) {
            logout();
            navigate("/login");
          }
        },
      },
    },
  });

  return queryClient;
};