import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import AuthProvider from "@/components/AuthProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ReefGPT",
  description: "AI-Powered Reef Tank Assistant",
};

import type { Viewport } from 'next';
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

import { ChatProvider } from "@/context/ChatContext";
import GlobalChatDrawer from "@/components/GlobalChatDrawer";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-[100dvh] md:h-[100dvh] w-full bg-slate-950 flex flex-col md:overflow-hidden overflow-x-hidden`}
      >
        <AuthProvider>
          <ChatProvider>
            <Navbar />
            <main className="flex-1 md:overflow-hidden relative">
              {children}
            </main>
            <GlobalChatDrawer />
          </ChatProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
