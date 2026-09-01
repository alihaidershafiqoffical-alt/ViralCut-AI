// =============================================================================
// components/sections/VideoInput.tsx — Dual-tab input for Upload + Paste URL.
// The URL tab now has full lifecycle: paste, validate, loading, error states,
// unsupported-source messaging, processing progress, and clear/remove.
// =============================================================================
"use client";

import React, { useState, useCallback, useRef, type DragEvent, type ChangeEvent } from "react";
import {
  Upload,
  Link2,
  FileVideo,
  AlertCircle,
  X,
  CheckCircle,
  ShieldCheck,
  LockIcon,
  ClipboardPaste,
  Loader2,
  AlertTriangle,
  Info,
} from "lucide-react";
import type { InputTab, VideoSource } from "@/types/index";
import { API_URL } from "@/lib/config";
import { formatFileSize } from "@/lib/formatters";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Progress } from "@/components/ui/Progress";
import { useVideoUpload } from "@/hooks/useVideoUpload";
import { useUrlIngest } from "@/hooks/useUrlIngest";

const ACCEPTED_MIME  = ["video/mp4", "video/quicktime", "video/webm", "video/x-matroska"];
const ACCEPTED_EXT   = ".mp4, .mov, .webm, .mkv";
const MAX_BYTES      = 2 * 1024 * 1024 * 1024; // 2 GB

/** Sources the backend actively supports. */
const SUPPORTED_SOURCES = [
  { icon: "▶", name: "YouTube", desc: "Public videos & Shorts" },
  { icon: "🔗", name: "Direct links", desc: ".mp4, .mov, .webm, .mkv" },
];

interface Props {
  onSourceSelected: (source: VideoSource) => void;
  disabled?: boolean;
}

// ---------------------------------------------------------------------------
// Tab button component
// ---------------------------------------------------------------------------
function TabBtn({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`
        flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-t-xl
        transition-all duration-200 border-b-2
        ${active
          ? "border-violet-500 text-violet-300 bg-violet-500/[0.08]"
          : "border-transparent text-white/40 hover:text-white/70 hover:bg-white/[0.04]"
        }
      `}
    >
      {icon}
      {label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------
export default function VideoInput({ onSourceSelected, disabled = false }: Props) {
  const [activeTab, setActiveTab]       = useState<InputTab>("upload");
  const [isDragOver, setIsDragOver]     = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError]              = useState<string | null>(null);
  const fileInputRef                    = useRef<HTMLInputElement>(null);

  // Upload hook (file tab)
  const { upload, cancel, progress, status: uploadStatus, error: uploadError } = useVideoUpload();

  // URL ingest hook (url tab)
  const [urlValue, setUrlValue] = useState("");
  const urlIngest = useUrlIngest();

  // Storage status check
  const [storageStatus, setStorageStatus] = useState<"READY" | "BUSY" | "TEMPORARILY_UNAVAILABLE" | null>(null);

  React.useEffect(() => {
    const checkStorageStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/videos/storage-status`);
        if (response.ok) {
          const data = await response.json();
          setStorageStatus(data.status);
        }
      } catch (err) {
        console.error("Failed to check storage status:", err);
      }
    };
    checkStorageStatus();
    const interval = setInterval(checkStorageStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const clearError  = () => setError(null);
  const clearFile   = () => {
    if (uploadStatus === "uploading") cancel();
    setSelectedFile(null);
    clearError();
  };
  const clearUrl = () => {
    setUrlValue("");
    urlIngest.reset();
    clearError();
  };

  // ---------------------------------------------------------------------------
  // File validation & handlers (Upload tab — unchanged)
  // ---------------------------------------------------------------------------
  function validateFile(file: File): string | null {
    const ext = file.name.split(".").pop()?.toLowerCase();
    const validExts = ["mp4", "mov", "webm", "mkv"];
    const isMimeValid = ACCEPTED_MIME.includes(file.type);
    const isExtValid = ext ? validExts.includes(ext) : false;

    if (!isMimeValid && !isExtValid) return `Unsupported format. Accepted: MP4, MOV, WebM, MKV.`;
    if (file.size > MAX_BYTES)              return `File too large (${formatFileSize(file.size)}). Max: 2 GB.`;
    return null;
  }

  const handleFile = useCallback((file: File) => {
    clearError();
    const err = validateFile(file);
    if (err) { setError(err); return; }
    setSelectedFile(file);
  }, []);

  const onDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onDragOver  = (e: DragEvent<HTMLDivElement>) => { e.preventDefault(); setIsDragOver(true);  };
  const onDragLeave = (e: DragEvent<HTMLDivElement>) => { e.preventDefault(); setIsDragOver(false); };

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  async function handleUploadSubmit() {
    if (!selectedFile) return;
    const result = await upload(selectedFile);
    if (result) {
      onSourceSelected({
        type: "upload",
        file: selectedFile,
        displayName: selectedFile.name,
        sizeBytes: selectedFile.size,
        videoId: result.videoId,
      });
    }
  }

  // ---------------------------------------------------------------------------
  // URL submission handler
  // ---------------------------------------------------------------------------
  async function handleUrlSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const result = await urlIngest.submit(urlValue);
    if (result) {
      const hostname = (() => {
        try {
          return new URL(urlValue.startsWith("http") ? urlValue : `https://${urlValue}`).hostname;
        } catch {
          return result.provider;
        }
      })();

      onSourceSelected({
        type: "url",
        url: urlValue.trim(),
        displayName: hostname,
        sizeBytes: result.sizeBytes,
        videoId: result.jobId,
        provider: result.provider,
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Clipboard paste handler
  // ---------------------------------------------------------------------------
  async function handlePasteFromClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      if (text?.trim()) {
        setUrlValue(text.trim());
        urlIngest.reset();
      }
    } catch {
      // Clipboard API not available or permission denied — do nothing
    }
  }

  // ---------------------------------------------------------------------------
  // Derived state for URL tab
  // ---------------------------------------------------------------------------
  const isUrlSubmitting = urlIngest.status === "submitting" || urlIngest.status === "validating";
  const isUrlUnsupported = urlIngest.status === "unsupported";
  const isUrlError = urlIngest.status === "error";
  const isUrlSuccess = urlIngest.status === "success";
  const hasUrlValue = urlValue.trim().length > 0;

  return (
    <section
      id="video-input"
      className="mx-auto max-w-2xl w-full px-4 animate-slide-up stagger-3"
      aria-label="Video source input"
    >
      {/* ── Tab bar ── */}
      <div className="flex border-b border-white/[0.08]" role="tablist" aria-label="Input method">
        <TabBtn
          active={activeTab === "upload"}
          onClick={() => { setActiveTab("upload"); clearError(); }}
          icon={<Upload className="h-4 w-4" />}
          label="Upload Video"
        />
        <TabBtn
          active={activeTab === "url"}
          onClick={() => { setActiveTab("url"); clearError(); }}
          icon={<Link2 className="h-4 w-4" />}
          label="Paste URL"
        />
      </div>

      {/* ── Storage Status Alerts ── */}
      {storageStatus === "BUSY" && (
        <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-amber-500/20 bg-amber-500/[0.06] px-4 py-3 animate-fade-in">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-amber-300">System is Busy</p>
            <p className="text-xs text-white/50 mt-0.5">Temporary processing storage is currently busy. Please try again in a few minutes.</p>
          </div>
        </div>
      )}

      {storageStatus === "TEMPORARILY_UNAVAILABLE" && (
        <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 animate-fade-in">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-red-300">Storage Busy</p>
            <p className="text-xs text-white/50 mt-0.5">Temporary processing storage is currently busy. Please try again later.</p>
          </div>
        </div>
      )}

      {disabled && (
        <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-amber-500/20 bg-amber-500/[0.06] px-4 py-3 animate-fade-in">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-amber-300">Active processing limit reached</p>
            <p className="text-xs text-white/50 mt-0.5">You currently have 2 active video processing tasks running. Please wait for one to complete before adding another video.</p>
          </div>
        </div>
      )}

      {/* ── Tab panels ── */}
      <div className="mt-px">

        {/* ================================================================
            UPLOAD TAB (unchanged)
            ================================================================ */}
        {activeTab === "upload" && (
          <div role="tabpanel" aria-label="Upload file panel" className="animate-fade-in">
            {selectedFile ? (
              <div className="glass rounded-b-2xl rounded-tr-2xl p-5 flex flex-col gap-4">
                <div className="flex flex-col sm:flex-row items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-violet-500/15">
                    <FileVideo className="h-6 w-6 text-violet-400" />
                  </div>
                  <div className="flex-1 min-w-0 text-center sm:text-left w-full">
                    <p className="text-sm font-medium text-white truncate">{selectedFile.name}</p>
                    <div className="flex items-center justify-center sm:justify-start gap-2 mt-0.5">
                      <p className="text-xs text-white/40">{formatFileSize(selectedFile.size)}</p>
                      {uploadStatus === "uploading" && (
                        <>
                          <span className="text-white/20">•</span>
                          <p className="text-xs font-medium text-violet-400">{progress}% Uploaded</p>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto mt-2 sm:mt-0">
                    <button
                      type="button"
                      onClick={clearFile}
                      disabled={uploadStatus === "uploading"}
                      className="p-2.5 rounded-lg text-white/40 hover:text-white/80 hover:bg-white/[0.06] transition-colors disabled:opacity-50"
                      aria-label="Remove selected file"
                    >
                      <X className="h-5 w-5" />
                    </button>
                    {uploadStatus === "uploading" ? (
                      <Button onClick={cancel} variant="outline" className="flex-1 sm:flex-none py-3 border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300">
                        Cancel Upload
                      </Button>
                    ) : (
                      <Button onClick={handleUploadSubmit} variant="primary" className="flex-1 sm:flex-none py-3" disabled={storageStatus === "TEMPORARILY_UNAVAILABLE"}>
                        {uploadStatus === "error" || uploadStatus === "cancelled" ? "Retry Upload" : "Upload & Continue"}
                      </Button>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                {uploadStatus === "uploading" && (
                  <div className="w-full px-1 animate-fade-in">
                    <Progress value={progress} className="h-1.5" />
                  </div>
                )}
              </div>
            ) : (
              <div
                role="button"
                tabIndex={0}
                aria-label="Click or drag and drop to upload a video"
                onClick={() => !disabled && fileInputRef.current?.click()}
                onKeyDown={(e) => e.key === "Enter" && !disabled && fileInputRef.current?.click()}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                className={`
                  glass rounded-b-2xl rounded-tr-2xl
                  border-2 border-dashed
                  flex flex-col items-center justify-center
                  py-16 px-6 text-center cursor-pointer
                  transition-all duration-300 select-none
                  ${isDragOver
                    ? "border-violet-500 bg-violet-500/[0.06] shadow-[0_0_40px_rgba(124,58,237,0.15)]"
                    : "border-white/[0.12] hover:border-violet-500/50 hover:bg-violet-500/[0.02]"
                  }
                  ${disabled ? "opacity-40 pointer-events-none" : ""}
                `}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_MIME.join(",")}
                  onChange={onFileChange}
                  className="sr-only"
                  aria-hidden="true"
                  disabled={disabled || uploadStatus === "uploading" || storageStatus === "TEMPORARILY_UNAVAILABLE"}
                />

                <div className={`mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.05] transition-transform duration-300 ${isDragOver ? "scale-110" : ""}`}>
                  <Upload className={`h-7 w-7 ${isDragOver ? "text-violet-400" : "text-white/40"}`} />
                </div>

                <p className="text-base font-semibold text-white mb-1">
                  {storageStatus === "TEMPORARILY_UNAVAILABLE"
                    ? "Storage is currently busy"
                    : isDragOver ? "Drop video to select" : "Drag & drop your video here"}
                </p>
                <p className="text-sm text-white/40 mb-4">
                  or <span className="text-violet-400 font-medium hover:underline">browse files</span>
                </p>
                <p className="text-xs text-white/30 font-mono bg-white/[0.03] px-3 py-1 rounded-md">
                  Supported: {ACCEPTED_EXT} • Max 2GB
                </p>
              </div>
            )}
          </div>
        )}

        {/* ================================================================
            URL TAB — Full lifecycle UI
            ================================================================ */}
        {activeTab === "url" && (
          <div role="tabpanel" aria-label="Paste URL panel" className="animate-fade-in">
            <div className="glass rounded-b-2xl rounded-tr-2xl p-5 sm:p-6 space-y-5">

              {/* ── Input row ── */}
              <form onSubmit={handleUrlSubmit} noValidate>
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="flex-1 relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none z-10">
                      <Link2 className="h-5 w-5 text-white/30" />
                    </div>
                    <Input
                      id="video-url"
                      type="url"
                      value={urlValue}
                      onChange={(e) => { setUrlValue(e.target.value); if (urlIngest.status !== "idle") urlIngest.reset(); }}
                      placeholder="https://youtube.com/watch?v=..."
                      autoComplete="off"
                      spellCheck={false}
                      disabled={disabled || isUrlSubmitting}
                      className="pl-10 pr-20 py-5 h-auto text-base rounded-xl bg-white/[0.03]"
                      aria-label="Video URL input"
                    />

                    {/* Right side action buttons inside input */}
                    <div className="absolute inset-y-0 right-0 pr-2 flex items-center gap-1">
                      {/* Paste button */}
                      {!disabled && !hasUrlValue && !isUrlSubmitting && (
                        <button
                          type="button"
                          onClick={handlePasteFromClipboard}
                          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-violet-400 hover:text-violet-300 hover:bg-violet-500/10 transition-all duration-150"
                          title="Paste from clipboard"
                        >
                          <ClipboardPaste className="h-3.5 w-3.5" />
                          <span className="hidden sm:inline">Paste</span>
                        </button>
                      )}

                      {/* Clear button (when there's text) */}
                      {hasUrlValue && !isUrlSubmitting && (
                        <button
                          type="button"
                          onClick={clearUrl}
                          className="p-1.5 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/[0.06] transition-colors"
                          aria-label="Clear URL"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}

                      {/* Spinner inside input during submission */}
                      {isUrlSubmitting && (
                        <div className="p-1.5">
                          <Loader2 className="h-4 w-4 text-violet-400 animate-spin" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Submit / Cancel button */}
                  {isUrlSubmitting ? (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={urlIngest.cancel}
                      className="py-5 h-auto sm:w-auto px-8 rounded-xl font-semibold whitespace-nowrap border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                    >
                      Cancel
                    </Button>
                  ) : (
                    <Button
                      type="submit"
                      variant="primary"
                      disabled={disabled || !hasUrlValue || storageStatus === "TEMPORARILY_UNAVAILABLE"}
                      className="py-5 h-auto sm:w-auto px-8 rounded-xl font-semibold whitespace-nowrap disabled:opacity-40"
                    >
                      {isUrlError || isUrlUnsupported ? "Retry" : "Create Shorts"}
                    </Button>
                  )}
                </div>
              </form>

              {/* ── Loading / Processing state ── */}
              {isUrlSubmitting && (
                <div className="animate-fade-in">
                  <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-violet-500/[0.06] border border-violet-500/15">
                    <div className="relative flex items-center justify-center h-8 w-8 shrink-0">
                      <div
                        className="absolute inset-0 rounded-full border-2 border-transparent"
                        style={{
                          background: "conic-gradient(from 0deg, #7c3aed, #4f46e5, #ec4899, #7c3aed) border-box",
                          WebkitMask: "linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0)",
                          WebkitMaskComposite: "destination-out",
                          maskComposite: "exclude",
                          animation: "spin-slow 2s linear infinite",
                        }}
                      />
                      <Loader2 className="h-4 w-4 text-violet-400" style={{ animation: "spin-slow 1.5s linear infinite" }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white">Validating and downloading…</p>
                      <p className="text-xs text-white/35 mt-0.5">Checking video source, this may take a moment for longer videos.</p>
                    </div>
                  </div>
                  {/* Indeterminate shimmer bar */}
                  <div className="mt-3 h-1 w-full rounded-full overflow-hidden bg-white/[0.04]">
                    <div className="h-full w-full shimmer-bar rounded-full" />
                  </div>
                </div>
              )}

              {/* ── Unsupported source message ── */}
              {isUrlUnsupported && urlIngest.error && (
                <div className="animate-slide-down" role="alert">
                  <div className="flex gap-3 p-4 rounded-xl bg-amber-500/[0.06] border border-amber-500/20">
                    <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-amber-300">Unsupported video source</p>
                      <p className="text-sm text-white/50 leading-relaxed">{urlIngest.error.message}</p>
                      <div className="flex flex-wrap gap-2 mt-3">
                        {SUPPORTED_SOURCES.map((src) => (
                          <span
                            key={src.name}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/[0.04] border border-white/[0.08] text-xs text-white/60"
                          >
                            <span>{src.icon}</span>
                            <span className="font-medium text-white/70">{src.name}</span>
                            <span className="text-white/30">—</span>
                            <span>{src.desc}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── Generic error state ── */}
              {isUrlError && urlIngest.error && !isUrlUnsupported && (
                <div className="animate-slide-down" role="alert">
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/[0.06] border border-red-500/20">
                    <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-red-300">Something went wrong</p>
                      <p className="text-sm text-white/50 mt-1 leading-relaxed">{urlIngest.error.message}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* ── Success confirmation (briefly shown before stage transition) ── */}
              {isUrlSuccess && (
                <div className="animate-scale-in" role="status">
                  <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/[0.06] border border-emerald-500/20">
                    <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-emerald-300">Video accepted!</p>
                      <p className="text-xs text-white/40 mt-0.5">Proceeding to clip settings…</p>
                    </div>
                  </div>
                </div>
              )}

              {/* ── Supported sources info (shown when idle and no URL) ── */}
              {!hasUrlValue && urlIngest.status === "idle" && (
                <div className="animate-fade-in">
                  <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                    <Info className="h-4 w-4 text-violet-400/60 shrink-0 mt-0.5" />
                    <div className="space-y-2">
                      <p className="text-xs text-white/40 leading-relaxed">
                        Only supported and authorized video sources can be processed.
                        We verify each link for safety and compatibility before downloading.
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {SUPPORTED_SOURCES.map((src) => (
                          <span
                            key={src.name}
                            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/[0.03] text-xs text-white/45"
                          >
                            <span>{src.icon}</span>
                            <span className="font-medium text-white/55">{src.name}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

            </div>
          </div>
        )}
      </div>

      {/* ── Global error (file tab) ── */}
      {(error || uploadError) && (
        <div role="alert" className="mt-4 flex items-center justify-center gap-2 text-sm text-red-400 animate-slide-down">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error || uploadError}</span>
        </div>
      )}

      {/* ── Privacy / No Login Notices ── */}
      <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 text-xs text-white/40">
        <div className="flex items-center gap-2">
          <LockIcon className="h-3.5 w-3.5 text-violet-400/70" />
          <span>No login or credit card required</span>
        </div>
        <div className="hidden sm:block text-white/20">•</div>
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400/70" />
          <span>Videos are processed privately & auto-deleted</span>
        </div>
      </div>
    </section>
  );
}
