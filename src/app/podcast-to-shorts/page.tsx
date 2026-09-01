import type { Metadata } from "next";
import LandingPageLayout from "@/components/app/LandingPageLayout";
import {
  PodcastHero,
  PodcastHowItWorks,
  PodcastFeatures,
  PodcastFAQ,
  PodcastSEOContent,
} from "@/components/sections/podcast/PodcastSections";

export const metadata: Metadata = {
  title: "Podcast to Shorts AI | Turn Episodes into Viral Clips | ViralCut",
  description:
    "Convert long podcast videos and audio episodes into viral vertical Shorts, Reels, and TikToks. Intelligent active speaker tracking and automated captions.",
  alternates: {
    canonical: "/podcast-to-shorts",
  },
};

export default function PodcastLandingPage() {
  return (
    <LandingPageLayout
      Hero={<PodcastHero />}
      HowItWorks={<PodcastHowItWorks />}
      Features={<PodcastFeatures />}
      FAQ={<PodcastFAQ />}
      SEOContent={<PodcastSEOContent />}
    />
  );
}
