// Utility function to check if a JWT token is expired
export const isTokenExpired = (token: string | null): boolean => {
  if (!token) return true;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expiry = payload.exp;
    return Math.floor(Date.now() / 1000) >= expiry;
  } catch (e) {
    // If we can't parse the token, consider it expired
    return true;
  }
};
