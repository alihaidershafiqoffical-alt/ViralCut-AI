"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { API_URL } from "@/lib/config";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import VideoInput from "@/components/sections/VideoInput";
import ShortsSettings from "@/components/sections/ShortsSettings";
import ProcessingState, { STAGES } from "@/components/sections/ProcessingState";
import Results from "@/components/sections/Results";
import AdSenseBanner from "@/components/ui/AdSenseBanner";

import type {
  AppStage,
  VideoSource,
  ShortsConfig,
  GeneratedClip,
} from "@/types/index";

interface LandingPageLayoutProps {
  Hero: React.ReactNode;
  HowItWorks: React.ReactNode;
  Features: React.ReactNode;
  FAQ: React.ReactNode;
  SEOContent: React.ReactNode;
}

export default function LandingPageLayout({
  Hero: heroSection,
  HowItWorks,
  Features,
  FAQ,
  SEOContent,
}: LandingPageLayoutProps) {
  const [stage, setStage] = useState<AppStage>("input");
  const [source, setSource] = useState<VideoSource | null>(null);
  const [clips, setClips] = useState<GeneratedClip[]>([]);

  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [currentAccessToken, setCurrentAccessToken] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentStageId, setCurrentStageId] = useState(1);
  const [customMessage, setCustomMessage] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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

        const stageName = data.currentStage;
        const match = STAGES.find(s => s.name === stageName);
        if (match) {
          setCurrentStageId(match.id);
        }

        if (data.status === "completed") {
          const formattedClips = data.clips.map((clip: { id?: string; title?: string; duration?: number; previewUrl?: string; downloadUrl?: string; viralScore?: number }, index: number) => ({
            id: clip.id || `clip-${index + 1}`,
            index: index + 1,
            title: clip.title || `Short #${index + 1}`,
            duration: clip.duration || 30,
            captionStyle: "Karaoke",
            previewUrl: `${API_URL}${clip.previewUrl}`,
            downloadUrl: `${API_URL}${clip.downloadUrl}`,
            thumbnailUrl: "",
            viralScore: clip.viralScore || 0.90,
            startTime: 0,
            endTime: clip.duration || 30,
          }));

          setClips(formattedClips);
          setStage("results");
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
  }, [currentJobId, currentAccessToken]);

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
      }, {
        headers: { "Content-Type": "application/json" }
      });

      const { jobId, accessToken } = response.data;
      setCurrentJobId(jobId);
      setCurrentAccessToken(accessToken);
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
        {/* Hero Section */}
        {heroSection}

        {/* Dynamic App Stage Container */}
        <div className="w-full pb-24">
          
          {stage === "input" && (
            <VideoInput onSourceSelected={handleSourceSelected} />
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
            />
          )}

          {stage === "results" && (
            <Results
              clips={clips}
              jobId={currentJobId}
              accessToken={currentAccessToken}
              onStartOver={handleStartOver}
            />
          )}
          
        </div>
      </main>
      
      {stage === "input" && (
        <>
          {HowItWorks}
          {Features}
          <AdSenseBanner slot="1234567890" />
          {FAQ}
          {SEOContent}
        </>
      )}

      <Footer />
    </>
  );
}
