import { Sparkles } from "lucide-react";

export default function Hero() {
  return (
    <section
      id="hero"
      className="relative overflow-hidden pt-36 pb-16 sm:pt-44 sm:pb-20 text-center"
      aria-label="Hero section"
    >
      {/* ── Ambient background blobs ── */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
        <div
          className="absolute -top-24 -left-32 h-[520px] w-[520px] rounded-full
                      bg-violet-700/20 blur-[120px]"
          style={{ animation: "float 8s ease-in-out infinite" }}
        />
        <div
          className="absolute -top-16 -right-40 h-[420px] w-[420px] rounded-full
                      bg-indigo-600/15 blur-[100px]"
          style={{ animation: "float 10s ease-in-out infinite 2s" }}
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                      h-[300px] w-[600px] rounded-full
                      bg-pink-600/10 blur-[140px]"
        />
        <div
          className="absolute inset-0 opacity-[0.025]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.15) 1px,transparent 1px)," +
              "linear-gradient(90deg,rgba(255,255,255,0.15) 1px,transparent 1px)",
            backgroundSize: "56px 56px",
          }}
        />
      </div>

      <div className="mb-6 animate-fade-in" style={{ animationDelay: "0s" }}>
        <span
          className="
            inline-flex items-center gap-2
            rounded-full border border-violet-500/30
            bg-violet-500/10 px-4 py-1.5
            text-xs font-semibold uppercase tracking-widest text-violet-300
          "
        >
          <Sparkles className="h-3 w-3" />
          Powered by Gemini AI + Faster-Whisper
        </span>
      </div>

      <h1
        className="
          mx-auto max-w-4xl px-4
          text-4xl sm:text-5xl md:text-6xl lg:text-7xl
          font-extrabold leading-[1.08] tracking-tight
          text-white
          animate-slide-up stagger-1
        "
        style={{ fontFamily: "var(--font-heading, inherit)" }}
      >
        Free <span className="gradient-text">AI Shorts Generator</span>: Turn Long Video to Shorts
      </h1>

      <p
        className="
          mx-auto mt-6 max-w-2xl px-4
          text-lg sm:text-xl text-white/60 leading-relaxed
          animate-slide-up stagger-2
        "
      >
        ViralCut is a free AI video clip generator that transforms long video to Shorts. Instantly identify viral highlights, crop to vertical format, and burn automatic captions to skyrocket retention.
      </p>

      {/* ── Scroll cue arrow ── */}
      <div
        className="mt-14 flex justify-center animate-fade-in stagger-4"
        aria-hidden="true"
      >
        <div
          className="flex flex-col items-center gap-1 text-white/20"
          style={{ animation: "float 3s ease-in-out infinite" }}
        >
          <span className="text-[10px] uppercase tracking-[0.2em] font-medium">
            Get started below
          </span>
          <svg
            width="16" height="24" viewBox="0 0 16 24"
            fill="none" className="opacity-60"
          >
            <path d="M8 0v20M1 13l7 8 7-8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
    </section>
  );
}
