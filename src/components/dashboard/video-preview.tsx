// =============================================================================
// components/dashboard/video-preview.tsx — Fully Responsive, Multi-Aspect-Ratio
// Visual Video Preview Component with Dynamic HTML Subtitle Timing Overlay.
// Supports custom typography presets, Y-positions, and device alignments.
// =============================================================================
"use client";

import React, { useState, useRef, useEffect, KeyboardEvent } from "react";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { VideoPreviewProps, AspectRatioPreset } from "@/types/index";

// ---------------------------------------------------------------------------
// Aspect Ratio Presets Configuration
// Mapped exactly to backend rendering choices.
// ---------------------------------------------------------------------------
export const ASPECT_RATIO_PRESETS: Record<
  "9:16" | "4:5" | "3:4" | "1:1" | "2:3",
  AspectRatioPreset
> = {
  "9:16": {
    width: 1080,
    height: 1920,
    label: "Vertical (9:16)",
    cssRatio: "9/16"
  },
  "4:5": {
    width: 1080,
    height: 1350,
    label: "Portrait (4:5)",
    cssRatio: "4/5"
  },
  "3:4": {
    width: 1080,
    height: 1440,
    label: "Portrait (3:4)",
    cssRatio: "3/4"
  },
  "1:1": {
    width: 1080,
    height: 1080,
    label: "Square (1:1)",
    cssRatio: "1/1"
  },
  "2:3": {
    width: 1080,
    height: 1620,
    label: "Portrait (2:3)",
    cssRatio: "2/3"
  }
};

// Default fallback subtitle segments if captions parameter is empty
const MOCK_CAPTION_WORDS = [
  { word: "This", start: 0.2, end: 0.6 },
  { word: "preview", start: 0.7, end: 1.2 },
  { word: "adapts", start: 1.3, end: 1.8 },
  { word: "to", start: 1.9, end: 2.1 },
  { word: "any", start: 2.2, end: 2.5 },
  { word: "ratio,", start: 2.6, end: 3.2 },
  { word: "including", start: 3.3, end: 3.8 },
  { word: "vertical,", start: 3.9, end: 4.5 },
  { word: "square,", start: 4.6, end: 5.2 },
  { word: "or", start: 5.3, end: 5.5 },
  { word: "portrait.", start: 5.6, end: 6.2 },
  { word: "Style", start: 6.5, end: 6.8 },
  { word: "properties", start: 6.9, end: 7.5 },
  { word: "and", start: 7.6, end: 7.8 },
  { word: "karaoke", start: 7.9, end: 8.4 },
  { word: "highlights", start: 8.5, end: 9.1 },
  { word: "render", start: 9.2, end: 9.6 },
  { word: "instantly.", start: 9.7, end: 10.5 }
];

export function VideoPreview({
  videoUrl,
  aspectRatio = "9:16",
  captions,
  captionSettings
}: VideoPreviewProps) {
  // Elements Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // States
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);

  // Active aspect configuration
  const currentPreset = ASPECT_RATIO_PRESETS[aspectRatio] || ASPECT_RATIO_PRESETS["9:16"];

  // Timing update listener
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handleDurationChange = () => {
      setDuration(video.duration || 0);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("durationchange", handleDurationChange);
    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("durationchange", handleDurationChange);
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
    };
  }, [videoUrl]);

  // Adjust volume settings
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.volume = isMuted ? 0 : volume;
    video.muted = isMuted;
  }, [volume, isMuted]);

  // Handle auto control hiding when playing
  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    const timer = setTimeout(() => {
      setShowControls(false);
    }, 2500);

    return () => clearTimeout(timer);
  }, [isPlaying, currentTime]);

  // Playback control toggle
  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play().catch((e) => console.warn("Autoplay block:", e));
    }
  };

  // Mute volume toggle
  const toggleMute = () => {
    setIsMuted((prev) => !prev);
  };

  // Fullscreen trigger
  const toggleFullscreen = () => {
    const container = containerRef.current;
    if (!container) return;

    if (!document.fullscreenElement) {
      container.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch((err) => {
        console.error("Fullscreen request failed:", err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  };

  // Monitor escape fullscreen binds
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  // Format MM:SS strings
  const formatTime = (seconds: number) => {
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  };

  // Keyboard navigation accessibility binds
  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === " ") {
      e.preventDefault();
      togglePlay();
    } else if (e.key === "m" || e.key === "M") {
      e.preventDefault();
      toggleMute();
    } else if (e.key === "f" || e.key === "F") {
      e.preventDefault();
      toggleFullscreen();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setVolume((prev) => Math.min(1.0, prev + 0.1));
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setVolume((prev) => Math.max(0.0, prev - 0.1));
    }
  };

  // Extract flattened words list from captions if provided, otherwise default fallback list
  const getFlattenedWords = () => {
    if (captions && captions.length > 0) {
      return captions.flatMap((seg) => seg.words);
    }
    return MOCK_CAPTION_WORDS;
  };

  const wordsList = getFlattenedWords();
  
  // Find which word is currently spoken (active)
  const activeWordIdx = wordsList.findIndex(
    (w) => currentTime >= w.start && currentTime <= w.end
  );

  // Group surrounding words for readability overlay window
  const getSubtitlesWindow = () => {
    if (activeWordIdx === -1) return [];
    
    // Renders the active word and up to 2 trailing/leading words in the phrase bounds
    const startWindow = Math.max(0, activeWordIdx - 1);
    const endWindow = Math.min(wordsList.length - 1, activeWordIdx + 2);
    
    return wordsList.slice(startWindow, endWindow + 1);
  };

  const visibleWords = getSubtitlesWindow();

  // CSS Alignment Mapping
  const alignmentStyles = {
    left: "text-left items-start",
    center: "text-center items-center",
    right: "text-right items-end"
  }[captionSettings.alignment];

  // Emulate font stroke outlines using drop shadow filters
  const outlineStyles = captionSettings.outlineColor !== "transparent" && captionSettings.outlineWidth > 0
    ? {
        textShadow: `
          -${captionSettings.outlineWidth}px -${captionSettings.outlineWidth}px 0 ${captionSettings.outlineColor}, 
           ${captionSettings.outlineWidth}px -${captionSettings.outlineWidth}px 0 ${captionSettings.outlineColor}, 
          -${captionSettings.outlineWidth}px  ${captionSettings.outlineWidth}px 0 ${captionSettings.outlineColor}, 
           ${captionSettings.outlineWidth}px  ${captionSettings.outlineWidth}px 0 ${captionSettings.outlineColor}
        `
      }
    : {};

  return (
    <div
      ref={containerRef}
      onKeyDown={handleKeyDown}
      onMouseMove={() => setShowControls(true)}
      tabIndex={0}
      aria-label="Interactive Video Preview Player"
      className="relative flex flex-col justify-center items-center w-full focus:outline-none select-none"
    >
      {/* ── Outer aspect scale boundary capsule ── */}
      <div
        className={cn(
          "relative overflow-hidden bg-zinc-950 rounded-2xl border border-white/10 shadow-2xl transition-all duration-300 w-full",
          isFullscreen ? "max-h-screen rounded-none border-none" : "max-h-[65vh] max-w-sm sm:max-w-md md:max-w-lg lg:max-w-xl"
        )}
        style={{
          aspectRatio: currentPreset.cssRatio
        }}
      >
        {/* HTML5 video element */}
        <video
          ref={videoRef}
          src={videoUrl}
          playsInline
          className="h-full w-full object-cover cursor-pointer"
          onClick={togglePlay}
        />

        {/* ── Visual Timed Subtitle Caption Overlay ── */}
        {activeWordIdx !== -1 && visibleWords.length > 0 && (
          <div
            className={cn(
              "absolute left-4 right-4 pointer-events-none select-none flex flex-col transition-all duration-200",
              alignmentStyles
            )}
            style={{
              top: `${captionSettings.verticalPosition}%`,
              transform: "translateY(-50%)"
            }}
          >
            <div
              className={cn(
                "px-4 py-2 transition-all duration-150 ease-out inline-block max-w-full"
              )}
              style={{
                fontFamily: captionSettings.font,
                fontSize: `${captionSettings.fontSize}px`,
                fontWeight: captionSettings.fontWeight,
                color: captionSettings.textColor,
                backgroundColor: captionSettings.backgroundColor || "transparent",
                padding: captionSettings.backgroundColor ? (captionSettings.backgroundPadding || "6px 12px") : undefined,
                borderRadius: captionSettings.backgroundColor ? (captionSettings.backgroundRadius || "8px") : undefined,
                textAlign: captionSettings.alignment,
                ...outlineStyles
              }}
            >
              {visibleWords.map((w, idx) => {
                // Determine if this is the active word
                const isWordActive = w.start <= currentTime && currentTime <= w.end;
                
                return (
                  <span
                    key={idx}
                    className="mx-1 inline-block transition-all duration-150"
                    style={{
                      color: isWordActive && captionSettings.karaokeActive ? captionSettings.highlightColor : undefined,
                      transform: isWordActive && captionSettings.karaokeActive && captionSettings.highlightScale > 1.0
                        ? `scale(${captionSettings.highlightScale})`
                        : "scale(1.0)",
                      fontWeight: isWordActive ? "bold" : undefined
                    }}
                  >
                    {w.word}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Playback Toggle Center Ring ── */}
        {!isPlaying && (
          <div
            onClick={togglePlay}
            className="absolute inset-0 bg-black/40 flex items-center justify-center cursor-pointer transition-all duration-300 hover:bg-black/35"
          >
            <div className="h-16 w-16 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center shadow-lg transform scale-100 hover:scale-105 active:scale-95 transition-all">
              <Play className="h-7 w-7 text-white fill-white ml-1" />
            </div>
          </div>
        )}

        {/* ── Bottom Controls bar ── */}
        <div
          className={cn(
            "absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent flex flex-col gap-2 transition-opacity duration-300 pointer-events-auto border-t border-white/5",
            showControls ? "opacity-100" : "opacity-0 pointer-events-none"
          )}
        >
          {/* Seek Progress Slider */}
          <div className="w-full flex items-center gap-2">
            <input
              type="range"
              min={0}
              max={duration || 100}
              step={0.1}
              value={currentTime}
              onChange={(e) => {
                const video = videoRef.current;
                if (video) {
                  video.currentTime = parseFloat(e.target.value);
                  setCurrentTime(video.currentTime);
                }
              }}
              className="w-full accent-vc-violet h-1 rounded-lg cursor-pointer bg-white/20 hover:bg-white/30 transition-all focus:outline-none"
              aria-label="Video Timeline Seek Scrub Bar"
            />
          </div>

          <div className="flex items-center justify-between gap-4">
            {/* Play/Pause + Timings */}
            <div className="flex items-center gap-3">
              <button
                onClick={togglePlay}
                className="p-1 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all focus:outline-none"
                aria-label={isPlaying ? "Pause video" : "Play video"}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 fill-white" />}
              </button>
              
              <div className="text-[11px] font-mono text-white/80 select-none">
                {formatTime(currentTime)} <span className="text-white/30">/</span> {formatTime(duration)}
              </div>
            </div>

            {/* Volume + Screen Maximize */}
            <div className="flex items-center gap-4">
              {/* Volume sliders control */}
              <div className="flex items-center gap-1.5 group/volume">
                <button
                  onClick={toggleMute}
                  className="p-1 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all focus:outline-none"
                  aria-label={isMuted ? "Unmute sound" : "Mute sound"}
                >
                  {isMuted || volume === 0 ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                </button>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={isMuted ? 0 : volume}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    setVolume(val);
                    if (val > 0) setIsMuted(false);
                  }}
                  className="w-0 group-hover/volume:w-16 h-1 accent-white rounded-lg bg-white/20 transition-all cursor-pointer focus:outline-none"
                  aria-label="Volume Slider bar"
                />
              </div>

              {/* Fullscreen control */}
              <button
                onClick={toggleFullscreen}
                className="p-1 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-all focus:outline-none"
                aria-label={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
              >
                {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
