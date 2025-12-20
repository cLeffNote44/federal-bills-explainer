'use client';

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { api } from '@/lib/api';

export interface User {
  id: string;
  email: string;
  display_name?: string;
  preferences?: Record<string, unknown>;
  email_notifications: boolean;
  notification_frequency: string;
  zip_code?: string;
  state?: string;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'fbx-auth-token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Generate a session ID for anonymous feedback
  useEffect(() => {
    if (!localStorage.getItem('fbx-session-id')) {
      localStorage.setItem('fbx-session-id', crypto.randomUUID());
    }
  }, []);

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const userData = await api.get('auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      }).json<User>();
      setUser(userData);
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    const response = await api.post('auth/login', {
      json: { email, password },
    }).json<{ access_token: string; user: User }>();

    localStorage.setItem(TOKEN_KEY, response.access_token);
    setUser(response.user);
  };

  const register = async (email: string, password: string, displayName?: string) => {
    const response = await api.post('auth/register', {
      json: { email, password, display_name: displayName },
    }).json<{ access_token: string; user: User }>();

    localStorage.setItem(TOKEN_KEY, response.access_token);
    setUser(response.user);
  };

  const logout = async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      try {
        await api.post('auth/logout', {
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // Ignore logout errors
      }
    }
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  };

  const updateProfile = async (data: Partial<User>) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) throw new Error('Not authenticated');

    const updated = await api.patch('auth/profile', {
      headers: { Authorization: `Bearer ${token}` },
      json: data,
    }).json<User>();

    setUser(updated);
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateProfile,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Helper to get auth token
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

// Helper to get session ID for anonymous users
export function getSessionId(): string {
  if (typeof window === 'undefined') return '';
  let sessionId = localStorage.getItem('fbx-session-id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('fbx-session-id', sessionId);
  }
  return sessionId;
}
