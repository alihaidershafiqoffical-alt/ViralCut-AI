"use client";

import { useState, useEffect } from "react";
import { UploadZone } from "@/components/dashboard/upload-zone";
import { TaskList } from "@/components/dashboard/task-list";
import { Separator } from "@/components/ui/Separator";
import dynamic from "next/dynamic";
import type { Task } from "@/types/task";
import axios from "axios";
import { API_URL } from "@/lib/config";

const SESSION_STORAGE_KEY = "viralcut_dashboard_tasks";

// Lazy-loaded to keep the initial bundle smaller
const UrlIngestZone = dynamic(
  () =>
    import("@/components/dashboard/url-ingest-zone").then(
      (m) => m.UrlIngestZone
    ),
  {
    ssr: false,
    loading: () => (
      <div className="h-36 rounded-2xl border-2 border-dashed border-white/10 animate-pulse" />
    ),
  }
);

export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = sessionStorage.getItem(SESSION_STORAGE_KEY);
        if (stored) {
          return JSON.parse(stored);
        }
      } catch (e) {
        console.error("Failed to parse stored tasks:", e);
      }
    }
    return [];
  });
  const [inputTab, setInputTab] = useState<"upload" | "url">("upload");

  // Helper to save tasks state and persist to SessionStorage
  const saveTasksList = (updated: Task[]) => {
    setTasks(updated);
    if (typeof window !== "undefined") {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(updated));
    }
  };

  // Poll status of active (pending/processing) tasks from backend
  useEffect(() => {
    const active = tasks.filter((t) => t.status === "processing" || t.status === "pending");
    if (active.length === 0) return;

    let isAborted = false;
    const interval = setInterval(async () => {
      const updatedTasks = [...tasks];
      let hasChanges = false;

      for (let i = 0; i < updatedTasks.length; i++) {
        const task = updatedTasks[i];
        if (task.status === "processing" || task.status === "pending") {
          try {
            // Retrieve accessToken stored on the task object locally
            const token = (task as Task & { accessToken?: string }).accessToken;
            const res = await axios.get(`${API_URL}/api/v1/jobs/status/${task.id}`, {
              headers: token ? { Authorization: `Bearer ${token}` } : {},
            });

            if (isAborted) return;

            const data = res.data;
            let newStatus: Task["status"] = "processing";
            if (data.status === "completed") newStatus = "completed";
            else if (data.status === "failed") newStatus = "failed";
            else if (data.status === "expired") newStatus = "failed";
            else if (data.status === "queued") newStatus = "pending";

            if (
              task.progress !== data.progress ||
              task.status !== newStatus ||
              (data.status === "failed" && task.error !== data.errorState)
            ) {
              hasChanges = true;
              updatedTasks[i] = {
                ...task,
                status: newStatus,
                progress: data.progress,
                error: data.errorState || undefined,
                outputUrls: data.status === "completed" && Array.isArray(data.clips)
                  ? data.clips.map((c: { previewUrl?: string }) => `${API_URL}${c.previewUrl}`) 
                  : undefined,
                completedAt: data.status === "completed" ? new Date().toISOString() : undefined,
              };
            }
          } catch (err) {
            console.error(`Failed to poll status for job ${task.id}:`, err);
          }
        }
      }

      if (hasChanges && !isAborted) {
        saveTasksList(updatedTasks);
      }
    }, 3000);

    return () => {
      isAborted = true;
      clearInterval(interval);
    };
  }, [tasks]);

  // Cancel active jobs when tab is closed/refreshed
  useEffect(() => {
    const handleUnload = () => {
      const activeList = tasks.filter((t) => (t.status === "processing" || t.status === "pending") && t.accessToken);
      for (const t of activeList) {
        const cancelUrl = `${API_URL}/api/v1/jobs/${t.id}/cancel`;
        fetch(cancelUrl, {
          method: "POST",
          keepalive: true,
          headers: {
            "Authorization": `Bearer ${t.accessToken}`,
            "Content-Type": "application/json"
          }
        });
      }
    };

    window.addEventListener("beforeunload", handleUnload);
    window.addEventListener("unload", handleUnload);

    return () => {
      window.removeEventListener("beforeunload", handleUnload);
      window.removeEventListener("unload", handleUnload);
    };
  }, [tasks]);

  const activeTasks = tasks.filter(
    (t) => t.status === "processing" || t.status === "pending"
  );
  const completedTasks = tasks.filter((t) => t.status === "completed");
  const failedTasks = tasks.filter((t) => t.status === "failed");
  const isLimitReached = activeTasks.length >= 2;

  // Handle uploaded video: triggers backend processing
  const handleUpload = async (file: File, videoId: string) => {
    const placeholderId = `upload-${Date.now()}`;
    const initialTask: Task = {
      id: placeholderId,
      status: "pending",
      progress: 5,
      videoTitle: file.name,
      createdAt: new Date().toISOString(),
    };
    const currentList = [initialTask, ...tasks];
    saveTasksList(currentList);

    try {
      const response = await axios.post(`${API_URL}/api/v1/jobs/process`, {
        videoSource: videoId,
        isUrl: false,
        targetCount: 3,
        clipDuration: 30.0,
        aspectRatio: "9:16",
      }, {
        headers: { "Content-Type": "application/json" }
      });

      const { jobId, accessToken } = response.data;

      const updated = currentList.map((t) => {
        if (t.id === placeholderId) {
          return {
            ...t,
            id: jobId,
            accessToken: accessToken,
            status: "pending" as const,
            progress: 10,
          };
        }
        return t;
      });
      saveTasksList(updated);
    } catch (err: unknown) {
      console.error("Failed to queue process job for upload:", err);
      const axiosErr = err as { response?: { data?: { detail?: string | { error?: string } } }; message?: string };
      const detail = axiosErr.response?.data?.detail;
      const msg = (typeof detail === "object" ? detail?.error : detail) || axiosErr.message || "Failed to queue job.";
      const updated = currentList.map((t) => {
        if (t.id === placeholderId) {
          return {
            ...t,
            status: "failed" as const,
            error: msg,
          };
        }
        return t;
      });
      saveTasksList(updated);
    }
  };

  // Handle URL ingest job: triggers backend processing
  const handleUrlJob = async (jobId: string) => {
    const placeholderId = `url-${Date.now()}`;
    const initialTask: Task = {
      id: placeholderId,
      status: "pending",
      progress: 5,
      videoTitle: "Ingested video link",
      createdAt: new Date().toISOString(),
    };
    const currentList = [initialTask, ...tasks];
    saveTasksList(currentList);

    try {
      const response = await axios.post(`${API_URL}/api/v1/jobs/process`, {
        videoSource: jobId,
        isUrl: false,
        targetCount: 3,
        clipDuration: 30.0,
        aspectRatio: "9:16",
      }, {
        headers: { "Content-Type": "application/json" }
      });

      const { jobId: realJobId, accessToken } = response.data;

      const updated = currentList.map((t) => {
        if (t.id === placeholderId) {
          return {
            ...t,
            id: realJobId,
            accessToken: accessToken,
            status: "pending" as const,
            progress: 10,
          };
        }
        return t;
      });
      saveTasksList(updated);
    } catch (err: unknown) {
      console.error("Failed to queue process job for URL:", err);
      const axiosErr = err as { response?: { data?: { detail?: string | { error?: string } } }; message?: string };
      const detail = axiosErr.response?.data?.detail;
      const msg = (typeof detail === "object" ? detail?.error : detail) || axiosErr.message || "Failed to queue job.";
      const updated = currentList.map((t) => {
        if (t.id === placeholderId) {
          return {
            ...t,
            status: "failed" as const,
            error: msg,
          };
        }
        return t;
      });
      saveTasksList(updated);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto space-y-8">
      {/* ── Input Section ─────────────────────────────────────────────── */}
      <section id="upload">
        {/* Header + source-type tabs */}
        <div className="mb-5 flex items-end justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-xl font-semibold">Add Video</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Upload a file or paste a supported video link
            </p>
          </div>

          <div className="flex items-center gap-1 rounded-xl border border-white/8 bg-white/[0.03] p-1">
            <button
              id="tab-upload"
              onClick={() => setInputTab("upload")}
              className={`pill text-xs px-4 py-1.5 ${inputTab === "upload" ? "pill-active" : ""}`}
            >
              Upload file
            </button>
            <button
              id="tab-url"
              onClick={() => setInputTab("url")}
              className={`pill text-xs px-4 py-1.5 ${inputTab === "url" ? "pill-active" : ""}`}
            >
              From URL
            </button>
          </div>
        </div>

        {/* Active limit warning banner */}
        {isLimitReached && (
          <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-amber-500/20 bg-amber-500/[0.06] p-4 text-sm text-amber-300">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-amber-300">Active processing limit reached</p>
              <p className="text-xs text-white/50 mt-0.5">
                You currently have 2 active video processing tasks running. Please wait for one of your tasks to complete before adding another video.
              </p>
            </div>
          </div>
        )}

        {/* Active panel */}
        {inputTab === "upload" ? (
          <UploadZone onUpload={handleUpload} disabled={isLimitReached} />
        ) : (
          <UrlIngestZone onJobCreated={handleUrlJob} disabled={isLimitReached} />
        )}
      </section>

      <Separator className="bg-white/5" />

      {/* ── Active Tasks ──────────────────────────────────────────────── */}
      <section>
        <TaskList
          title="Active Tasks"
          tasks={activeTasks}
          emptyMessage="No active tasks. Upload a video to get started!"
        />
      </section>

      {/* ── Completed Tasks ───────────────────────────────────────────── */}
      {completedTasks.length > 0 && (
        <>
          <Separator className="bg-white/5" />
          <section id="history">
            <TaskList title="Completed" tasks={completedTasks} />
          </section>
        </>
      )}

      {/* ── Failed Tasks ──────────────────────────────────────────────── */}
      {failedTasks.length > 0 && (
        <>
          <Separator className="bg-white/5" />
          <section>
            <TaskList title="Failed" tasks={failedTasks} />
          </section>
        </>
      )}
    </div>
  );
}
