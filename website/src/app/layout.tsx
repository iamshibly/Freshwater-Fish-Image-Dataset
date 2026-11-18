import type { Metadata, Viewport } from "next";
import { Fraunces, Inter, JetBrains_Mono } from "next/font/google";
import { site } from "@/data/site";
import "./globals.css";

const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-fraunces", display: "swap" });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

const description =
  "23 small indigenous freshwater fish species from Bangladesh: 5,520 raw images, 19,868 augmented images and per-100 g nutritional metadata, with nested cross-validation and open code.";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://nutrifish-bd.vercel.app"),
  title: `${site.name} — ${site.tagline}`,
  description,
  openGraph: {
    title: `${site.name} — Freshwater fish images + nutrition for Bangladesh`,
    description,
    images: [{ url: "/og.jpg", width: 1200, height: 630 }],
    type: "website",
  },
  twitter: { card: "summary_large_image", images: ["/og.jpg"] },
};
export const viewport: Viewport = { themeColor: "#04141a" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${inter.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
