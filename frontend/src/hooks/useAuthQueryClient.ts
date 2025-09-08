import { QueryClient } from "@tanstack/react-query";

// Create the QueryClient instance once globally
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3, // Default retries
    },
    mutations: {}, // Re-adding an empty mutations object to satisfy useMutation
  },
});