"use client";

import { create } from "zustand";

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
  initialize: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  isAuthenticated: false,

  login: (token: string) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("auto_ads_token", token);
    }
    set({ token, isAuthenticated: true });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auto_ads_token");
    }
    set({ token: null, isAuthenticated: false });
  },

  initialize: () => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("auto_ads_token");
      if (token) {
        set({ token, isAuthenticated: true });
      }
    }
  },
}));