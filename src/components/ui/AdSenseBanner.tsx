"use client";

import { useEffect, useRef, useState } from "react";
import Script from "next/script";

interface AdSenseBannerProps {
  slot: string;
  format?: "auto" | "fluid" | "rectangle";
  responsive?: boolean;
  className?: string;
}

export default function AdSenseBanner({
  slot,
  format = "auto",
  responsive = true,
  className = "",
}: AdSenseBannerProps) {
  const [hasError, setHasError] = useState(false);
  const adRef = useRef<HTMLModElement>(null);
  const pushedRef = useRef(false);

  const publisherId = process.env.NEXT_PUBLIC_ADSENSE_PUB_ID || "";
  const isEnabled = Boolean(publisherId && publisherId !== "ca-pub-3940256099942544");

  const isDev =
    process.env.NODE_ENV === "development" ||
    typeof window === "undefined" ||
    (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) ||
    !isEnabled;

  useEffect(() => {
    if (isDev || pushedRef.current) return;

    // In production with real publisher ID, wait until layout has computed width > 0
    let retryCount = 0;
    const maxRetries = 10;

    const initAd = () => {
      if (!adRef.current || pushedRef.current) return;

      const width = adRef.current.offsetWidth;
      if (width > 0) {
        try {
          const win = window as unknown as { adsbygoogle?: Record<string, unknown>[] };
          win.adsbygoogle = win.adsbygoogle || [];
          win.adsbygoogle.push({});
          pushedRef.current = true;
        } catch (err) {
          console.warn("AdSense push error caught:", err);
          setHasError(true);
        }
      } else if (retryCount < maxRetries) {
        retryCount++;
        setTimeout(initAd, 200);
      }
    };

    const timer = setTimeout(initAd, 150);
    return () => clearTimeout(timer);
  }, [isDev]);

  if (hasError) {
    return null;
  }

  // In development mode or when no real AdSense ID is configured, show a clean dev preview
  if (isDev) {
    return (
      <aside
        className={`my-8 mx-auto max-w-4xl w-full px-4 text-center select-none flex flex-col items-center gap-1.5 ${className}`}
        aria-label="Advertisement Placeholder"
      >
        <span className="text-[10px] uppercase tracking-[0.2em] text-white/35 font-medium">
          Advertisement (Dev Mode)
        </span>
        <div className="w-full min-h-[90px] rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-4 flex flex-col items-center justify-center gap-1">
          <p className="text-xs text-white/40 font-mono">
            AdSense Unit Slot: {slot}
          </p>
          <p className="text-[11px] text-white/25">
            (Live ads disabled on localhost to prevent width measurement errors)
          </p>
        </div>
      </aside>
    );
  }

  return (
    <aside
      className={`my-8 mx-auto max-w-4xl w-full px-4 text-center select-none flex flex-col items-center gap-1.5 ${className}`}
      aria-label="Advertisement"
    >
      <span className="text-[10px] uppercase tracking-[0.2em] text-white/35 font-medium">
        Advertisement
      </span>

      <div className="w-full min-h-[100px] rounded-2xl border border-white/[0.06] bg-white/[0.02] p-4 flex items-center justify-center overflow-hidden">
        <Script
          async
          src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${publisherId}`}
          crossOrigin="anonymous"
          strategy="lazyOnload"
        />

        <ins
          ref={adRef}
          className="adsbygoogle"
          style={{ display: "block", width: "100%" }}
          data-ad-client={publisherId}
          data-ad-slot={slot}
          data-ad-format={format}
          data-full-width-responsive={responsive ? "true" : "false"}
        />
      </div>
    </aside>
  );
}
