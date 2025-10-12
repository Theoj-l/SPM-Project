import { Toaster } from "@/components/ui/sonner";
import Navigation from "@/components/navigation";
import ProtectedRoute from "@/components/ProtectedRoute";
import { AuthProvider } from "@/contexts/AuthContext";
import "@/utils/auth-utils"; // Import auth utilities for console debugging
import "@/utils/role-utils"; // Import role utilities for console debugging
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Jite",
  description: "Your personal & team task manager",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          <ProtectedRoute>
            <Navigation>{children}</Navigation>
          </ProtectedRoute>
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  );
}
