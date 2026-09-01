// =============================================================================
// app/editor/page.tsx — Lightweight, mobile-friendly AI Shorts Editor.
// Features trim sliders, styling selectors, interactive preview overlays,
// and a simulated rendering task progress overlay.
// =============================================================================
"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Play,
  Pause,
  Download,
  ArrowLeft,
  Settings,
  Scissors,
  Type,
  Maximize,
  Save,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/Separator";
import { Button } from "@/components/ui/Button";

// ---------------------------------------------------------------------------
// Word timestamp mock data for visual overlay rendering
// ---------------------------------------------------------------------------
interface MockWord {
  word: string;
  start: number;
  end: number;
}

const MOCK_WORDS: MockWord[] = [
  { word: "Welcome", start: 0.5, end: 0.9 },
  { word: "to", start: 1.0, end: 1.2 },
  { word: "the", start: 1.3, end: 1.5 },
  { word: "future", start: 1.6, end: 2.1 },
  { word: "of", start: 2.2, end: 2.4 },
  { word: "AI", start: 2.5, end: 2.9 },
  { word: "video", start: 3.0, end: 3.4 },
  { word: "clipping.", start: 3.5, end: 4.2 },
  { word: "Generate", start: 4.8, end: 5.3 },
  { word: "shorts", start: 5.4, end: 5.8 },
  { word: "instantly", start: 5.9, end: 6.5 },
  { word: "with", start: 6.6, end: 6.8 },
  { word: "dynamic", start: 6.9, end: 7.4 },
  { word: "karaoke", start: 7.5, end: 8.1 },
  { word: "word", start: 8.2, end: 8.6 },
  { word: "highlights.", start: 8.7, end: 9.5 },
  { word: "This", start: 10.0, end: 10.3 },
  { word: "editor", start: 10.4, end: 10.8 },
  { word: "makes", start: 10.9, end: 11.2 },
  { word: "tuning", start: 11.3, end: 11.7 },
  { word: "extremely", start: 11.8, end: 12.3 },
  { word: "simple.", start: 12.4, end: 13.0 }
];

// ---------------------------------------------------------------------------
// Font presets registry definitions
// ---------------------------------------------------------------------------
const FONTS = ["Inter", "Poppins", "Montserrat", "Roboto"];

// ---------------------------------------------------------------------------
// Caption visual style configurations
// ---------------------------------------------------------------------------
interface StylePreset {
  name: string;
  fontFamily: string;
  fontWeight: string;
  color: string;
  highlightColor: string;
  outlineColor: string;
  shadowColor?: string;
  backgroundColor?: string;
  scaleOnActive?: boolean;
}

const STYLE_PRESETS: Record<string, StylePreset> = {
  Classic: {
    name: "Classic",
    fontFamily: "Arial",
    fontWeight: "bold",
    color: "#FFFFFF",
    highlightColor: "#FFFFFF",
    outlineColor: "#000000",
    shadowColor: "rgba(0,0,0,0.5)"
  },
  Bold: {
    name: "Bold",
    fontFamily: "Montserrat",
    fontWeight: "900",
    color: "#FFFFFF",
    highlightColor: "#FFFF00", // Vivid yellow
    outlineColor: "#000000",
    scaleOnActive: true
  },
  Minimal: {
    name: "Minimal",
    fontFamily: "Inter",
    fontWeight: "normal",
    color: "#EEEEEE",
    highlightColor: "#EEEEEE",
    outlineColor: "transparent"
  },
  Modern: {
    name: "Modern",
    fontFamily: "Outfit",
    fontWeight: "bold",
    color: "#FFFFFF",
    highlightColor: "#FFFFFF",
    outlineColor: "transparent",
    backgroundColor: "rgba(0,0,0,0.7)"
  },
  Highlight: {
    name: "Highlight",
    fontFamily: "Montserrat",
    fontWeight: "bold",
    color: "#FFFFFF",
    highlightColor: "#FF4500", // Vibrant orange
    outlineColor: "#111111"
  },
  Karaoke: {
    name: "Karaoke",
    fontFamily: "Outfit",
    fontWeight: "bold",
    color: "#AAAAAA", // Dimmed inactive gray
    highlightColor: "#00FF00", // Neon green highlight
    outlineColor: "#000000",
    scaleOnActive: true
  }
};

export default function EditorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Search parameters or fallback defaults
  const videoUrlParam = searchParams.get("videoUrl") || "https://assets.mixkit.co/videos/preview/mixkit-founder-working-on-his-laptop-at-the-office-42261-large.mp4";
  const startParam = parseFloat(searchParams.get("startTime") || "0");
  const endParam = parseFloat(searchParams.get("endTime") || "13.0");
  const styleParam = searchParams.get("captionStyle") || "Karaoke";
  const posParam = parseFloat(searchParams.get("captionPosition") || "78");
  const fontParam = searchParams.get("font") || "Outfit";
  const sizeParam = parseFloat(searchParams.get("fontSize") || "42");

  // State Management
  const [startTime, setStartTime] = useState(startParam);
  const [endTime, setEndTime] = useState(endParam);
  const [selectedStyle, setSelectedStyle] = useState(styleParam);
  const [selectedFont, setSelectedFont] = useState(fontParam);
  const [fontSize, setFontSize] = useState(sizeParam);

  // Positioning States
  const [alignment, setAlignment] = useState<"left" | "center" | "right">("center");
  const [verticalPreset, setVerticalPreset] = useState<"top" | "center" | "bottom">(
    posParam < 30 ? "top" : posParam < 65 ? "center" : "bottom"
  );
  const [verticalOffset, setVerticalOffset] = useState<number>(
    posParam - (posParam < 30 ? 15 : posParam < 65 ? 50 : 80)
  );

  const getPresetY = (preset: "top" | "center" | "bottom") => {
    if (preset === "top") return 15;
    if (preset === "center") return 50;
    return 80;
  };
  const positionY = getPresetY(verticalPreset) + verticalOffset;

  // Player States
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Rendering Task State simulation
  const [isRendering, setIsRendering] = useState(false);
  const [renderProgress, setRenderProgress] = useState(0);
  const [renderStep, setRenderStep] = useState("");
  const [isRenderComplete, setIsRenderComplete] = useState(false);

  // Apply properties on style preset changes
  const applyPreset = (presetName: string) => {
    setSelectedStyle(presetName);
    const preset = STYLE_PRESETS[presetName];
    if (preset) {
      if (FONTS.includes(preset.fontFamily)) {
        setSelectedFont(preset.fontFamily);
      }
    }
  };

  // Sync video timeline playback loop
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
      
      // Auto-loop bounds constraint check
      if (video.currentTime >= endTime) {
        video.currentTime = startTime;
        if (!isPlaying) {
          video.pause();
        }
      }
      if (video.currentTime < startTime) {
        video.currentTime = startTime;
      }
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [startTime, endTime, isPlaying]);

  const togglePlayback = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    } else {
      // Seek to start bounds if at or past end
      if (video.currentTime >= endTime || video.currentTime < startTime) {
        video.currentTime = startTime;
      }
      video.play().then(() => {
        setIsPlaying(true);
      }).catch((e) => {
        console.error("Playback block:", e);
      });
    }
  };

  const handleSave = () => {
    // Show toast or simulation update
    alert("Changes saved to video project settings!");
  };

  const handleRender = () => {
    setIsRendering(true);
    setRenderProgress(0);
    setIsRenderComplete(false);

    const steps = [
      { progress: 15, label: "Downloading high-resolution source..." },
      { progress: 35, label: "Applying precise trim cuts..." },
      { progress: 60, label: "Cropping video dimensions to vertical 9:16..." },
      { progress: 85, label: "Generating styled subtitle overlay tracks..." },
      { progress: 100, label: "Compiling output MP4 package..." }
    ];

    let currentStepIdx = 0;
    const interval = setInterval(() => {
      const step = steps[currentStepIdx];
      if (step) {
        setRenderStep(step.label);
        setRenderProgress((prev) => {
          const next = prev + 5;
          if (next >= step.progress) {
            currentStepIdx++;
          }
          return next > 100 ? 100 : next;
        });
      } else {
        clearInterval(interval);
        setIsRenderComplete(true);
      }
    }, 250);
  };

  // Extract active visual subtitle words based on timing bounds
  const getActiveWordIndex = () => {
    return MOCK_WORDS.findIndex(
      (w) => currentTime >= w.start && currentTime <= w.end
    );
  };

  const activeIndex = getActiveWordIndex();
  const currentPreset = STYLE_PRESETS[selectedStyle] || STYLE_PRESETS.Classic;

  return (
    <main className="min-h-screen bg-vc-surface text-white p-4 sm:p-6 md:p-8 flex flex-col font-sans select-none antialiased">
      {/* ── Top Bar / Header ────────────────────────────────────────── */}
      <header className="mb-6 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="p-2 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.08] text-white/70 hover:text-white transition-all"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Shorts Editor</h1>
            <p className="text-xs text-muted-foreground">Adjust styling, position, and trim properties</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={handleSave}
            variant="outline"
            className="rounded-xl border-white/10 text-white/80 bg-white/[0.02] hover:bg-white/[0.08] text-xs h-9 px-4 gap-1.5"
          >
            <Save className="h-4 w-4" />
            Save
          </Button>
          <Button
            onClick={handleRender}
            className="rounded-xl bg-vc-violet hover:bg-vc-violet/90 text-xs h-9 px-4 gap-1.5 font-bold shadow-md shadow-vc-violet/10"
          >
            <Maximize className="h-4 w-4 animate-pulse" />
            Render Video
          </Button>
        </div>
      </header>

      {/* ── Editor Container ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start flex-1">
        
        {/* Left Column: 9:16 Custom Video Preview area */}
        <section className="lg:col-span-7 xl:col-span-8 flex flex-col items-center justify-center p-2 rounded-3xl border border-white/5 bg-white/[0.01] backdrop-blur-3xl min-h-[50vh] lg:min-h-[75vh]">
          <div className="relative aspect-[9/16] w-full max-w-[340px] bg-black rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
            
            {/* The HTML5 video node */}
            <video
              ref={videoRef}
              src={videoUrlParam}
              className="absolute inset-0 h-full w-full object-cover"
              playsInline
              loop
              muted
              onClick={togglePlayback}
              aria-label="Video clip preview — click to play or pause"
              title="Short-form video clip preview"
            />

            {/* Timed subtitle text overlay renderer */}
            {activeIndex !== -1 && (
              <div
                className={cn(
                  "absolute left-4 right-4 pointer-events-none flex flex-col select-none",
                  {
                    "text-left items-start": alignment === "left",
                    "text-center items-center": alignment === "center",
                    "text-right items-end": alignment === "right"
                  }
                )}
                style={{
                  top: `${positionY}%`,
                  transform: "translateY(-50%)"
                }}
              >
                <div
                  className="px-4 py-2 transition-all duration-150 ease-out inline-block max-w-full"
                  style={{
                    fontFamily: selectedFont,
                    fontSize: `${fontSize}px`,
                    fontWeight: currentPreset.fontWeight,
                    color: currentPreset.color,
                    backgroundColor: currentPreset.backgroundColor || "transparent",
                    borderRadius: currentPreset.backgroundColor ? "12px" : "0",
                    // Emulate font outlines using clean css shadow drops
                    textShadow: currentPreset.outlineColor !== "transparent"
                      ? `-1.5px -1.5px 0 ${currentPreset.outlineColor}, 1.5px -1.5px 0 ${currentPreset.outlineColor}, -1.5px 1.5px 0 ${currentPreset.outlineColor}, 1.5px 1.5px 0 ${currentPreset.outlineColor}`
                      : undefined
                  }}
                >
                  {/* Words line mapping */}
                  {MOCK_WORDS.map((w, idx) => {
                    // Render surrounding words inside the timing frame window
                    const minIdx = Math.max(0, activeIndex - 1);
                    const maxIdx = Math.min(MOCK_WORDS.length - 1, activeIndex + 2);
                    
                    if (idx < minIdx || idx > maxIdx) return null;

                    const isActive = idx === activeIndex;
                    return (
                      <span
                        key={idx}
                        className="mx-1 inline-block transition-all duration-150"
                        style={{
                          color: isActive ? currentPreset.highlightColor : undefined,
                          transform: isActive && currentPreset.scaleOnActive ? "scale(1.15)" : "scale(1.0)",
                          fontWeight: isActive ? "bold" : undefined
                        }}
                      >
                        {w.word}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Play/Pause Overlay indicator */}
            {!isPlaying && (
              <div
                onClick={togglePlayback}
                className="absolute inset-0 bg-black/40 flex items-center justify-center cursor-pointer transition-colors hover:bg-black/30"
              >
                <div className="h-16 w-16 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center shadow-lg transform scale-100 hover:scale-105 active:scale-95 transition-all">
                  <Play className="h-7 w-7 text-white fill-white ml-1" />
                </div>
              </div>
            )}
          </div>

          {/* Simple video player scrub control */}
          <div className="w-full max-w-[340px] mt-4 flex items-center justify-between gap-3 bg-white/[0.02] border border-white/5 p-3 rounded-2xl">
            <button
              onClick={togglePlayback}
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/80 hover:text-white transition-colors"
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 fill-white" />}
            </button>
            <div className="flex-1 flex items-center gap-2">
              <span className="text-[10px] text-muted-foreground font-mono">
                {currentTime.toFixed(1)}s
              </span>
              <input
                type="range"
                min={startTime}
                max={endTime}
                step={0.1}
                value={currentTime}
                onChange={(e) => {
                  const video = videoRef.current;
                  if (video) {
                    video.currentTime = parseFloat(e.target.value);
                    setCurrentTime(video.currentTime);
                  }
                }}
                className="flex-1 accent-vc-violet h-1 rounded-lg cursor-pointer bg-white/10"
              />
              <span className="text-[10px] text-muted-foreground font-mono">
                {endTime.toFixed(1)}s
              </span>
            </div>
          </div>
        </section>

        {/* Right Column: Settings & Configuration Controls */}
        <section className="lg:col-span-5 xl:col-span-4 space-y-6 bg-white/[0.02] border border-vc-border/30 p-5 rounded-3xl backdrop-blur-xl shadow-2xl h-full lg:max-h-[75vh] overflow-y-auto">
          
          {/* 1. Trim adjustments */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-vc-pink">
              <Scissors className="h-4 w-4" />
              <h2 className="text-sm font-semibold tracking-wide uppercase">Trim Settings</h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground">Start bounds (seconds)</label>
                <input
                  type="number"
                  min={0}
                  max={endTime - 0.5}
                  step={0.1}
                  value={startTime.toFixed(1)}
                  onChange={(e) => {
                    const val = Math.max(0, parseFloat(e.target.value) || 0);
                    setStartTime(val);
                    if (videoRef.current) videoRef.current.currentTime = val;
                  }}
                  className="w-full text-xs bg-white/5 border border-white/10 p-2.5 rounded-xl text-white font-mono text-center focus:outline-none focus:border-vc-violet"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground">End bounds (seconds)</label>
                <input
                  type="number"
                  min={startTime + 0.5}
                  step={0.1}
                  value={endTime.toFixed(1)}
                  onChange={(e) => {
                    const val = Math.max(startTime + 0.5, parseFloat(e.target.value) || 0);
                    setEndTime(val);
                  }}
                  className="w-full text-xs bg-white/5 border border-white/10 p-2.5 rounded-xl text-white font-mono text-center focus:outline-none focus:border-vc-violet"
                />
              </div>
            </div>
          </div>

          <Separator className="bg-white/5" />

          {/* 2. Style Preset Picker */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-vc-violet">
              <Settings className="h-4 w-4" />
              <h2 className="text-sm font-semibold tracking-wide uppercase">Caption Style Preset</h2>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {Object.keys(STYLE_PRESETS).map((name) => {
                const isActive = selectedStyle === name;
                return (
                  <button
                    key={name}
                    type="button"
                    onClick={() => applyPreset(name)}
                    className={`p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                      isActive
                        ? "border-vc-violet bg-vc-violet/10 text-white shadow-md"
                        : "border-white/5 bg-white/[0.02] text-white/60 hover:bg-white/[0.06] hover:text-white"
                    }`}
                  >
                    {name}
                  </button>
                );
              })}
            </div>
          </div>

          <Separator className="bg-white/5" />

          {/* 3. Typography & Positioning */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-vc-emerald">
              <Type className="h-4 w-4" />
              <h2 className="text-sm font-semibold tracking-wide uppercase">Typography & Positioning</h2>
            </div>

            {/* Font Picker */}
            <div className="space-y-1.5">
              <label className="text-[10px] text-muted-foreground">Font Family</label>
              <select
                value={selectedFont}
                onChange={(e) => setSelectedFont(e.target.value)}
                className="w-full text-xs bg-white/5 border border-white/10 p-2.5 rounded-xl text-white focus:outline-none focus:border-vc-violet"
              >
                {FONTS.map((f) => (
                  <option key={f} value={f} className="bg-vc-surface text-white">
                    {f}
                  </option>
                ))}
              </select>
            </div>

            {/* Font Size slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-muted-foreground">Font Size (px)</span>
                <span className="font-mono text-white/80">{fontSize}px</span>
              </div>
              <input
                type="range"
                min={20}
                max={75}
                value={fontSize}
                onChange={(e) => setFontSize(parseInt(e.target.value))}
                className="w-full accent-vc-violet h-1 rounded-lg bg-white/10"
              />
            </div>

            {/* Horizontal Alignment */}
            <div className="space-y-1.5">
              <label className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">Horizontal Alignment</label>
              <div className="flex rounded-xl border border-white/8 bg-white/[0.03] p-1 gap-1">
                {(["left", "center", "right"] as const).map((align) => (
                  <button
                    key={align}
                    type="button"
                    onClick={() => setAlignment(align)}
                    className={cn(
                      "flex-1 rounded-lg text-xs py-1.5 capitalize font-semibold transition-all cursor-pointer",
                      alignment === align
                        ? "bg-vc-violet text-white shadow-sm"
                        : "text-white/60 hover:text-white"
                    )}
                  >
                    {align}
                  </button>
                ))}
              </div>
            </div>

            {/* Vertical Preset */}
            <div className="space-y-1.5">
              <label className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">Vertical Position Preset</label>
              <div className="flex rounded-xl border border-white/8 bg-white/[0.03] p-1 gap-1">
                {(["top", "center", "bottom"] as const).map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setVerticalPreset(preset)}
                    className={cn(
                      "flex-1 rounded-lg text-xs py-1.5 capitalize font-semibold transition-all cursor-pointer",
                      verticalPreset === preset
                        ? "bg-vc-violet text-white shadow-sm"
                        : "text-white/60 hover:text-white"
                    )}
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>

            {/* Vertical Offset */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-muted-foreground">Vertical Position Offset</span>
                <span className="font-mono text-white/80">
                  {verticalOffset > 0 ? `+${verticalOffset}` : verticalOffset}%
                </span>
              </div>
              <input
                type="range"
                min={-15}
                max={15}
                value={verticalOffset}
                onChange={(e) => setVerticalOffset(parseInt(e.target.value))}
                className="w-full accent-vc-violet h-1 rounded-lg bg-white/10"
              />
              <div className="flex justify-between text-[8px] text-muted-foreground font-mono">
                <span>-15% (Higher)</span>
                <span>Calculated position: {positionY}%</span>
                <span>+15% (Lower)</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* ── Fullscreen Rendering Loader Overlay ─────────────────────── */}
      {isRendering && (
        <div className="fixed inset-0 z-50 bg-vc-surface/95 backdrop-blur-xl flex flex-col items-center justify-center p-6 text-center animate-fade-in">
          <div className="max-w-md w-full space-y-6">
            
            {/* Visual state handler */}
            {!isRenderComplete ? (
              <>
                <div className="relative flex items-center justify-center">
                  <div className="h-24 w-24 rounded-full border-2 border-white/5 flex items-center justify-center animate-pulse" />
                  <Loader2 className="absolute h-10 w-10 text-vc-violet animate-spin" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-white">Rendering Video...</h3>
                  <p className="text-sm text-muted-foreground font-mono">{renderStep}</p>
                </div>
                <div className="space-y-1">
                  <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/10">
                    <div
                      className="bg-vc-violet h-full transition-all duration-300 ease-out"
                      style={{ width: `${renderProgress}%` }}
                    />
                  </div>
                  <div className="flex justify-end text-[10px] text-muted-foreground font-mono">
                    {renderProgress}%
                  </div>
                </div>
              </>
            ) : (
              <div className="space-y-6 animate-scale-in">
                <div className="flex items-center justify-center">
                  <div className="h-20 w-20 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <CheckCircle2 className="h-10 w-10" />
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-white">Rendering Complete!</h3>
                  <p className="text-sm text-muted-foreground">Your social-media Short is optimized and ready to post.</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-3 pt-2 justify-center">
                  <a
                    href={videoUrlParam}
                    download="viralcut-short.mp4"
                    className="gradient-cta rounded-xl px-6 py-3 font-semibold text-sm flex items-center justify-center gap-2 shadow-lg shadow-vc-violet/20"
                  >
                    <Download className="h-4 w-4" />
                    Download Optimized Short
                  </a>
                  <button
                    onClick={() => {
                      setIsRendering(false);
                      setIsRenderComplete(false);
                      router.push("/dashboard");
                    }}
                    className="rounded-xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.08] px-6 py-3 font-semibold text-sm transition-colors"
                  >
                    Back to Dashboard
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
