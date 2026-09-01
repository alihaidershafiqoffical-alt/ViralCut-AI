"use client";

/**
 * url-ingest-zone.tsx
 * -------------------
 * URL-based video ingestion UI for ViralCut.
 *
 * States:
 *   idle      → shows input + paste + submit
 *   loading   → shows spinner + "Validating and downloading…" + progress steps
 *   success   → shows accepted indicator + queued message
 *   error     → shows error message + clear/retry option
 *
 * The component mirrors the visual language of upload-zone.tsx:
 * same surface, same error pattern, same button styles.
 */

import { useState, useRef, useCallback } from "react";
import {
  Link2,
  ClipboardPaste,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
  Play,
  Globe,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Progress } from "@/components/ui/Progress";
import { cn } from "@/lib/utils";
import { API_URL } from "@/lib/config";

// ---------------------------------------------------------------------------
// Supported providers — purely cosmetic; enforcement is backend-only.
// ---------------------------------------------------------------------------

const SUPPORTED_SOURCES = [
  {
    id: "youtube",
    label: "YouTube",
    icon: Play,
    color: "#FF0000",
    example: "youtube.com/watch?v=…",
  },
  {
    id: "direct_url",
    label: "Direct video link",
    icon: Globe,
    color: "#a78bfa",
    example: "storage.example.com/video.mp4",
  },
];

// ---------------------------------------------------------------------------
// Processing steps shown during loading
// ---------------------------------------------------------------------------

const PROGRESS_STEPS = [
  { label: "Validating URL", pct: 15 },
  { label: "Checking video source", pct: 30 },
  { label: "Downloading video", pct: 65 },
  { label: "Verifying content", pct: 90 },
  { label: "Queuing for processing", pct: 100 },
];

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

const API_BASE = API_URL;

async function ingestUrl(url: string): Promise<{ jobId: string; provider: string }> {
  const res = await fetch(`${API_BASE}/api/v1/videos/ingest-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  const data = await res.json();
  if (!res.ok) {
    const msg =
      typeof data?.detail === "string"
        ? data.detail
        : "Something went wrong. Please try again.";
    throw new Error(msg);
  }
  return { jobId: data.jobId, provider: data.provider };
}

// ---------------------------------------------------------------------------
// Client-side pre-check (UX only — server re-validates everything)
// ---------------------------------------------------------------------------

function clientCheck(raw: string): string | null {
  const url = raw.trim();
  if (!url) return "Please enter a video URL.";
  if (!url.startsWith("https://"))
    return "Please enter a URL that begins with https://";
  return null;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface UrlIngestZoneProps {
  onJobCreated?: (jobId: string) => void;
  disabled?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

type Phase = "idle" | "loading" | "success" | "error";

export function UrlIngestZone({ onJobCreated, disabled = false }: UrlIngestZoneProps) {
  const [url, setUrl] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [progressStep, setProgressStep] = useState(0);
  const [acceptedProvider, setAcceptedProvider] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // -- helpers ---------------------------------------------------------------

  const reset = useCallback(() => {
    setPhase("idle");
    setErrorMsg(null);
    setProgressStep(0);
    setAcceptedProvider(null);
    setUrl("");
    setTimeout(() => inputRef.current?.focus(), 50);
  }, []);

  const clearError = useCallback(() => {
    if (phase === "error") {
      setPhase("idle");
      setErrorMsg(null);
    }
  }, [phase]);

  // -- paste -----------------------------------------------------------------

  const handlePaste = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      setUrl(text.trim());
      clearError();
      inputRef.current?.focus();
    } catch {
      inputRef.current?.focus();
    }
  }, [clearError]);

  // -- submit ----------------------------------------------------------------

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();

      const clientError = clientCheck(trimmed);
      if (clientError) {
        setPhase("error");
        setErrorMsg(clientError);
        return;
      }

      setPhase("loading");
      setErrorMsg(null);
      setProgressStep(0);

      // Simulate step-through during network wait
      let step = 0;
      const stepTimer = setInterval(() => {
        step = Math.min(step + 1, PROGRESS_STEPS.length - 2); // hold at second-to-last
        setProgressStep(step);
      }, 900);

      try {
        const result = await ingestUrl(trimmed);
        clearInterval(stepTimer);
        setProgressStep(PROGRESS_STEPS.length - 1); // snap to 100%
        await new Promise((r) => setTimeout(r, 400)); // brief pause at 100%
        setAcceptedProvider(result.provider);
        setPhase("success");
        onJobCreated?.(result.jobId);
      } catch (err) {
        clearInterval(stepTimer);
        setPhase("error");
        setErrorMsg(
          err instanceof Error ? err.message : "An unexpected error occurred."
        );
        setProgressStep(0);
      }
    },
    [url, onJobCreated]
  );

  // -- input change ----------------------------------------------------------

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setUrl(e.target.value);
      if (phase === "error") {
        setPhase("idle");
        setErrorMsg(null);
      }
    },
    [phase]
  );

  const isLoading = phase === "loading";
  const currentStep = PROGRESS_STEPS[progressStep];

  // -- render ----------------------------------------------------------------

  return (
    <div className="space-y-4">

      {/* ── Supported sources note ─────────────────────────────────────── */}
      <div className="flex items-start gap-2.5 rounded-xl border border-violet-500/10 bg-violet-500/[0.05] px-3.5 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" />
        <div className="min-w-0">
          <p className="text-xs font-medium text-violet-300">
            Authorized sources only
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground leading-relaxed">
            ViralCut only processes publicly accessible videos from supported
            platforms. Private, geo-restricted, or paywalled content cannot be
            accessed.
          </p>
          <div className="mt-2.5 flex flex-wrap gap-2">
            {SUPPORTED_SOURCES.map((src) => {
              const Icon = src.icon;
              return (
                <span
                  key={src.id}
                  className="inline-flex items-center gap-1.5 rounded-full border border-white/8 bg-white/[0.04] px-2.5 py-0.5 text-xs text-muted-foreground"
                >
                  <Icon className="h-3 w-3 shrink-0" style={{ color: src.color }} />
                  {src.label}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Main surface ───────────────────────────────────────────────── */}
      <div
        className={cn(
          "rounded-2xl border-2 border-dashed transition-all duration-300",
          phase === "error"
            ? "border-red-500/30 bg-red-500/[0.03]"
            : phase === "success"
            ? "border-emerald-500/30 bg-emerald-500/[0.03]"
            : phase === "loading"
            ? "border-violet-500/30 bg-violet-500/[0.04]"
            : "border-white/10 bg-white/[0.02]"
        )}
      >
        {/* ── SUCCESS state ────────────────────────────────────────────── */}
        {phase === "success" ? (
          <div className="flex items-center gap-4 p-6 animate-fade-in">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-500/15">
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-emerald-300">
                Video accepted
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {acceptedProvider === "youtube"
                  ? "YouTube video"
                  : "Video"}{" "}
                queued for processing. You can track progress below.
              </p>
            </div>
            <button
              onClick={reset}
              title="Add another URL"
              className="shrink-0 flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          </div>
        ) : (
          /* ── IDLE / LOADING / ERROR state ─────────────────────────────── */
          <div className={`p-5 space-y-4 ${disabled ? "opacity-40 pointer-events-none" : ""}`}>

            {/* URL input row */}
            <form
              id="url-ingest-form"
              onSubmit={handleSubmit}
              noValidate
              className="flex items-center gap-2"
            >
              {/* Icon */}
              <div className="shrink-0">
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin text-violet-400" />
                ) : phase === "error" ? (
                  <AlertCircle className="h-4 w-4 text-red-400" />
                ) : (
                  <Link2 className="h-4 w-4 text-muted-foreground" />
                )}
              </div>

              {/* Input */}
              <input
                ref={inputRef}
                id="url-ingest-input"
                type="url"
                inputMode="url"
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck={false}
                value={url}
                onChange={handleChange}
                disabled={disabled || isLoading}
                placeholder="https://www.youtube.com/watch?v=…"
                aria-label="Video URL"
                aria-describedby={errorMsg ? "url-ingest-error" : undefined}
                aria-invalid={phase === "error"}
                className="flex-1 min-w-0 bg-transparent text-sm outline-none placeholder:text-muted-foreground/40 disabled:opacity-50 disabled:cursor-not-allowed"
              />

              {/* Paste */}
              <button
                type="button"
                id="url-paste-btn"
                onClick={handlePaste}
                disabled={disabled || isLoading}
                title="Paste from clipboard"
                className="shrink-0 flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1.5 text-xs text-muted-foreground hover:bg-white/[0.08] hover:text-foreground transition-colors disabled:opacity-40 disabled:pointer-events-none"
              >
                <ClipboardPaste className="h-3.5 w-3.5" />
                Paste
              </button>

              {/* Submit */}
              <Button
                type="submit"
                id="url-ingest-submit"
                disabled={disabled || isLoading || !url.trim()}
                isLoading={isLoading}
                className="shrink-0 gradient-cta border-0 text-white"
              >
                {isLoading ? (
                  "Loading…"
                ) : (
                  <span className="flex items-center gap-1.5">
                    Process
                    <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                )}
              </Button>
            </form>

            {/* Progress indicator — only during loading */}
            {isLoading && (
              <div className="space-y-2 animate-fade-in">
                <Progress
                  value={currentStep.pct}
                  indicatorClassName="bg-gradient-to-r from-violet-600 to-indigo-500 transition-all duration-700"
                />
                <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <Loader2 className="h-3 w-3 animate-spin shrink-0" />
                  {currentStep.label}…
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Error message ──────────────────────────────────────────────── */}
      {phase === "error" && errorMsg && (
        <div
          id="url-ingest-error"
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-3.5 py-3 animate-slide-down"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <div className="flex-1 min-w-0">
            <p className="text-xs text-red-300 leading-relaxed">{errorMsg}</p>
          </div>
          <button
            onClick={reset}
            title="Dismiss"
            className="shrink-0 rounded-md p-0.5 text-red-400/60 hover:text-red-400 transition-colors"
            aria-label="Dismiss error"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
