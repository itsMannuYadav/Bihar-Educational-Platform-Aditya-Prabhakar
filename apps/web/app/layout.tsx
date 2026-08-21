import type { Metadata } from "next";
import { Baloo_2, Hind } from "next/font/google";
import "./globals.css";

import { OfflineBanner } from "@/components/layout/OfflineBanner";

const baloo2 = Baloo_2({
  variable: "--font-display",
  subsets: ["latin", "devanagari"],
  weight: ["600", "700", "800"],
});

const hind = Hind({
  variable: "--font-body",
  subsets: ["latin", "devanagari"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Shiksha Sathi — शिक्षा सारथी",
  description: "AI teaching companion for Bihar's government-school teachers. BSEB-aligned lesson plans, worksheets, mind maps and audio — in Hindi.",
  manifest: "/manifest.json",
  themeColor: "#E56010",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Shiksha Sathi",
  },
};

// Every route here is session-dependent (auth pages are client-only and
// interactive, dashboard pages read the signed-in user's data) — nothing
// benefits from static generation, so opt the whole app out at the root
// rather than remembering this per page.
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="hi"
      className={`${baloo2.variable} ${hind.variable} h-full antialiased`}
    >
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#E56010" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js').catch(function() {});
                });
              }
            `,
          }}
        />
      </head>
      <body className="font-body flex min-h-full flex-col">
        <OfflineBanner />
        {children}
      </body>
    </html>
  );
}
