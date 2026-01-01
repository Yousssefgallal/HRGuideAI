"use client";

import { createContext, useContext, useState, ReactNode, useEffect } from "react";

/**
 * User interface matching backend response from /auth/login endpoint
 */
export interface User {
  user_id: number;
  full_name: string;
  email: string;
  role_type: string;
  position_title: string;
  faculty_or_department: string;
  is_admin: boolean;
}

interface AuthContextType {
  user: User | null;
  signIn: (userData: User) => void;
  signOut: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "giu_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem(STORAGE_KEY);
    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser) as User;
        setUser(parsedUser);
        console.log("✅ User loaded from localStorage:", parsedUser);
      } catch (error) {
        console.error("❌ Failed to parse stored user:", error);
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setIsInitialized(true);
  }, []);

  const signIn = (userData: User) => {
    console.log("✅ Signing in user:", userData);
    setUser(userData);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));

    // Trigger storage event for other components (like CopilotProvider)
    window.dispatchEvent(new Event("storage"));
  };

  const signOut = () => {
    console.log("✅ Signing out user");
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);

    document.cookie = "user_id=; Max-Age=0; path=/;";

    // Trigger storage event
    window.dispatchEvent(new Event("storage"));
  };

  // Don't render children until we've checked localStorage
  if (!isInitialized) {
    return null;
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        signIn,
        signOut,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
