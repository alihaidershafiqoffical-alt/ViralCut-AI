"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Zap, Cookie, X } from "lucide-react";

export default function Footer() {
  const year = new Date().getFullYear();
  const [showConsent, setShowConsent] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      const consent = localStorage.getItem("viralcut-cookie-consent");
      if (!consent) {
        setShowConsent(true);
      }
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const handleAccept = () => {
    localStorage.setItem("viralcut-cookie-consent", "accepted");
    setShowConsent(false);
  };

  const handleDecline = () => {
    localStorage.setItem("viralcut-cookie-consent", "essential_only");
    setShowConsent(false);
  };

  return (
    <>
      <footer
        className="border-t border-white/[0.06] py-12 mt-24"
        role="contentinfo"
      >
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          {/* Top footer row with tools & use cases links */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-8 mb-8 border-b border-white/[0.04]">
            <div className="flex flex-col gap-3">
              <Link href="/" className="flex items-center gap-2" aria-label="ViralCut">
                <span className="flex h-6 w-6 items-center justify-center rounded-md gradient-cta">
                  <Zap className="h-3 w-3 text-white" strokeWidth={2.5} />
                </span>
                <span className="text-sm font-bold">
                  <span className="gradient-text">Viral</span>
                  <span className="text-white">Cut</span>
                </span>
              </Link>
              <p className="text-xs text-white/40 leading-relaxed max-w-xs">
                AI-powered video clipping and automatic captions. Turn long-form recordings into viral short clips with zero watermark.
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <span className="text-xs font-semibold text-white/80 uppercase tracking-wider">Features</span>
              <Link href="/automatic-caption-generator" className="text-xs text-white/40 hover:text-white/70 transition-colors">
                Automatic Caption Generator
              </Link>
              <Link href="/long-video-to-shorts" className="text-xs text-white/40 hover:text-white/70 transition-colors">
                Long Video to Shorts AI
              </Link>
            </div>

            <div className="flex flex-col gap-2">
              <span className="text-xs font-semibold text-white/80 uppercase tracking-wider">Use Cases</span>
              <Link href="/podcast-to-shorts" className="text-xs text-white/40 hover:text-white/70 transition-colors">
                Podcast to Shorts
              </Link>
              <Link href="/youtube-shorts-generator" className="text-xs text-white/40 hover:text-white/70 transition-colors">
                YouTube Shorts Generator
              </Link>
            </div>
          </div>

          {/* Bottom footer row */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <nav className="flex items-center gap-5" aria-label="Footer navigation">
              <Link
                href="/privacy"
                className="text-xs text-white/40 hover:text-white/70 transition-colors"
              >
                Privacy Policy
              </Link>
              <Link
                href="/terms"
                className="text-xs text-white/40 hover:text-white/70 transition-colors"
              >
                Terms of Service
              </Link>
            </nav>

            <p className="text-xs text-white/30">
              © {year} ViralCut. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

      {/* Floating, Non-intrusive Cookie & Privacy Consent Banner */}
      {showConsent && (
        <aside
          aria-label="Cookie and Privacy Consent"
          className="fixed bottom-4 sm:bottom-6 right-4 sm:right-6 left-4 sm:left-auto sm:max-w-md z-50 animate-slide-up"
        >
          <div className="rounded-2xl p-5 bg-slate-900/95 border border-white/10 backdrop-blur-xl shadow-2xl shadow-violet-950/40 flex flex-col gap-3.5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-violet-500/15 border border-violet-500/20 text-violet-400">
                  <Cookie className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">We value your privacy</h3>
                  <p className="text-[11px] text-white/40">Cookies & Anonymous Analytics</p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleDecline}
                className="p-1 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/[0.06] transition-colors"
                aria-label="Close cookie consent banner"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              We use essential cookies and anonymous analytics to process videos securely and personalize your experience. We never store personal information. Learn more in our{" "}
              <Link href="/privacy" className="text-violet-400 font-medium hover:underline inline-flex items-center gap-0.5">
                Privacy Policy
              </Link>
              .
            </p>

            <div className="flex items-center gap-2 pt-1">
              <button
                type="button"
                onClick={handleDecline}
                className="flex-1 py-2 px-3.5 rounded-xl border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] text-xs font-medium text-white/70 hover:text-white transition-all duration-150"
              >
                Essential Only
              </button>
              <button
                type="button"
                onClick={handleAccept}
                className="flex-1 py-2 px-3.5 rounded-xl gradient-cta text-xs font-semibold text-white shadow-md shadow-violet-500/20 hover:opacity-95 transition-all duration-150"
              >
                Accept All
              </button>
            </div>
          </div>
        </aside>
      )}
    </>
  );
}
