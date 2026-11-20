import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "BuildAtlas — Research Smarter. Architect Better.", description: "Evidence-backed software project planning." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
