"use client";

import * as React from "react";
import { CheckCircle2, XCircle, AlertCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastVariant = "default" | "success" | "error" | "info";

export interface ToastProps {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  onClose: (id: string) => void;
}

const icons = {
  default: null,
  success: <CheckCircle2 className="h-5 w-5 text-emerald-500" />,
  error: <XCircle className="h-5 w-5 text-red-500" />,
  info: <AlertCircle className="h-5 w-5 text-blue-500" />,
};

export function Toast({ id, title, description, variant = "default", onClose }: ToastProps) {
  React.useEffect(() => {
    const timer = setTimeout(() => onClose(id), 5000);
    return () => clearTimeout(timer);
  }, [id, onClose]);

  return (
    <div
      className={cn(
        "pointer-events-auto flex w-full max-w-sm items-start gap-4 rounded-xl border border-gray-800 bg-[#161825] p-4 shadow-lg transition-all animate-in slide-in-from-right-full fade-in duration-300",
        variant === "error" && "border-red-900/50 bg-red-950/20"
      )}
      role="alert"
    >
      {icons[variant] && <div className="shrink-0 pt-0.5">{icons[variant]}</div>}
      <div className="flex-1 space-y-1">
        <p className="text-sm font-semibold text-white">{title}</p>
        {description && <p className="text-sm text-white/60">{description}</p>}
      </div>
      <button
        onClick={() => onClose(id)}
        className="shrink-0 rounded-md p-1 text-white/40 hover:bg-white/10 hover:text-white transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

// Simple Toast Container for demo purposes
export function ToastProvider({ children, toasts }: { children: React.ReactNode; toasts: ToastProps[] }) {
  return (
    <>
      {children}
      <div className="fixed bottom-0 right-0 z-50 m-4 flex flex-col gap-2 p-4 sm:m-6 sm:bottom-0 sm:right-0">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} />
        ))}
      </div>
    </>
  );
}
