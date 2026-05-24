import type { Metadata } from "next";
import { ReactNode } from "react";
import { Providers } from "./providers";
import { Shell } from "@/components/shell/Shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "TrustOps Assessment Console",
  description:
    "Continuous compliance assessment for security data lakes — SOC 2, NIST AI RMF, and beyond.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Shell>{children}</Shell>
        </Providers>
        <script
          id="app-data"
          type="application/json"
          // dashboard.py replaces this with the live assessment payload when
          // generating a static console.html for offline/audit distribution.
          dangerouslySetInnerHTML={{ __html: "{}" }}
        />
      </body>
    </html>
  );
}
