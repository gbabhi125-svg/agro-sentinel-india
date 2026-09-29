import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ThemeProvider } from "@/lib/theme";
import { I18nProvider } from "@/lib/i18n";
import BottomNav from "@/components/BottomNav";

export const metadata: Metadata = {
  title: "AgroSentinel",
  description: "Photo-based crop diagnosis and farm advisory for Indian farmers",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <I18nProvider>
            {children}
            <BottomNav />
          </I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
