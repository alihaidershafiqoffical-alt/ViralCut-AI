import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://viralcut.ai";

  return [
    {
      url: baseUrl,
      lastModified: "2026-08-26",
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${baseUrl}/podcast-to-shorts`,
      lastModified: "2026-08-26",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/youtube-shorts-generator`,
      lastModified: "2026-08-26",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/automatic-caption-generator`,
      lastModified: "2026-08-26",
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/long-video-to-shorts`,
      lastModified: "2026-08-26",
      changeFrequency: "weekly",
      priority: 0.9,
    },
  ];
}
