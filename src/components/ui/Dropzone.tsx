"use client";

import * as React from "react";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

interface DropzoneProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "onDrop"> {
  onDropFile: (file: File) => void;
  isUploading?: boolean;
  accept?: string;
  maxSizeMB?: number;
}

export function Dropzone({
  className,
  onDropFile,
  isUploading = false,
  accept = "video/*",
  maxSizeMB = 2000,
  ...props
}: DropzoneProps) {
  const [isDragActive, setIsDragActive] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleDragOver = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDrop = React.useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        onDropFile(e.dataTransfer.files[0]);
      }
    },
    [onDropFile]
  );

  const handleChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files.length > 0) {
        onDropFile(e.target.files[0]);
      }
    },
    [onDropFile]
  );

  return (
    <div
      role="presentation"
      onClick={() => !isUploading && inputRef.current?.click()}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "group relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed transition-colors",
        "py-12 px-6 text-center",
        isDragActive
          ? "border-violet-500 bg-violet-500/[0.04]"
          : "border-gray-700 bg-white/[0.02] hover:border-violet-500/50 hover:bg-white/[0.04]",
        isUploading && "pointer-events-none opacity-60",
        className
      )}
      {...props}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={accept}
        onChange={handleChange}
        disabled={isUploading}
      />
      <div className={cn("rounded-full bg-white/[0.05] p-4 mb-4 transition-transform", isDragActive && "scale-110")}>
        <UploadCloud className={cn("h-8 w-8", isDragActive ? "text-violet-400" : "text-white/60")} />
      </div>
      <p className="mb-2 text-base font-medium text-white/90">
        {isDragActive ? "Drop video here" : "Drag and drop your video"}
      </p>
      <p className="text-sm text-white/40">
        or <span className="text-violet-400 font-medium">browse files</span>
      </p>
      <p className="mt-4 text-xs text-white/30">
        Max file size: {maxSizeMB}MB
      </p>
    </div>
  );
}
