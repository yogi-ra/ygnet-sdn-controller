import { Container, Navbar, Nav } from 'react-bootstrap';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DeviceListPage from './pages/DeviceListPage';
import AddDevicePage from './pages/AddDevicePage';
import DeviceDetailPage from './pages/DeviceDetailPage';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './hooks/useAuth';
import EditDevicePage from './pages/EditDevicePage';

import DeviceFeaturesPage from './pages/DeviceFeaturesPage';

import FeatureOutputPage from './pages/FeatureOutputPage';
import { QueryClientProvider } from '@tanstack/react-query';
import { useAuthQueryClient } from './hooks/useAuthQueryClient';
import AuthQueryClientProviderWrapper from './components/AuthQueryClientProviderWrapper';

const MainLayout = () => {
  const { token, logout } = useAuth();

  return (
    <>
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container fluid>
          <Navbar.Brand href="/">{import.meta.env.VITE_PROJECT_NAME}</Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="me-auto">
              <Nav.Link href="/dashboard">Dashboard</Nav.Link>
              <Nav.Link href="/devices">Devices</Nav.Link>
              {token ? (
                <Nav.Link onClick={logout}>Logout</Nav.Link>
              ) : (
                <Nav.Link href="/login">Login</Nav.Link>
              )}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
      <Container fluid className="p-3">
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/devices"
            element={
              <ProtectedRoute>
                <DeviceListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/devices/add"
            element={
              <ProtectedRoute>
                <AddDevicePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/devices/:id"
            element={
              <ProtectedRoute>
                <DeviceDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/devices/edit/:id"
            element={
              <ProtectedRoute>
                <EditDevicePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/devices/:id/features"
            element={
              <ProtectedRoute>
                <DeviceFeaturesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/devices/:id/features/:featureName"
            element={
              <ProtectedRoute>
                <FeatureOutputPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Container>
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AuthQueryClientProviderWrapper>
          <MainLayout />
        </AuthQueryClientProviderWrapper>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;