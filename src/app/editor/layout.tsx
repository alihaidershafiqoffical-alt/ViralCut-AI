import { Suspense } from "react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Shorts Editor",
  description:
    "Fine-tune your AI-generated Shorts with trim controls, caption styling, and vertical positioning before downloading.",
  robots: {
    index: false,
    follow: false,
  },
  alternates: {
    canonical: "/editor",
  },
};

export default function EditorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0a0b12] text-white flex items-center justify-center">Loading Editor...</div>}>
      {children}
    </Suspense>
  );
}
