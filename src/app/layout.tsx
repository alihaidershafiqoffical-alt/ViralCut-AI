// =============================================================================
// app/layout.tsx — Root layout with comprehensive Technical SEO, JSON-LD, fonts
// =============================================================================

import type { Metadata, Viewport } from "next";
import { Inter, Poppins } from "next/font/google";
import "./globals.css";

// ---------------------------------------------------------------------------
// Fonts — Inter for body text, Poppins for headings with optimal display
// ---------------------------------------------------------------------------
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

const poppins = Poppins({
  variable: "--font-heading",
  subsets: ["latin"],
  display: "swap",
  weight: ["600", "700", "800"],
});

const SITE_URL = process.env.NEXT_PUBLIC_APP_URL || "https://viralcut.ai";

// ---------------------------------------------------------------------------
// Technical SEO Metadata
// ---------------------------------------------------------------------------
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "ViralCut — AI Shorts Generator | Free AI Video Clip Generator",
    template: "%s | ViralCut AI",
  },
  description:
    "Transform long video to Shorts with our free AI Shorts Generator. Create YouTube Shorts, TikToks, and Reels with automatic captions and smart AI video clipping.",
  keywords: [
    "AI Shorts Generator",
    "AI video clip generator",
    "Long video to Shorts",
    "YouTube Shorts generator",
    "Automatic captions",
    "AI video clipping",
    "TikTok clip maker",
    "Instagram Reels creator",
    "ViralCut",
  ],
  authors: [{ name: "ViralCut AI Team", url: SITE_URL }],
  creator: "ViralCut AI",
  publisher: "ViralCut AI",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE_URL,
    siteName: "ViralCut AI",
    title: "ViralCut — AI Shorts Generator & AI Video Clip Generator",
    description:
      "Transform long video to Shorts with our free AI Shorts Generator. Create YouTube Shorts, TikToks, and Reels with automatic captions and smart AI video clipping.",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "ViralCut — AI Video to Shorts Generator",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "ViralCut — AI Shorts Generator & AI Video Clip Generator",
    description:
      "Transform long video to Shorts with our free AI Shorts Generator. Create YouTube Shorts, TikToks, and Reels with automatic captions and smart AI video clipping.",
    images: ["/opengraph-image"],
    creator: "@viralcutai",
    site: "@viralcutai",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#0d0e1a",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

// ---------------------------------------------------------------------------
// Structured Data / JSON-LD Schema
// ---------------------------------------------------------------------------
const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebApplication",
      "@id": `${SITE_URL}/#webapp`,
      name: "ViralCut AI",
      url: SITE_URL,
      applicationCategory: "MultimediaApplication",
      operatingSystem: "All",
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
      },
      description:
        "Free AI Shorts Generator and AI video clip generator that converts long video to Shorts automatically with automatic captions and smart AI video clipping.",
      featureList: [
        "AI Shorts Generator",
        "AI Video Clipping & Speaker Tracking",
        "Automatic Captions & Subtitles",
        "Long Video to Shorts Conversion",
        "YouTube Shorts Generator Output",
        "No Watermark Export",
      ],
    },
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: SITE_URL,
      name: "ViralCut AI",
      description: "Free AI Shorts Generator from Long Videos",
      publisher: {
        "@type": "Organization",
        name: "ViralCut AI",
        url: SITE_URL,
      },
    },
    {
      "@type": "FAQPage",
      "@id": `${SITE_URL}/#faq`,
      mainEntity: [
        {
          "@type": "Question",
          name: "What is an AI Shorts Generator and how does it work?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "An AI Shorts Generator is an online tool that uses artificial intelligence to convert long video to Shorts. It analyzes the transcript and audio cues of a long video to find the most engaging segments, crops the video to a vertical 9:16 layout, and burns automatic captions directly onto the video. With ViralCut, you simply paste a link or upload a file, and our AI video clipping engine does the rest.",
          },
        },
        {
          "@type": "Question",
          name: "Can I use ViralCut as a YouTube Shorts generator?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Yes! ViralCut is specifically designed as a YouTube Shorts generator, TikTok clip maker, and Instagram Reels creator. The clips are generated in 1080x1920 portrait aspect ratio, complete with engaging automatic captions, making them perfectly formatted and ready to upload to any vertical video platform.",
          },
        },
        {
          "@type": "Question",
          name: "How does the AI handle video clipping and framing?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Our advanced AI video clipping system uses intelligent facial and speaker tracking to identify where the active speaker is in the original horizontal frame. It then dynamically adjusts the vertical crop window so that the subject remains centered, preventing important details from being cut off.",
          },
        },
        {
          "@type": "Question",
          name: "Is there a limit on long video to Shorts conversion?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "We support long-form video uploads up to 2GB in size, as well as direct YouTube links of any length. Our AI video clip generator will scan the entire length of the video to locate the absolute best retention hooks and create multiple high-quality Shorts from it.",
          },
        },
        {
          "@type": "Question",
          name: "Are the automatic captions customizable?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Yes! Our automatic captions are transcribed using Faster-Whisper for near-perfect accuracy. Once the clips are ready, you can customize the caption text, correct spelling, adjust timing, and choose from multiple animated styles like 'Karaoke Glow' or 'Hormozi Pop' to match your personal brand.",
          },
        },
      ],
    },
    {
      "@type": "HowTo",
      "@id": `${SITE_URL}/#howto`,
      name: "How to Convert Long Video to Shorts with ViralCut AI",
      description:
        "Convert long videos into viral, short-form clips in 4 simple steps.",
      step: [
        {
          "@type": "HowToStep",
          position: 1,
          name: "Upload Video",
          text: "Drag & drop your video file or paste a YouTube link. We accept MP4, MOV, WebM, and direct URLs.",
        },
        {
          "@type": "HowToStep",
          position: 2,
          name: "Configure AI Settings",
          text: "Choose the target duration and how many vertical clips you want to generate.",
        },
        {
          "@type": "HowToStep",
          position: 3,
          name: "AI Video Clipping & Auto Captioning",
          text: "The AI video clip generator scans the transcript for hooks, crops the video to vertical format, and adds automatic captions.",
        },
        {
          "@type": "HowToStep",
          position: 4,
          name: "Preview & Download",
          text: "Review the generated YouTube Shorts. Edit the captions, adjust styling, and download the finished HD clips.",
        },
      ],
    },
  ],
};

// ---------------------------------------------------------------------------
// Root Layout
// ---------------------------------------------------------------------------
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`dark ${inter.variable} ${poppins.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body
        suppressHydrationWarning
        className="min-h-screen antialiased bg-[#0a0b12] text-white"
      >
        {children}
      </body>
    </html>
  );
}

