import AdSenseBanner from "@/components/ui/AdSenseBanner";

export default function SEOContent() {
  return (
    <article id="seo" className="py-24 px-4 bg-black/40 border-t border-white/[0.05]" aria-labelledby="seo-heading">
      <div className="max-w-4xl mx-auto prose prose-invert prose-violet">
        <h2 id="seo-heading" className="text-2xl font-bold text-white mb-4">
          What is an AI Shorts Generator?
        </h2>
        <p className="text-white/60 mb-8 leading-relaxed">
          An <strong>AI Shorts Generator</strong> is an advanced web-based tool that utilizes machine learning and natural language processing to automatically convert long video to Shorts. Instead of manually parsing hours of footage, creators can leverage an AI video clip generator to identify the most engaging and viral highlights. The engine handles complex editing tasks like vertical 9:16 cropping, speaker tracking, and burning automatic captions directly onto the video, making it instantly shareable.
        </p>

        <h3 className="text-xl font-semibold text-white mb-3">
          Why Choose ViralCut as Your YouTube Shorts Generator?
        </h3>
        <p className="text-white/60 mb-8 leading-relaxed">
          Short-form video is the fastest way to grow an audience online, but manual editing is incredibly tedious. ViralCut acts as a dedicated YouTube Shorts generator, TikTok clipper, and Reels maker all in one. With our advanced AI video clipping algorithm and highly accurate automatic captions, you can turn a single podcast episode or live stream into dozens of high-retention clips. Scale your content output, save hours of manual editing time, and dominate short-form feeds with zero watermarks.
        </p>

        <AdSenseBanner slot="9876543210" className="mt-12" />
      </div>
    </article>
  );
}

