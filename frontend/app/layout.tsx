import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";

import { AuthProvider } from "@/lib/auth-context";
import { CopilotKit } from "@copilotkit/react-core";
import { ThemeProvider } from "@/components/theme-provider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GIU HR Assistant",
  description: "Ask questions about GIU Administrative Policies",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {/* client providers are allowed inside a server component */}
          <AuthProvider>
            <CopilotKit runtimeUrl="/api/copilotkit" agent="policy_qa_agent">
              {children}
            </CopilotKit>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
