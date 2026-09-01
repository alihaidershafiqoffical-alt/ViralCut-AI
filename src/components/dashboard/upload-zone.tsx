"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, FileVideo, X, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { formatFileSize } from "@/lib/formatters";

import axios from "axios";
import { API_URL } from "@/lib/config";

interface UploadZoneProps {
  onUpload?: (file: File, videoId: string) => void;
  disabled?: boolean;
}

const ACCEPTED_TYPES = [
  "video/mp4",
  "video/webm",
  "video/quicktime",
  "video/x-msvideo",
  "video/x-matroska",
];
const MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024; // 2GB

export function UploadZone({ onUpload, disabled = false }: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    const validExts = ["mp4", "mov", "webm", "mkv", "avi"];
    const isMimeValid = ACCEPTED_TYPES.includes(file.type);
    const isExtValid = ext ? validExts.includes(ext) : false;

    if (!isMimeValid && !isExtValid) {
      return "Unsupported format. Please upload MP4, WebM, MOV, AVI, or MKV.";
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}.`;
    }
    return null;
  };

  const handleFile = useCallback((file: File) => {
    setError(null);
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSelectedFile(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(
        `${API_URL}/api/v1/videos/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setUploadProgress(percentCompleted);
          },
        }
      );

      const { videoId } = response.data;
      onUpload?.(selectedFile, videoId);
      setSelectedFile(null);
    } catch (err: unknown) {
      console.error("Upload error:", err);
      const axiosError = err as { response?: { data?: { detail?: string | object } }; message?: string };
      const respData = axiosError.response?.data;
      let msg = "Failed to upload video.";
      if (respData?.detail) {
        msg = typeof respData.detail === "string" ? respData.detail : JSON.stringify(respData.detail);
      } else if (axiosError.message) {
        msg = axiosError.message;
      }
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="space-y-4">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !disabled && !selectedFile && inputRef.current?.click()}
        className={`relative rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer ${
          isDragOver
            ? "border-viral-purple bg-viral-purple/10 scale-[1.01]"
            : selectedFile
              ? "border-viral-purple/30 bg-viral-purple/5"
              : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
        } ${disabled ? "opacity-40 pointer-events-none" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled}
        />

        {selectedFile ? (
          /* File preview */
          <div className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-viral-purple/15 shrink-0">
              <FileVideo className="h-6 w-6 text-viral-purple" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleUpload();
                }}
                disabled={isUploading}
                className="bg-gradient-to-r from-viral-purple to-viral-pink hover:opacity-90 text-white border-0 cursor-pointer"
              >
                {isUploading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Uploading ({uploadProgress}%)…
                  </span>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Process
                  </>
                )}
              </Button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  clearFile();
                }}
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        ) : (
          /* Drop zone */
          <div className="flex flex-col items-center justify-center py-12 px-6">
            <div
              className={`flex h-14 w-14 items-center justify-center rounded-2xl mb-4 transition-colors ${
                isDragOver ? "bg-viral-purple/20" : "bg-white/5"
              }`}
            >
              <Upload
                className={`h-6 w-6 transition-colors ${
                  isDragOver ? "text-viral-purple" : "text-muted-foreground"
                }`}
              />
            </div>
            <p className="text-sm font-medium mb-1">
              {isDragOver ? "Drop your video here" : "Drag & drop a video file"}
            </p>
            <p className="text-xs text-muted-foreground">
              or click to browse · MP4, WebM, MOV, AVI, MKV up to 2GB
            </p>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-400 animate-slide-down">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
