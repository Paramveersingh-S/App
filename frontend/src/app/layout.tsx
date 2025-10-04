import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { GoogleOAuthProvider } from '@react-oauth/google'; // 1. Import the Google provider
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// 2. Update metadata to be specific to the AURA project
export const metadata: Metadata = {
  title: "AURA - Your Air Quality Co-Pilot",
  description: "Predicting Cleaner, Safer Skies with NASA data.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // 3. Add your Google Client ID here
  // You must get this from the Google Cloud Console
  const googleClientId = "661777857775-7t6j9npuk7ogs61hq8d75gjpiurme92s.apps.googleusercontent.com";

  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {/* 4. Wrap the application with the GoogleOAuthProvider */}
        <GoogleOAuthProvider clientId={googleClientId}>
          {children}
        </GoogleOAuthProvider>
      </body>
    </html>
  );
}

