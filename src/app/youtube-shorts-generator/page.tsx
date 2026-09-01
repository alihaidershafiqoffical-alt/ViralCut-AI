import type { Metadata } from "next";
import LandingPageLayout from "@/components/app/LandingPageLayout";
import {
  YoutubeHero,
  YoutubeHowItWorks,
  YoutubeFeatures,
  YoutubeFAQ,
  YoutubeSEOContent,
} from "@/components/sections/youtube/YoutubeSections";

export const metadata: Metadata = {
  title: "YouTube Shorts Generator | Convert YouTube Video to Shorts | ViralCut",
  description:
    "Paste any YouTube video link to extract high-retention vertical clips automatically. Free AI clipping tool with automatic subtitles and 9:16 layout formatting.",
  alternates: {
    canonical: "/youtube-shorts-generator",
  },
};

export default function YoutubeLandingPage() {
  return (
    <LandingPageLayout
      Hero={<YoutubeHero />}
      HowItWorks={<YoutubeHowItWorks />}
      Features={<YoutubeFeatures />}
      FAQ={<YoutubeFAQ />}
      SEOContent={<YoutubeSEOContent />}
    />
  );
}
