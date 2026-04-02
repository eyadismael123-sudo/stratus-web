import type { Metadata } from "next";
import "./globals.css";

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
        {/* Clash Display — display/headline font (Fontshare) */}
        <link
          href="https://api.fontshare.com/v2/css?f[]=clash-display@700,600&display=swap"
          rel="stylesheet"
        />
        {/* Satoshi — body/UI font (Fontshare) */}
        <link
          href="https://api.fontshare.com/v2/css?f[]=satoshi@900,700,500,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col antialiased">
        {children}
      </body>
    </html>
  );
}
