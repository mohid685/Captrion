import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  token: string;
}

interface AuthContextType {
  currentUser: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const getApiError = (error: unknown, fallback: string) => {
  if (!error || typeof error !== 'object') return fallback;
  const payload = error as { detail?: unknown; message?: string };
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join('. ') || fallback;
  }
  return payload.message || fallback;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('captrion_token');
    const userJson = localStorage.getItem('captrion_user');

    if (token && userJson) {
      try {
        const user = JSON.parse(userJson);
        setCurrentUser({
          id: user.id,
          email: user.email,
          token,
        });
      } catch (e) {
        localStorage.removeItem('captrion_token');
        localStorage.removeItem('captrion_user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(getApiError(error, 'Login failed'));
    }

    const data = await response.json();
    const { access_token: token } = data;

    const user = { id: Date.now().toString(), email, token };

    setCurrentUser(user);
    localStorage.setItem('captrion_token', token);
    localStorage.setItem('captrion_user', JSON.stringify({ id: user.id, email }));
  };

  const register = async (email: string, password: string) => {
    const response = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(getApiError(error, 'Registration failed'));
    }

    const data = await response.json();
    const { access_token: token } = data;

    const user = { id: Date.now().toString(), email, token };

    setCurrentUser(user);
    localStorage.setItem('captrion_token', token);
    localStorage.setItem('captrion_user', JSON.stringify({ id: user.id, email }));
  };

  const logout = () => {
    setCurrentUser(null);
    localStorage.removeItem('captrion_token');
    localStorage.removeItem('captrion_user');
  };

  return (
    <AuthContext.Provider value={{ currentUser, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
