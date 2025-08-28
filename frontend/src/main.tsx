import 'bootstrap/dist/css/bootstrap.min.css';
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ConfigProvider } from './context/ConfigContext.tsx';
import { AuthProvider } from './context/AuthContext.tsx';

const root = createRoot(document.getElementById('root')!); // Define root outside render
root.render(
  <StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </StrictMode>,
);

function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ConfigProvider>
        {children}
      </ConfigProvider>
    </AuthProvider>
  );
}