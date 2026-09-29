"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

type User = { id: string; name: string; username: string };

type AuthState = {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (name: string, username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
});

function saveToken(token: string) {
  try {
    localStorage.setItem("agrosentinel_token", token);
  } catch {
    // ignore
  }
}

function clearToken() {
  try {
    localStorage.removeItem("agrosentinel_token");
  } catch {
    // ignore
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let token: string | null = null;
    try {
      token = localStorage.getItem("agrosentinel_token");
    } catch {
      // ignore
    }
    if (!token) {
      setLoading(false);
      return;
    }
    api.me().then(setUser).catch(() => clearToken()).finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const res = await api.login(username, password);
    saveToken(res.access_token);
    setUser(await api.me());
  };

  const register = async (name: string, username: string, password: string) => {
    const res = await api.register(name, username, password);
    saveToken(res.access_token);
    setUser(await api.me());
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
