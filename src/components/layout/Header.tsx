// =============================================================================
// components/layout/Header.tsx — Fixed navigation bar.
// Clean, minimal SaaS style. No auth buttons — ViralCut is fully anonymous.
// =============================================================================
"use client";

import Link from "next/link";
import { Zap, BookOpen } from "lucide-react";

export default function Header() {
  return (
    <header
      className="
        fixed top-0 left-0 right-0 z-50
        border-b border-white/[0.06]
        glass
      "
      role="banner"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">

          {/* ── Logo ── */}
          <Link
            href="/"
            className="flex items-center gap-2.5 group"
            aria-label="ViralCut home"
          >
            {/* Animated icon badge */}
            <span
              className="
                flex h-8 w-8 items-center justify-center rounded-lg
                gradient-cta shadow-lg shadow-violet-900/30
              "
            >
              <Zap className="h-4 w-4 text-white" strokeWidth={2.5} />
            </span>

            <span className="text-lg font-bold tracking-tight leading-none">
              {/* "Viral" in gradient, "Cut" plain */}
              <span className="gradient-text">Viral</span>
              <span className="text-white">Cut</span>
            </span>
          </Link>

          {/* ── Right nav ── */}
          <nav className="flex items-center gap-1 sm:gap-2" aria-label="Main navigation">
            {/* "How it works" smooth-scroll anchor */}
            <a
              href="#how-it-works"
              className="
                hidden sm:inline-flex items-center gap-1.5
                rounded-lg px-3 py-2 text-sm font-medium
                text-white/60 hover:text-white hover:bg-white/[0.06]
                transition-all duration-200
              "
            >
              <BookOpen className="h-3.5 w-3.5" />
              How it works
            </a>

            {/* GitHub link */}
            <a
              href="https://github.com/viralcut"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="ViralCut on GitHub"
              className="
                flex items-center gap-1.5
                rounded-lg px-3 py-2 text-sm font-medium
                text-white/60 hover:text-white hover:bg-white/[0.06]
                transition-all duration-200
              "
            >
              <svg
                viewBox="0 0 24 24"
                width="16"
                height="16"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
                className="h-4 w-4"
              >
                <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
                <path d="M9 18c-4.51 2-5-2-7-2" />
              </svg>
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
