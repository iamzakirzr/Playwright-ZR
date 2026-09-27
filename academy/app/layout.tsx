import type { Metadata } from "next";
import { JetBrains_Mono, Syne } from "next/font/google";
import "./globals.css";

const display = Syne({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const code = JetBrains_Mono({
  variable: "--font-code",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: {
    default: "AI QA Academy",
    template: "%s · AI QA Academy",
  },
  description:
    "Learn how AI works by testing it — LLMs, RAG, agents, and MCP from the Playwright-ZR Python QA framework.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  return (
    <html lang="en" className="dark">
      <body className={`${display.variable} ${code.variable} antialiased`}>{children}</body>
    </html>
  );
}
