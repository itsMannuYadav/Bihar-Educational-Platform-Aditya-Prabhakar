import type { Metadata } from "next";
import { Baloo_2, Hind } from "next/font/google";
import "./globals.css";

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
  title: "Shiksha Sathi",
  description: "AI teaching companion for Bihar's government-school teachers.",
};

// Every route here is session-dependent (auth pages are client-only and
// interactive, dashboard pages read the signed-in user's data) — nothing
// benefits from static generation, so opt the whole app out at the root
// rather than remembering this per page.
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${baloo2.variable} ${hind.variable} h-full antialiased`}
    >
      <body className="font-body flex min-h-full flex-col">{children}</body>
    </html>
  );
}
