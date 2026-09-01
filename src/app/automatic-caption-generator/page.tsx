import type { Metadata } from "next";
import LandingPageLayout from "@/components/app/LandingPageLayout";
import {
  CaptionsHero,
  CaptionsHowItWorks,
  CaptionsFeatures,
  CaptionsFAQ,
  CaptionsSEOContent,
} from "@/components/sections/captions/CaptionsSections";

export const metadata: Metadata = {
  title: "Automatic Caption Generator | Subtitles to Video Free | ViralCut",
  description:
    "Add eye-catching animated captions to your videos automatically. Fast speech-to-text transcription with custom fonts, colors, and Karaoke style animations.",
  alternates: {
    canonical: "/automatic-caption-generator",
  },
};

export default function CaptionsLandingPage() {
  return (
    <LandingPageLayout
      Hero={<CaptionsHero />}
      HowItWorks={<CaptionsHowItWorks />}
      Features={<CaptionsFeatures />}
      FAQ={<CaptionsFAQ />}
      SEOContent={<CaptionsSEOContent />}
    />
  );
}
