import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthUser {
  username: string;
  role: 'ADMIN' | 'RESPONDER' | 'CITIZEN';
  responderId?: string;
  name?: string;
}

interface AuthContextType {
  token: string | null;
  user: AuthUser | null;
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('samanvay_token') || localStorage.getItem('raahat_token'));
  const [user, setUser] = useState<AuthUser | null>(() => {
    const saved = localStorage.getItem('samanvay_user') || localStorage.getItem('raahat_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (newToken: string, newUser: AuthUser) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('samanvay_token', newToken);
    localStorage.setItem('samanvay_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('samanvay_token');
    localStorage.removeItem('samanvay_user');
    localStorage.removeItem('raahat_token');
    localStorage.removeItem('raahat_user');
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
