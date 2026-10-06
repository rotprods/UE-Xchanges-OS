import type { Metadata } from "next";
import { Orbitron, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import ClientLayout from "./ClientLayout";
import LevelUpOverlay from "@/components/dom/LevelUpOverlay";
import { Analytics } from "@vercel/analytics/next";

const orbitron = Orbitron({
  variable: "--font-orbitron",
  subsets: ["latin"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Chronos Quantum | Real-Time Crypto Intelligence Terminal",
  description:
    "Institutional-grade trading terminal with AI pattern detection, on-chain whale tracking, 3D volatility surfaces, and autonomous trading. Real-time data from Binance, Deribit, and Ethereum.",
  keywords: [
    "crypto",
    "trading",
    "terminal",
    "bitcoin",
    "AI",
    "quantitative",
    "on-chain",
    "derivatives",
  ],
  authors: [{ name: "Chronos Quantum" }],
  openGraph: {
    title: "Chronos Quantum | Crypto Intelligence Terminal",
    description:
      "AI-powered trading terminal with real-time on-chain analytics, 3D visualization, and autonomous execution.",
    type: "website",
    locale: "en_US",
    siteName: "Chronos Quantum",
  },
  twitter: {
    card: "summary_large_image",
    title: "Chronos Quantum",
    description: "Institutional-grade crypto intelligence terminal",
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport = {
  themeColor: "#05050A",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth" data-scroll-behavior="smooth">
      <body
        className={`${orbitron.variable} ${inter.variable} ${jetbrainsMono.variable} bg-[#05050A] text-white font-sans antialiased overflow-x-hidden`}
      >
        <ClientLayout>{children}</ClientLayout>
        <LevelUpOverlay />
        <Analytics />
      </body>
    </html>
  );
}
