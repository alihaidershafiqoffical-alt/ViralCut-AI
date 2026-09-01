import type { Metadata } from "next";
import LandingPageLayout from "@/components/app/LandingPageLayout";
import {
  LongVideoHero,
  LongVideoHowItWorks,
  LongVideoFeatures,
  LongVideoFAQ,
  LongVideoSEOContent,
} from "@/components/sections/longvideo/LongVideoSections";

export const metadata: Metadata = {
  title: "Long Video to Shorts AI | Repurpose Courses & Streams | ViralCut",
  description:
    "Turn hours of long-form courses, live streams, or webinars into multiple engaging short clips with AI. Auto crop to vertical format with animated subtitles.",
  alternates: {
    canonical: "/long-video-to-shorts",
  },
};

export default function LongVideoLandingPage() {
  return (
    <LandingPageLayout
      Hero={<LongVideoHero />}
      HowItWorks={<LongVideoHowItWorks />}
      Features={<LongVideoFeatures />}
      FAQ={<LongVideoFAQ />}
      SEOContent={<LongVideoSEOContent />}
    />
  );
}
