// =============================================================================
// app/opengraph-image.tsx — Dynamic OG image via Next.js ImageResponse API.
// Replaces the missing static og-image.png with a programmatic solution.
// Next.js auto-serves this at /opengraph-image and /twitter-image routes.
// =============================================================================

import { ImageResponse } from "next/og";

export const alt = "ViralCut — AI Video to Shorts Generator";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OGImage() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "linear-gradient(135deg, #0a0b12 0%, #1a1c2e 50%, #0d0e1a 100%)",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, sans-serif",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Background decorative circles */}
        <div
          style={{
            position: "absolute",
            top: "-80px",
            left: "-100px",
            width: "400px",
            height: "400px",
            borderRadius: "50%",
            background: "rgba(124, 58, 237, 0.15)",
            filter: "blur(80px)",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "-60px",
            right: "-80px",
            width: "350px",
            height: "350px",
            borderRadius: "50%",
            background: "rgba(236, 72, 153, 0.12)",
            filter: "blur(80px)",
          }}
        />

        {/* Brand badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            marginBottom: "32px",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "12px",
              background: "linear-gradient(135deg, #7c3aed, #4f46e5)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span style={{ fontSize: "24px", color: "white" }}>⚡</span>
          </div>
          <span
            style={{
              fontSize: "28px",
              fontWeight: 800,
              color: "white",
              letterSpacing: "-0.5px",
            }}
          >
            ViralCut AI
          </span>
        </div>

        {/* Headline */}
        <div
          style={{
            fontSize: "56px",
            fontWeight: 800,
            color: "white",
            textAlign: "center",
            lineHeight: 1.1,
            maxWidth: "900px",
            letterSpacing: "-1.5px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <span>Turn Long Videos Into</span>
          <span
            style={{
              background: "linear-gradient(135deg, #a78bfa, #ec4899, #60a5fa)",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            Viral Shorts
          </span>
        </div>

        {/* Subheadline */}
        <p
          style={{
            fontSize: "22px",
            color: "rgba(255,255,255,0.55)",
            textAlign: "center",
            maxWidth: "700px",
            marginTop: "24px",
            lineHeight: 1.5,
          }}
        >
          AI-powered clipping • Animated captions • 9:16 crop • Zero watermark
        </p>

        {/* CTA badge */}
        <div
          style={{
            marginTop: "36px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "12px 28px",
            borderRadius: "999px",
            background: "linear-gradient(135deg, #7c3aed, #4f46e5)",
            fontSize: "18px",
            fontWeight: 700,
            color: "white",
          }}
        >
          Try Free — No Account Required
        </div>
      </div>
    ),
    {
      ...size,
    }
  );
}
