"use client";

import { useAuth } from "@/lib/auth-context";
import { LoginPage } from "@/components/login";
import { ChatInterface } from "@/components/chat-interface";

export default function Home() {
  const { isAuthenticated } = useAuth();

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Show chat interface if authenticated
  return <ChatInterface />;
}
