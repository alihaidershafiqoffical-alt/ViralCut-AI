import { useState, useCallback, useRef } from "react";
import axios, { AxiosError } from "axios";
import { API_URL } from "../lib/config";

export type UploadStatus = "idle" | "uploading" | "success" | "error" | "cancelled";

interface UploadResponse {
  videoId: string;
  url?: string;
  message?: string;
}

export function useVideoUpload() {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  
  // We use AbortController for modern fetch/axios cancellation
  const abortControllerRef = useRef<AbortController | null>(null);

  const upload = useCallback(async (file: File): Promise<UploadResponse | null> => {
    // Reset state
    setProgress(0);
    setStatus("uploading");
    setError(null);

    // Create a new AbortController for this request
    abortControllerRef.current = new AbortController();
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post<UploadResponse>(
        `${API_URL}/api/v1/videos/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          signal: abortControllerRef.current.signal,
          onUploadProgress: (progressEvent) => {
            const percentCompleted = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setProgress(percentCompleted);
          },
        }
      );

      setStatus("success");
      return response.data;
    } catch (err) {
      if (axios.isCancel(err) || (err instanceof Error && err.name === "CanceledError")) {
        setStatus("cancelled");
        setError("Upload was cancelled.");
      } else {
        setStatus("error");
        const axiosError = err as AxiosError<{ detail?: string | { error?: string } | Array<{ msg?: string }> }>;
        const respData = axiosError.response?.data;
        let msg = "An unexpected error occurred during upload.";
        
        if (respData?.detail) {
          if (typeof respData.detail === "string") {
            msg = respData.detail;
          } else if (Array.isArray(respData.detail)) {
            msg = respData.detail.map((d) => d.msg).filter(Boolean).join(", ");
          } else if (typeof respData.detail === "object" && respData.detail.error) {
            msg = respData.detail.error;
          }
        } else if (axiosError.message) {
          msg = axiosError.message;
        }
        
        setError(msg);
      }
      return null;
    } finally {
      abortControllerRef.current = null;
    }
  }, []);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setStatus("cancelled");
    }
  }, []);

  return {
    upload,
    cancel,
    progress,
    status,
    error,
  };
}
