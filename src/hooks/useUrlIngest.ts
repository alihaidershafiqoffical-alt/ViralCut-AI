// =============================================================================
// hooks/useUrlIngest.ts — Manages the URL ingestion lifecycle.
// Validates client-side, submits to POST /api/v1/videos/ingest-url, and exposes
// status, progress simulation, and error state to the consuming component.
// =============================================================================

import { useState, useCallback, useRef } from "react";
import axios, { type AxiosError } from "axios";
import { API_URL } from "../lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type UrlIngestStatus =
  | "idle"
  | "validating"
  | "submitting"
  | "success"
  | "error"
  | "unsupported";

export interface UrlIngestResult {
  jobId: string;
  provider: string;
  message: string;
  sizeBytes: number;
}

export interface UrlIngestError {
  /** User-facing message */
  message: string;
  /** HTTP status code, if available */
  statusCode?: number;
  /** Whether this is an unsupported-source error (400) */
  isUnsupported: boolean;
}

// ---------------------------------------------------------------------------
// Supported source patterns (client-side pre-check)
// ---------------------------------------------------------------------------

const SUPPORTED_PATTERNS: { label: string; regex: RegExp }[] = [
  {
    label: "YouTube",
    regex: /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)/i,
  },
  {
    label: "Direct video link",
    regex: /^https?:\/\/.+\.(mp4|mov|webm|mkv)(\?.*)?$/i,
  },
];

function isLikelySupported(url: string): boolean {
  return SUPPORTED_PATTERNS.some((p) => p.regex.test(url));
}

function isValidUrl(url: string): boolean {
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    return u.protocol === "https:" || u.protocol === "http:";
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useUrlIngest() {
  const [status, setStatus] = useState<UrlIngestStatus>("idle");
  const [error, setError] = useState<UrlIngestError | null>(null);
  const [result, setResult] = useState<UrlIngestResult | null>(null);

  // For cancel support
  const abortRef = useRef<AbortController | null>(null);

  /**
   * Validate + submit the URL to the backend.
   * Returns the UrlIngestResult on success, null otherwise.
   */
  const submit = useCallback(async (rawUrl: string): Promise<UrlIngestResult | null> => {
    const url = rawUrl.trim();

    // ── Client-side validation ──
    setError(null);
    setResult(null);
    setStatus("validating");

    if (!url) {
      setStatus("error");
      setError({ message: "Please enter a video URL.", isUnsupported: false });
      return null;
    }

    if (!isValidUrl(url)) {
      setStatus("error");
      setError({ message: "That doesn't look like a valid URL. Check for typos and try again.", isUnsupported: false });
      return null;
    }

    if (!isLikelySupported(url)) {
      setStatus("unsupported");
      setError({
        message: "This video source isn't supported yet. We currently accept YouTube links and direct video file URLs (.mp4, .mov, .webm, .mkv).",
        isUnsupported: true,
      });
      return null;
    }

    // ── Submit to backend ──
    setStatus("submitting");
    abortRef.current = new AbortController();

    try {
      const response = await axios.post<UrlIngestResult>(
        `${API_URL}/api/v1/videos/ingest-url`,
        { url },
        {
          signal: abortRef.current.signal,
          headers: { "Content-Type": "application/json" },
          timeout: 120_000, // 2 min timeout for slow downloads
        },
      );

      const data: UrlIngestResult = {
        jobId: response.data.jobId,
        provider: response.data.provider,
        message: response.data.message,
        sizeBytes: response.data.sizeBytes,
      };

      setResult(data);
      setStatus("success");
      return data;
    } catch (err) {
      if (axios.isCancel(err) || (err instanceof Error && err.name === "CanceledError")) {
        setStatus("idle");
        return null;
      }

      const axiosErr = err as AxiosError<{ detail?: string }>;
      const statusCode = axiosErr.response?.status;
      const detail = axiosErr.response?.data?.detail;

      // Map status codes to user-friendly error types
      const isUnsupported = statusCode === 400;

      let message: string;
      if (isUnsupported) {
        message = detail || "This video source isn't supported. We currently accept YouTube links and direct video file URLs.";
      } else if (statusCode === 422) {
        message = detail || "The URL or video content couldn't be processed. Please check the link and try again.";
      } else if (statusCode === 413) {
        message = detail || "The video is too large to process. Maximum file size is 2 GB.";
      } else if (statusCode === 502) {
        message = detail || "Couldn't reach the video source. The video may be private, removed, or unavailable.";
      } else if (statusCode === 504) {
        message = detail || "The download timed out. Please try again with a shorter video.";
      } else {
        message = detail || axiosErr.message || "Something went wrong. Please try again.";
      }

      setStatus(isUnsupported ? "unsupported" : "error");
      setError({ message, statusCode, isUnsupported });
      return null;
    } finally {
      abortRef.current = null;
    }
  }, []);

  /**
   * Cancel an in-flight request.
   */
  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
    setError(null);
  }, []);

  /**
   * Reset all state back to idle.
   */
  const reset = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
    setError(null);
    setResult(null);
  }, []);

  return { status, error, result, submit, cancel, reset };
}
