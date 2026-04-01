import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "MIRA Stylist",
  description: "A premium AI styling experience for trying on looks, hearing editorial guidance, and building a personal wardrobe.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
  themeColor: "#f7f1e8",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-mira-cream mira-shell-pad">
        {children}
      </body>
    </html>
  );
}
