// =============================================================================
// components/sections/ProcessingState.tsx — 9-Stage Real-Time Progress Panel
// =============================================================================
"use client";

import { useEffect, useState } from "react";
import { Loader2, CheckCircle2, Sparkles } from "lucide-react";

export interface PipelineStage {
  id: number;
  name: string;
  percent: number;
  message: string;
}

export const STAGES: PipelineStage[] = [
  { id: 1, name: "Uploading",        percent: 10, message: "Uploading your video securely to our processing servers…" },
  { id: 2, name: "Analyzing video",  percent: 22, message: "Scanning video dimensions, resolution, and frame rates…" },
  { id: 3, name: "Extracting audio", percent: 35, message: "Isolating high-fidelity audio tracks for vocal detection…" },
  { id: 4, name: "Transcribing",     percent: 48, message: "Transcribing speech with AI word-level synchronization…" },
  { id: 5, name: "AI analysis",      percent: 60, message: "Gemini AI is analyzing sentiment, hooks, and viral retention points…" },
  { id: 6, name: "Selecting clips",  percent: 72, message: "Scoring and picking the top viral moments for your Shorts…" },
  { id: 7, name: "Generating Shorts",percent: 85, message: "Cropping to 9:16 vertical layout with active speaker tracking…" },
  { id: 8, name: "Adding captions",  percent: 94, message: "Rendering dynamic kinetic animated captions and emojis…" },
  { id: 9, name: "Finalizing",       percent: 100,message: "Packaging your ready-to-publish viral Shorts!" },
];

interface Props {
  currentStageId?: number;
  progress?: number;
  customMessage?: string;
  isError?: boolean;
  onStartOver?: () => void;
}

export default function ProcessingState({
  currentStageId,
  progress,
  customMessage,
  isError,
  onStartOver,
}: Props) {
  const [stageIndex, setStageIndex] = useState(0);
  const [demoProgress, setDemoProgress] = useState(10);

  const effectiveStageIndex = currentStageId !== undefined
    ? Math.min(Math.max(currentStageId - 1, 0), STAGES.length - 1)
    : stageIndex;

  // Auto-advance demo stages if external props are not supplied
  useEffect(() => {
    if (currentStageId !== undefined || isError) {
      return;
    }

    const interval = setInterval(() => {
      setStageIndex((prev) => {
        if (prev < STAGES.length - 1) {
          const next = prev + 1;
          setDemoProgress(STAGES[next].percent);
          return next;
        }
        return prev;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [currentStageId, isError]);

  const activeStage = STAGES[effectiveStageIndex] || STAGES[0];
  const displayProgress = progress !== undefined ? progress : demoProgress;
  const isComplete = displayProgress >= 100 && !isError;
  const displayMessage = customMessage || activeStage.message;

  return (
    <section
      id="processing"
      className="mx-auto max-w-2xl w-full px-4 animate-fade-in"
      aria-label="Video processing status"
      aria-live="polite"
      aria-busy={!isComplete && !isError}
    >
      <div className="rounded-3xl p-8 sm:p-10 flex flex-col gap-6 bg-slate-900/80 backdrop-blur-xl border border-white/10 shadow-2xl shadow-violet-950/40">
        
        {/* Header with Stage & Percentage */}
        <div className="flex justify-between items-end">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-violet-400 bg-violet-500/10 border border-violet-500/20 mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Stage {activeStage.id} of {STAGES.length}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              {activeStage.name}
            </h2>
          </div>

          <div className="flex items-baseline font-mono">
            <span className="text-4xl font-extrabold text-white tracking-tight">
              {Math.round(displayProgress)}
            </span>
            <span className="text-xl font-bold text-violet-400 ml-1">%</span>
          </div>
        </div>

        {/* Progress Track */}
        <div
          className="h-3 w-full overflow-hidden rounded-full bg-white/[0.07] border border-white/[0.05] relative"
          role="progressbar"
          aria-valuenow={Math.round(displayProgress)}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full transition-all duration-500 ease-out shadow-lg"
            style={{
              width: `${displayProgress}%`,
              background: isError
                ? "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)"
                : "linear-gradient(90deg, #7c3aed 0%, #a855f7 50%, #ec4899 100%)",
            }}
          />
        </div>

        {/* Friendly Status Message Box */}
        <div className={`flex items-center gap-3 p-4 rounded-xl border ${
          isError 
            ? "bg-red-500/10 border-red-500/30 text-red-200" 
            : "bg-white/[0.03] border-white/[0.06] text-slate-200"
        }`}>
          <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isError ? "bg-red-500/20 text-red-400" : "bg-violet-500/10 text-violet-400"
          }`}>
            {isError ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            ) : isComplete ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <Loader2 className="w-5 h-5 animate-spin" />
            )}
          </div>
          <p className="text-sm sm:text-base font-medium">
            {displayMessage}
          </p>
        </div>

        {/* 9 Stages Grid Indicator */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2">
          {STAGES.map((s, idx) => {
            const isFinished = idx < effectiveStageIndex || (idx === effectiveStageIndex && isComplete);
            const isCurrent = idx === effectiveStageIndex && !isComplete;

            return (
              <div
                key={s.id}
                className={`flex items-center gap-2 p-2.5 rounded-lg text-xs font-medium border transition-all duration-300 ${
                  isCurrent
                    ? "bg-violet-600/20 border-violet-500/50 text-white shadow-md shadow-violet-500/10"
                    : isFinished
                    ? "bg-emerald-500/10 border-emerald-500/20 text-slate-300"
                    : "bg-white/[0.02] border-white/[0.04] text-slate-500"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isCurrent
                      ? "bg-violet-500 text-white"
                      : isFinished
                      ? "bg-emerald-500 text-white"
                      : "bg-white/10 text-slate-400"
                  }`}
                >
                  {isFinished ? "✓" : s.id}
                </div>
                <span className="truncate">{s.name}</span>
              </div>
            );
          })}
        </div>

        {isError && onStartOver && (
          <div className="flex justify-center pt-4 border-t border-white/5">
            <button
              onClick={onStartOver}
              className="px-6 py-2.5 rounded-full text-sm font-semibold text-white bg-red-600 hover:bg-red-500 hover:scale-105 active:scale-95 transition-all shadow-md shadow-red-900/20"
            >
              Start Over & Try Again
            </button>
          </div>
        )}

        <p className="text-center text-xs text-slate-500 pt-2">
          Safe processing active. All clips and temporary assets are protected and auto-cleaned.
        </p>
      </div>
    </section>
  );
}
