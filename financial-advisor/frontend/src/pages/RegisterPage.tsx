import { Box, Button, Text, useToast } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import type { FormEvent } from 'react';
import captrionLogo from '../../logo/logo_C.png';

const EyeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);
const EyeOffIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 7 11 7a13.16 13.16 0 0 1-1.67 2.68M6.61 6.61C3.35 8.56 1 12 1 12s4 7 11 7a9.26 9.26 0 0 0 5.39-1.61M14.12 14.12a3 3 0 1 1-4.24-4.24" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </svg>
);

const RegisterPage = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast({ title: 'Please fill in all fields', status: 'error', duration: 3000, isClosable: true });
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      toast({ title: 'Enter a valid email address', status: 'error', duration: 3000, isClosable: true });
      return;
    }
    if (password.length < 8) {
      toast({ title: 'Your password must be at least 8 characters', status: 'error', duration: 3000, isClosable: true });
      return;
    }

    setLoading(true);
    try {
      await register(email, password);
      toast({ title: 'Registration successful', status: 'success', duration: 3000, isClosable: true });
      navigate('/login');
    } catch (error: any) {
      toast({ title: error.message || 'Registration failed', status: 'error', duration: 3000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box className="auth-shell">
      <Box className="auth-visual">
        <Box className="auth-core">
          <Box className="auth-core-ring r1" />
          <Box className="auth-core-ring r2" />
          <Box className="auth-core-ring r3" />
          <Box className="auth-core-ticks" />
          <Box className="auth-core-hub">
            <Box className="auth-core-logo">
              <img src={captrionLogo} alt="Captrion" />
            </Box>
          </Box>
        </Box>
        <Text className="auth-visual-title">Set up your workspace</Text>
        <Text className="auth-visual-sub">
          Create an account and let your agentic advisor start tracking your portfolio and answering in real time.
        </Text>
        <Box className="auth-visual-tags">
          <span>Agentic AI</span>
          <span>Live markets</span>
          <span>Voice ready</span>
        </Box>
      </Box>

      <Box className="auth-form-panel">
        <Box className="auth-form-inner">
          <Text className="auth-form-eyebrow">Secure access</Text>
          <Text className="auth-form-title">Create account</Text>
          <Text className="auth-form-sub">A few details and you're in.</Text>

          <form onSubmit={handleSubmit}>
            <Box className="auth-field">
              <label htmlFor="register-email">Email</label>
              <input
                id="register-email"
                className="auth-underline-input"
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </Box>
            <Box className="auth-field">
              <label htmlFor="register-password">Password</label>
              <Box className="auth-password-wrap">
                <input
                  id="register-password"
                  className="auth-underline-input"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="At least 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </Box>
            </Box>

            <Button
              className="auth-submit"
              bgGradient="linear(to-r, brand.500, brand.600)"
              color="white"
              _hover={{ bgGradient: 'linear(to-r, brand.400, brand.600)' }}
              isLoading={loading}
              type="submit"
            >
              Register
            </Button>
          </form>

          <Text className="auth-switch">
            Already have an account?{' '}
            <Text
              as="span"
              color="brand.300"
              cursor="pointer"
              fontWeight="semibold"
              onClick={() => navigate('/login')}
            >
              Login here
            </Text>
          </Text>
        </Box>
      </Box>
    </Box>
  );
};

export default RegisterPage;