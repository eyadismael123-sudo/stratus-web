import type { Metadata } from "next";
import "./globals.css";
import { CustomCursor } from "../components/effects/CustomCursor";
import { ScrollProgress } from "../components/effects/ScrollProgress";

export const metadata: Metadata = {
  title: "Stratus — Hire your first AI employee",
  description:
    "Hiring your next team member just got a lot simpler. AI agents for your business — hire, watch, grow.",
  keywords: ["AI agents", "automation", "business", "LinkedIn", "AI employees"],
  openGraph: {
    title: "Stratus — Hire your first AI employee",
    description: "Hiring your next team member just got a lot simpler. AI agents for your business.",
    siteName: "Stratus",
    locale: "en_AE",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <head>
        <link
          href="https://api.fontshare.com/v2/css?f[]=clash-display@700,600&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://api.fontshare.com/v2/css?f[]=satoshi@900,700,500,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col antialiased">
        <ScrollProgress />
        <CustomCursor />
        {children}
      </body>
    </html>
  );
}
