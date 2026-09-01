// =============================================================================
// components/sections/Results.tsx — Generated Shorts Results Page
// Clean card-based responsive grid displaying [Video Preview], Title, Duration,
// Caption Style, [Edit], [Download], and [Download All].
// =============================================================================
"use client";

import { useState, useRef } from "react";
import {
  Download,
  Edit2,
  Play,
  Pause,
  Archive,
  Flame,
  Clock,
  Type,
  Sparkles,
  CheckCircle2,
  X,
  Volume2,
  VolumeX,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import type { GeneratedClip } from "@/types/index";
import { formatDuration } from "@/lib/formatters";
import { API_URL } from "@/lib/config";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface Props {
  clips: GeneratedClip[];
  jobId?: string | null;
  accessToken?: string | null;
  onStartOver: () => void;
  targetCount?: number;
  jobStatus?: string;
}

// ---------------------------------------------------------------------------
// Sub-component: Placeholder Card
// ---------------------------------------------------------------------------
function PlaceholderCard({ index, status }: { index: number; status: "processing" | "queued" }) {
  return (
    <div className="relative aspect-[9/16] w-full bg-slate-950/50 border border-white/5 opacity-70 flex flex-col justify-between rounded-2xl overflow-hidden p-6 text-center">
      <div className="flex-1 flex flex-col items-center justify-center space-y-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/5 border border-white/10">
          {status === "processing" ? (
            <Loader2 className="h-6 w-6 text-violet-400 animate-spin" />
          ) : (
            <Clock className="h-6 w-6 text-slate-500" />
          )}
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-slate-300">Short #{index}</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            {status === "processing" ? "Generating vertical video with AI captions..." : "Waiting in queue..."}
          </p>
        </div>
      </div>
      
      {/* Skeleton Footer */}
      <div className="h-10 bg-white/5 rounded-xl border border-white/5 animate-pulse mt-auto flex items-center justify-center text-[10px] uppercase font-bold tracking-wider text-slate-600">
        {status === "processing" ? "Processing..." : "Queued"}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Short Card
// ---------------------------------------------------------------------------
interface ShortCardProps {
  clip: GeneratedClip;
  onPreviewClick: (clip: GeneratedClip) => void;
}

function ShortCard({ clip, onPreviewClick }: ShortCardProps) {
  const [isPlayingPreview, setIsPlayingPreview] = useState(false);
  const [isDownloaded, setIsDownloaded] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDownloaded(true);
    // Simulate real download trigger
    const link = document.createElement("a");
    link.href = clip.downloadUrl || "#";
    link.download = `${clip.title ? clip.title.toLowerCase().replace(/[^a-z0-9]/g, "-") : `short-${clip.index}`}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => setIsDownloaded(false), 2500);
  };

  const handleMouseEnter = () => {
    setIsPlayingPreview(true);
    if (videoRef.current) {
      videoRef.current.play().catch(() => {});
    }
  };

  const handleMouseLeave = () => {
    setIsPlayingPreview(false);
    if (videoRef.current) {
      videoRef.current.pause();
    }
  };

  const titleText = clip.title || `Viral Short #${clip.index}`;
  const styleText = clip.captionStyle || "Karaoke Glow";
  const viralPct = Math.round(clip.viralScore * 100);
  const hasValidVideo = clip.previewUrl && clip.previewUrl !== "#";

  return (
    <article
      className="group relative flex flex-col rounded-2xl bg-slate-900/80 border border-white/10 hover:border-violet-500/50 shadow-xl hover:shadow-2xl hover:shadow-violet-950/40 transition-all duration-300 overflow-hidden"
      aria-label={titleText}
    >
      {/* ── 1. [Video Preview] 9:16 Frame ── */}
      <div
        className="relative aspect-[9/16] w-full bg-slate-950 overflow-hidden cursor-pointer group/preview select-none"
        onClick={() => onPreviewClick(clip)}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {hasValidVideo ? (
          <video
            ref={videoRef}
            src={clip.previewUrl}
            className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            muted
            loop
            playsInline
          />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-violet-950/60 via-slate-950 to-fuchsia-950/50 flex items-center justify-center transition-transform duration-500 group-hover:scale-105">
            <div
              className="absolute inset-0 opacity-20"
              style={{
                backgroundImage: "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)",
                backgroundSize: "16px 16px"
              }}
            />
            <div className="absolute inset-x-4 bottom-14 flex flex-col items-center text-center pointer-events-none transition-all duration-300">
              <div className="inline-block px-3 py-1.5 rounded-lg bg-black/75 backdrop-blur-md border border-white/10 shadow-lg">
                <span className="text-xs font-black uppercase tracking-wider text-white">
                  THIS IS HOW <span className="text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.8)]">VIRAL SHORTS</span> ARE MADE 🔥
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Top Badges (Duration & Viral Score) */}
        <div className="absolute top-3 left-3 right-3 flex justify-between items-start z-10">
          {/* Duration Badge */}
          <div className="flex items-center gap-1 rounded-full bg-black/70 backdrop-blur-md px-2.5 py-1 text-xs font-semibold text-white border border-white/15 shadow-md">
            <Clock className="w-3 h-3 text-violet-400" />
            <span>{formatDuration(clip.duration)}</span>
          </div>

          {/* Viral Score Badge */}
          <div className="flex items-center gap-1 rounded-full bg-black/70 backdrop-blur-md px-2.5 py-1 text-xs font-bold text-white border border-white/15 shadow-md">
            <Flame className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            <span className="text-amber-300">{viralPct}</span>
            <span className="text-[10px] text-white/50">/100</span>
          </div>
        </div>

        {/* Play / Pause Center Overlay Button */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover/preview:bg-black/35 transition-colors duration-300 z-10">
          <div className="w-13 h-13 rounded-full bg-violet-600/90 text-white flex items-center justify-center shadow-lg shadow-violet-950/60 transform transition-all duration-300 group-hover/preview:scale-110">
            {isPlayingPreview ? (
              <Pause className="w-6 h-6 fill-white" />
            ) : (
              <Play className="w-6 h-6 fill-white ml-0.5" />
            )}
          </div>
        </div>

        {/* Hover Hint */}
        <div className="absolute bottom-3 left-0 right-0 text-center opacity-0 group-hover/preview:opacity-100 transition-opacity duration-200 z-10">
          <span className="text-[11px] font-medium text-white/80 bg-black/60 backdrop-blur-sm px-2.5 py-0.5 rounded-full border border-white/10">
            Click to watch preview
          </span>
        </div>
      </div>

      {/* ── 2. Details & Metadata ── */}
      <div className="p-4 sm:p-5 flex flex-col flex-1 gap-3.5 bg-slate-900/90">
        {/* Title */}
        <div>
          <h3
            className="text-sm sm:text-base font-bold text-white leading-snug line-clamp-2 hover:text-violet-300 transition-colors cursor-pointer"
            title={titleText}
            onClick={() => onPreviewClick(clip)}
          >
            {titleText}
          </h3>
        </div>

        {/* Metadata Tags: Duration & Caption Style */}
        <div className="flex flex-col gap-2 text-xs">
          {/* Duration info */}
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              Duration
            </span>
            <span className="font-semibold text-slate-200">
              {formatDuration(clip.duration)} ({formatDuration(clip.startTime)} - {formatDuration(clip.endTime)})
            </span>
          </div>

          {/* Caption Style info */}
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <Type className="w-3.5 h-3.5 text-slate-500" />
              Caption Style
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-medium text-violet-300 bg-violet-500/10 border border-violet-500/20">
              <Sparkles className="w-2.5 h-2.5" />
              {styleText}
            </span>
          </div>
        </div>

        {/* ── 3. [Edit] and [Download] Action Buttons ── */}
        <div className="flex items-center gap-2 pt-2 mt-auto">
          {/* [Edit] Button */}
          <Link
            href={`/editor?videoUrl=${encodeURIComponent(clip.previewUrl)}&startTime=${clip.startTime}&endTime=${clip.endTime}&style=${encodeURIComponent(styleText)}`}
            className="flex-1 py-2.5 px-3 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] border border-white/10 hover:border-white/20 text-slate-200 hover:text-white transition-all text-xs sm:text-sm font-semibold flex items-center justify-center gap-1.5 shadow-sm active:scale-95"
            title="Edit timing, framing, and caption styles"
          >
            <Edit2 className="w-3.5 h-3.5 text-violet-400" />
            <span>Edit</span>
          </Link>

          {/* [Download] Button */}
          <button
            onClick={handleDownload}
            className={`flex-1 py-2.5 px-3 rounded-xl transition-all text-xs sm:text-sm font-semibold flex items-center justify-center gap-1.5 shadow-md active:scale-95 ${
              isDownloaded
                ? "bg-emerald-600 text-white shadow-emerald-900/40"
                : "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-violet-900/40 hover:shadow-violet-900/60"
            }`}
            title="Download full HD Short"
          >
            {isDownloaded ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Downloaded</span>
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5" />
                <span>Download</span>
              </>
            )}
          </button>
        </div>
      </div>
    </article>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Fullscreen Video Preview Modal
// ---------------------------------------------------------------------------
interface PreviewModalProps {
  clips: GeneratedClip[];
  clip: GeneratedClip | null;
  onClose: () => void;
  onClipChange: (clip: GeneratedClip) => void;
}

function PreviewModal({ clips, clip, onClose, onClipChange }: PreviewModalProps) {
  const [isMuted, setIsMuted] = useState(false);

  if (!clip) return null;
  const hasValidVideo = clip.previewUrl && clip.previewUrl !== "#";

  const currentIdx = clips.findIndex(c => c.id === clip.id);
  const hasPrev = currentIdx > 0;
  const hasNext = currentIdx < clips.length - 1;

  const handlePrev = () => {
    if (hasPrev) onClipChange(clips[currentIdx - 1]);
  };

  const handleNext = () => {
    if (hasNext) onClipChange(clips[currentIdx + 1]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-[400px] h-[82vh] min-h-[500px] max-h-[820px] bg-slate-900 rounded-3xl border border-white/15 overflow-hidden shadow-2xl flex flex-col animate-scale-in">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-slate-950/60 flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-violet-500 animate-pulse" />
            <h4 className="text-sm font-bold text-white truncate max-w-[240px]">
              {clip.title || `Short #${clip.index}`}
            </h4>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-slate-300 hover:text-white flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 9:16 Video Player Area with side-navigation buttons */}
        <div className="relative flex-1 min-h-0 bg-black flex items-center justify-center overflow-hidden group">
          {hasValidVideo ? (
            <video
              key={clip.previewUrl}
              src={clip.previewUrl}
              className="absolute inset-0 w-full h-full object-cover"
              controls
              autoPlay
              playsInline
              muted={isMuted}
            />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-t from-black via-slate-950 to-violet-950/50 flex items-center justify-center">
              <div className="text-center p-6 space-y-3">
                <div className="w-16 h-16 mx-auto rounded-full bg-violet-600/30 border border-violet-500/40 flex items-center justify-center text-violet-400">
                  <Play className="w-8 h-8 fill-current ml-1" />
                </div>
                <p className="text-sm font-semibold text-slate-300">
                  1080 &times; 1920 HD Ready
                </p>
              </div>

              {/* Live Caption Mockup */}
              <div className="absolute bottom-16 inset-x-6 text-center">
                <div className="inline-block p-3 rounded-xl bg-black/80 backdrop-blur-md border border-white/15">
                  <p className="text-sm sm:text-base font-black text-white uppercase tracking-wide">
                    &quot;THE SECRET TO <span className="text-emerald-400">EXPONENTIAL</span> GROWTH&quot;
                  </p>
                  <span className="text-[10px] text-violet-300 block mt-1">
                    Style: {clip.captionStyle || "Karaoke Glow"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Previous Reels Button Overlay */}
          {hasPrev && (
            <button
              onClick={handlePrev}
              className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/55 hover:bg-black/80 text-white border border-white/10 flex items-center justify-center transition-all z-20 shadow-md"
              aria-label="Previous Clip"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
          )}

          {/* Next Reels Button Overlay */}
          {hasNext && (
            <button
              onClick={handleNext}
              className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/55 hover:bg-black/80 text-white border border-white/10 flex items-center justify-center transition-all z-20 shadow-md"
              aria-label="Next Clip"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          )}

          {/* Quick controls on video overlay */}
          <div className="absolute top-4 right-4 flex gap-2 z-10">
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="w-9 h-9 rounded-full bg-black/60 backdrop-blur-md text-white border border-white/10 flex items-center justify-center hover:bg-black/80"
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="p-4 bg-slate-950 flex items-center gap-3 flex-shrink-0">
          <Link
            href={`/editor?videoUrl=${encodeURIComponent(clip.previewUrl)}&startTime=${clip.startTime}&endTime=${clip.endTime}`}
            className="flex-1 py-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 border border-white/10"
          >
            <Edit2 className="w-4 h-4 text-violet-400" />
            Open in Editor
          </Link>
          <a
            href={clip.downloadUrl || "#"}
            download={`short-${clip.index}.mp4`}
            className="flex-1 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-violet-900/40"
          >
            <Download className="w-4 h-4" />
            Download MP4
          </a>
        </div>

      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component: Results
// ---------------------------------------------------------------------------
export default function Results({ clips, jobId, accessToken, onStartOver, targetCount, jobStatus }: Props) {
  const [selectedClip, setSelectedClip] = useState<GeneratedClip | null>(null);
  const [isDownloadingAll, setIsDownloadingAll] = useState(false);
  const [downloadAllProgress, setDownloadAllProgress] = useState(0);

  if (!clips || clips.length === 0) {
    return null;
  }

  // Handle Download All batch package
  const handleDownloadAll = () => {
    if (isDownloadingAll) return;
    setIsDownloadingAll(true);
    setDownloadAllProgress(25);

    const zipUrl = jobId
      ? `${API_URL}/api/v1/jobs/${jobId}/download-all${accessToken ? `?token=${accessToken}` : ""}`
      : "#";

    const link = document.createElement("a");
    link.href = zipUrl;
    link.download = `viralcut_shorts_${jobId || "package"}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setDownloadAllProgress(100);
    setTimeout(() => {
      setIsDownloadingAll(false);
      setDownloadAllProgress(0);
    }, 1500);
  };

  return (
    <section
      id="results"
      className="mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 py-4 animate-fade-in"
      aria-label="Generated Shorts Results"
    >
      {/* ── Page Header Row ── */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-8 border-b border-white/10 mb-8">
        
        {/* Left: Titles & Stats */}
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Processing Complete
            </span>
            <span className="text-xs text-slate-400 font-medium">
              {clips.length} Shorts Ready
            </span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Generated <span className="bg-gradient-to-r from-violet-400 via-purple-300 to-pink-400 bg-clip-text text-transparent">Viral Shorts</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Preview, customize captions, or download full high-definition 1080×1920 clips.
          </p>
        </div>

        {/* Right: Actions ([Download All] & [Start Over]) */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Start Over Button */}
          <button
            onClick={onStartOver}
            className="px-4 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 text-slate-300 hover:text-white text-xs sm:text-sm font-medium transition-all"
          >
            Process Another Video
          </button>

          {/* [Download All] Button */}
          <button
            onClick={handleDownloadAll}
            disabled={isDownloadingAll || jobStatus !== "completed"}
            className={`relative overflow-hidden px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm text-white shadow-xl transition-all flex items-center justify-center gap-2 ${
              isDownloadingAll
                ? "bg-slate-800 border border-violet-500/50 cursor-wait"
                : jobStatus !== "completed"
                  ? "bg-slate-800 border border-white/5 opacity-40 cursor-not-allowed"
                  : "bg-gradient-to-r from-violet-600 via-purple-600 to-pink-600 hover:opacity-90 shadow-violet-900/40 active:scale-95"
            }`}
          >
            {isDownloadingAll ? (
              <>
                <Archive className="w-4 h-4 text-violet-400 animate-bounce" />
                <span>Zipping Shorts ({downloadAllProgress}%)…</span>
                {/* Progress bar inside button */}
                <div
                  className="absolute bottom-0 left-0 h-1 bg-violet-400 transition-all duration-300"
                  style={{ width: `${downloadAllProgress}%` }}
                />
              </>
            ) : (
              <>
                <Archive className="w-4 h-4" />
                <span>Download All (.zip)</span>
              </>
            )}
          </button>
        </div>

      </div>

      {/* ── Responsive Card Grid ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {clips.map((clip) => (
          <ShortCard
            key={clip.id}
            clip={clip}
            onPreviewClick={(c) => setSelectedClip(c)}
          />
        ))}
        {/* Placeholder cards for remaining clips */}
        {targetCount && targetCount > clips.length && (
          Array.from({ length: targetCount - clips.length }).map((_, idx) => {
            const index = clips.length + idx + 1;
            const status = idx === 0 && jobStatus !== "completed" && jobStatus !== "failed" ? "processing" : "queued";
            return (
              <PlaceholderCard
                key={`placeholder-${index}`}
                index={index}
                status={status}
              />
            );
          })
        )}
      </div>

      {/* ── Reassurance / Expiration Note ── */}
      <div className="mt-12 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] text-center max-w-xl mx-auto">
        <p className="text-xs text-slate-400">
          ⚡ Storage Notice: Generated videos are stored securely for 24 hours. Be sure to download your clips before they expire.
        </p>
      </div>

      {/* ── Fullscreen Preview Modal ── */}
      <PreviewModal
        clips={clips}
        clip={selectedClip}
        onClose={() => setSelectedClip(null)}
        onClipChange={(c) => setSelectedClip(c)}
      />
    </section>
  );
}
