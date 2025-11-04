import { Container, Navbar, Nav, Button } from "react-bootstrap";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import BackupPage from "./pages/BackupPage";
import SshPage from "./pages/SshPage.tsx";
import DeviceListPage from "./pages/DeviceListPage";
import AddDevicePage from "./pages/AddDevicePage";
import DeviceDetailPage from "./pages/DeviceDetailPage";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./hooks/useAuth";
import useTokenValidation from "./hooks/useTokenValidation";
import EditDevicePage from "./pages/EditDevicePage";

import { QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import AuthQueryClientProviderWrapper from "./components/AuthQueryClientProviderWrapper";
import { Toaster } from "react-hot-toast";

const MainLayout = () => {
  const { token, logout, isLoading } = useAuth();
  // Use the token validation hook
  useTokenValidation();

  // Show loading state while authentication is being checked
  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container fluid>
          <Navbar.Brand href="/">
            {import.meta.env.VITE_PROJECT_NAME}
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse id="basic-navbar-nav">
            <Nav className="me-auto">
              <Nav.Link href="/dashboard">Dashboard</Nav.Link>
              <Nav.Link href="/devices">Devices</Nav.Link>
              <Nav.Link href="/backup">Backup</Nav.Link>
              <Nav.Link href="/webssh">Web SSH</Nav.Link>
            </Nav>
            <Nav>
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
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/webssh"
            element={
              <ProtectedRoute>
                <SshPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/backup"
            element={
              <ProtectedRoute>
                <BackupPage />
              </ProtectedRoute>
            }
          />
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
          <Toaster />
          <MainLayout />
        </AuthQueryClientProviderWrapper>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

