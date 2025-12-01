import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Button, Container, Row, Col, Alert, Spinner } from 'react-bootstrap';
import { useAuth } from '../hooks/useAuth';
import { isTokenExpired } from '../utils/authUtils';
import { API_BASE_URL } from '../api';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, token, isLoading } = useAuth();

  const navigate = useNavigate();

  useEffect(() => {
    if (token && !isTokenExpired(token)) {
      // Check if there's a saved redirect URL
      const redirectUrl = localStorage.getItem('redirectAfterLogin');
      if (redirectUrl) {
        localStorage.removeItem('redirectAfterLogin');
        navigate(redirectUrl);
      } else {
        navigate('/dashboard');
      }
    }
  }, [token, navigate]);

  // Show loading state while authentication is being checked
  if (isLoading) {
    return <div>Loading...</div>;
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      login(data.access_token);
      
      // Check if there's a saved redirect URL
      const redirectUrl = localStorage.getItem('redirectAfterLogin');
      if (redirectUrl) {
        localStorage.removeItem('redirectAfterLogin');
        navigate(redirectUrl);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError('Invalid username or password');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container fluid>
      <Row className="justify-content-md-center mt-5">
        <Col xs={12} md={6}>
          <h2>Login</h2>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form onSubmit={handleLogin}>
            <Form.Group className="mb-3" controlId="formBasicEmail">
              <Form.Label>Username</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isSubmitting}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formBasicPassword">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isSubmitting}
              />
            </Form.Group>
            <Button 
              variant="primary" 
              type="submit" 
              className="w-100" 
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Spinner
                    as="span"
                    animation="border"
                    size="sm"
                    role="status"
                    aria-hidden="true"
                  />{' '}
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </Button>
          </Form>
        </Col>
      </Row>
    </Container>
  );
};

export default LoginPage;