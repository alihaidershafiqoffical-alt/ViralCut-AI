import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Remove the X-Powered-By: Next.js response header (reduces fingerprinting)
  poweredByHeader: false,

  // Enable gzip/brotli compression at the framework level
  compress: true,

  // Image optimization
  images: {
    formats: ["image/avif", "image/webp"],
  },

  // Security & performance headers applied to every response
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },

  async redirects() {
    return [
      {
        source: "/ai-shorts-generator",
        destination: "/",
        permanent: true,
      },
      {
        source: "/ai-video-clip-generator",
        destination: "/",
        permanent: true,
      },
      {
        source: "/video-to-short-clips",
        destination: "/long-video-to-shorts",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
