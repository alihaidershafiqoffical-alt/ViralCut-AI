// =============================================================================
// app/page.tsx — Main entry point for the ViralCut single-page flow.
// Orchestrates state transitions: Input -> Settings -> Processing -> Results.
// =============================================================================
"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { API_URL } from "@/lib/config";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import Hero from "@/components/sections/Hero";
import VideoInput from "@/components/sections/VideoInput";
import ShortsSettings from "@/components/sections/ShortsSettings";
import ProcessingState, { STAGES } from "@/components/sections/ProcessingState";
import Results from "@/components/sections/Results";
import HowItWorks from "@/components/sections/HowItWorks";
import Features from "@/components/sections/Features";
import FAQ from "@/components/sections/FAQ";
import SEOContent from "@/components/sections/SEOContent";
import AdSenseBanner from "@/components/ui/AdSenseBanner";

import type {
  AppStage,
  VideoSource,
  ShortsConfig,
  GeneratedClip,
} from "@/types/index";

export default function Home() {
  const [stage, setStage] = useState<AppStage>("input");
  const [source, setSource] = useState<VideoSource | null>(null);
  const [clips, setClips] = useState<GeneratedClip[]>([]);

  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [currentAccessToken, setCurrentAccessToken] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentStageId, setCurrentStageId] = useState(1);
  const [customMessage, setCustomMessage] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [targetCount, setTargetCount] = useState<number>(3);
  const [jobStatus, setJobStatus] = useState<string>("queued");
  const [activeTasksCount, setActiveTasksCount] = useState<number>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = sessionStorage.getItem("viralcut_dashboard_tasks");
        if (stored) {
          const list = JSON.parse(stored);
          return list.filter((t: { status?: string }) => t.status === "pending" || t.status === "processing").length;
        }
      } catch (e) {
        console.error("Failed to count active tasks:", e);
      }
    }
    return 0;
  });

  // Monitor count of active tasks for dashboard/concurrency checks
  useEffect(() => {
    if (typeof window === "undefined") return;
    const updateActiveCount = () => {
      try {
        const stored = sessionStorage.getItem("viralcut_dashboard_tasks");
        if (stored) {
          const list = JSON.parse(stored);
          const active = list.filter((t: { status?: string }) => t.status === "pending" || t.status === "processing");
          setActiveTasksCount(active.length);
        } else {
          setActiveTasksCount(0);
        }
      } catch (e) {
        console.error("Failed to count active tasks:", e);
      }
    };
    const interval = setInterval(updateActiveCount, 3000);
    return () => clearInterval(interval);
  }, []);

  // Poll status when jobId & accessToken are set
  useEffect(() => {
    if (!currentJobId || !currentAccessToken) return;

    let timerId: ReturnType<typeof setTimeout> | null = null;
    let isAborted = false;

    const pollStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/jobs/status/${currentJobId}`, {
          headers: {
            "Authorization": `Bearer ${currentAccessToken}`
          }
        });

        if (isAborted) return;

        const data = response.data;
        setProgress(data.progress);
        setCustomMessage(data.statusMessage);
        setJobStatus(data.status || "queued");
        if (data.targetCount) {
          setTargetCount(data.targetCount);
        }

        const stageName = data.currentStage;
        const match = STAGES.find(s => s.name === stageName);
        if (match) {
          setCurrentStageId(match.id);
        }

        // Progressive Results transition: if we have generated clips, show them immediately!
        if (data.clips && data.clips.length > 0) {
          const formattedClips = data.clips.map((clip: { id?: string; title?: string; duration?: number; previewUrl?: string; downloadUrl?: string; viralScore?: number; start?: number; end?: number }, index: number) => ({
            id: clip.id || `clip-${index + 1}`,
            index: index + 1,
            title: clip.title || `Short #${index + 1}`,
            duration: clip.duration || 30,
            captionStyle: "Karaoke",
            previewUrl: `${API_URL}${clip.previewUrl}`,
            downloadUrl: `${API_URL}${clip.downloadUrl}`,
            thumbnailUrl: "",
            viralScore: clip.viralScore || 0.90,
            startTime: clip.start || 0,
            endTime: clip.end || clip.duration || 30,
          }));

          setClips(formattedClips);
          setStage("results");
        }

        if (data.status === "completed") {
          // Finished polling on completion
        } else if (data.status === "failed") {
          setErrorMsg(data.errorState || "Job failed during background processing.");
        } else if (data.status === "expired") {
          setErrorMsg("Access to this job has expired.");
        } else {
          timerId = setTimeout(pollStatus, 3000);
        }
      } catch (err: unknown) {
        if (isAborted) return;
        const axiosErr = err as { response?: { data?: { detail?: string | { error?: string } } }; message?: string };
        const detail = axiosErr.response?.data?.detail;
        const msg = (typeof detail === "object" ? detail?.error : detail) || axiosErr.message || "Failed to poll job status.";
        setErrorMsg(msg);
      }
    };

    pollStatus();

    return () => {
      isAborted = true;
      if (timerId) clearTimeout(timerId);
    };
  }, [currentJobId, currentAccessToken, stage]);

  // Cancel active job on tab close or navigation away
  useEffect(() => {
    if (stage !== "processing" || !currentJobId || !currentAccessToken) return;

    const handleUnload = () => {
      const cancelUrl = `${API_URL}/api/v1/jobs/${currentJobId}/cancel`;
      fetch(cancelUrl, {
        method: "POST",
        keepalive: true,
        headers: {
          "Authorization": `Bearer ${currentAccessToken}`,
          "Content-Type": "application/json"
        }
      });
    };

    window.addEventListener("beforeunload", handleUnload);
    window.addEventListener("unload", handleUnload);

    return () => {
      window.removeEventListener("beforeunload", handleUnload);
      window.removeEventListener("unload", handleUnload);
    };
  }, [stage, currentJobId, currentAccessToken]);

  // ---------------------------------------------------------------------------
  // Flow Handlers
  // ---------------------------------------------------------------------------
  const handleSourceSelected = (newSource: VideoSource) => {
    setSource(newSource);
    setStage("settings");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleGenerate = async (newConfig: ShortsConfig) => {
    setStage("processing");
    setProgress(5);
    setCurrentStageId(1);
    setCustomMessage("Queuing video processing task...");
    setErrorMsg(null);
    window.scrollTo({ top: 0, behavior: "smooth" });

    try {
      const response = await axios.post(`${API_URL}/api/v1/jobs/process`, {
        videoSource: source?.videoId || "",
        isUrl: source?.type === "url",
        targetCount: newConfig.count === "custom" ? newConfig.customCount : newConfig.count,
        clipDuration: newConfig.duration,
        aspectRatio: newConfig.aspectRatio,
        topic: newConfig.topic || undefined,
        startTime: newConfig.startTime !== undefined ? newConfig.startTime : undefined,
        endTime: newConfig.endTime !== undefined ? newConfig.endTime : undefined,
      }, {
        headers: { "Content-Type": "application/json" }
      });

      const { jobId, accessToken } = response.data;
      setCurrentJobId(jobId);
      setCurrentAccessToken(accessToken);

      // Save to sessionStorage for dashboard integration
      if (typeof window !== "undefined") {
        try {
          const stored = sessionStorage.getItem("viralcut_dashboard_tasks");
          const list = stored ? JSON.parse(stored) : [];
          const newTask = {
            id: jobId,
            accessToken: accessToken,
            status: "pending",
            progress: 5,
            videoTitle: source?.displayName || "Video from Homepage",
            createdAt: new Date().toISOString(),
          };
          // Insert at the beginning of list
          list.unshift(newTask);
          sessionStorage.setItem("viralcut_dashboard_tasks", JSON.stringify(list));
        } catch (e) {
          console.error("Failed to sync enqueued job to dashboard storage:", e);
        }
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string | { error?: string } } }; message?: string };
      const detail = axiosErr.response?.data?.detail;
      const msg = (typeof detail === "object" ? detail?.error : detail) || axiosErr.message || "Failed to start video processing.";
      setErrorMsg(msg);
      setProgress(100);
      setCustomMessage(msg);
    }
  };

  const handleStartOver = () => {
    setStage("input");
    setSource(null);
    setClips([]);
    setCurrentJobId(null);
    setCurrentAccessToken(null);
    setProgress(0);
    setErrorMsg(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <>
      <Header />
      
      <main className="flex-1 flex flex-col min-h-screen">
        {/* Render the Hero only if we are in the initial input stage */}
        {stage === "input" && <Hero />}

        {/* Adjust top padding when Hero is hidden */}
        <div className={`w-full ${stage !== "input" ? "pt-32 pb-16 flex-1 flex flex-col justify-center" : "pb-24"}`}>
          
          {stage === "input" && (
            <VideoInput onSourceSelected={handleSourceSelected} disabled={activeTasksCount >= 2} />
          )}

          {stage === "settings" && source && (
            <ShortsSettings
              source={source}
              onBack={() => setStage("input")}
              onGenerate={handleGenerate}
            />
          )}

          {stage === "processing" && (
            <ProcessingState
              currentStageId={currentStageId}
              progress={progress}
              customMessage={errorMsg || customMessage}
              isError={!!errorMsg}
              onStartOver={handleStartOver}
            />
          )}

          {stage === "results" && (
            <Results
              clips={clips}
              jobId={currentJobId}
              accessToken={currentAccessToken}
              onStartOver={handleStartOver}
              targetCount={targetCount}
              jobStatus={jobStatus}
            />
          )}
          
        </div>
      </main>
      
      {/* Informational / Marketing Sections (Only show on initial input stage for cleaner UX, or show always based on preference. I'll show always for SEO purposes, but separated.) */}
      {stage === "input" && (
        <>
          <HowItWorks />
          <Features />
          <AdSenseBanner slot="1234567890" />
          <FAQ />
          <SEOContent />
        </>
      )}

      <Footer />
    </>
  );
}
