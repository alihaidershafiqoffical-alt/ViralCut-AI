import { Link2, Download, Zap, Heart } from "lucide-react";
import Link from "next/link";

function YoutubeIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M2.5 7.1C2.6 6.3 3.3 5.6 4.1 5.5C5.9 5.2 12 5.2 12 5.2s6.1 0 7.9.3c.8.1 1.5.8 1.6 1.6.3 1.9.3 5.9.3 5.9s0 4-.3 5.9c-.1.8-.8 1.5-1.6 1.6-1.8.3-7.9.3-7.9.3s-6.1 0-7.9-.3c-.8-.1-1.5-.8-1.6-1.6C2.2 16.1 2.2 12.1 2.2 12.1s0-4 .3-5.9z" />
      <polygon points="9.75 15.02 15.5 12 9.75 8.98 9.75 15.02" />
    </svg>
  );
}

export function YoutubeHero() {
  return (
    <section
      id="youtube-hero"
      className="relative overflow-hidden pt-36 pb-16 sm:pt-44 sm:pb-20 text-center"
      aria-label="YouTube Hero"
    >
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
        <div
          className="absolute -top-24 -left-32 h-[520px] w-[520px] rounded-full
                      bg-red-700/10 blur-[120px]"
          style={{ animation: "float 8s ease-in-out infinite" }}
        />
        <div
          className="absolute inset-0 opacity-[0.025]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.15) 1px,transparent 1px)," +
              "linear-gradient(90deg,rgba(255,255,255,0.15) 1px,transparent 1px)",
            backgroundSize: "56px 56px",
          }}
        />
      </div>

      <div className="mb-6 animate-fade-in">
        <span
          className="
            inline-flex items-center gap-2
            rounded-full border border-red-500/30
            bg-red-500/10 px-4 py-1.5
            text-xs font-semibold uppercase tracking-widest text-red-300
          "
        >
          <YoutubeIcon className="h-3.5 w-3.5" />
          YouTube Shorts Generator
        </span>
      </div>

      <h1
        className="
          mx-auto max-w-4xl px-4
          text-4xl sm:text-5xl md:text-6xl lg:text-7xl
          font-extrabold leading-[1.08] tracking-tight
          text-white
          animate-slide-up
        "
        style={{ fontFamily: "var(--font-heading, inherit)" }}
      >
        Free YouTube Shorts Generator: Convert <span className="gradient-text">Videos in Seconds</span>
      </h1>

      <p
        className="
          mx-auto mt-6 max-w-2xl px-4
          text-lg sm:text-xl text-white/60 leading-relaxed
          animate-slide-up
        "
      >
        Paste any public YouTube link to extract the most engaging moments automatically. No downloads, no software installations—just instant vertical clips with automated subtitles.
      </p>
    </section>
  );
}

export function YoutubeHowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Paste YouTube Link",
      desc: "Copy your long video URL from YouTube and paste it directly into our input field.",
    },
    {
      num: "02",
      title: "AI Moment Detection",
      desc: "Our AI scans the video's transcript and sound cues to find high-retention highlights.",
    },
    {
      num: "03",
      title: "Crop to Portrait 9:16",
      desc: "AI identifies key visual focus, automatically framing active speakers in vertical format.",
    },
    {
      num: "04",
      title: "Save as MP4",
      desc: "Preview your generated YouTube Shorts, adjust caption styles, and export in full HD.",
    },
  ];

  return (
    <section id="youtube-how-it-works" className="py-24 px-4 border-t border-white/[0.05]">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Convert <span className="gradient-text">YouTube Videos to Shorts</span> in 4 Steps
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Zero friction. Repurpose existing channel content to scale up your publication schedule and get more subscribers.
          </p>
        </div>

        <ol className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 list-none p-0 m-0">
          {steps.map((step, idx) => (
            <li key={idx}>
              <article className="relative p-6 glass rounded-2xl group hover:-translate-y-1 transition-transform duration-300 h-full">
                <div className="absolute top-4 right-4 text-4xl font-bold text-white/[0.03] pointer-events-none">
                  {step.num}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2 mt-4">{step.title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{step.desc}</p>
              </article>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function YoutubeFeatures() {
  const features = [
    {
      title: "Direct YouTube Link Fetching",
      desc: "Skip long download times. Our cloud servers fetch and process public YouTube videos directly in the background.",
      icon: <Link2 className="h-6 w-6 text-red-400" />,
    },
    {
      title: "Algorithmic Retention Focus",
      desc: "The AI highlights finder extracts moments that follow viral video patterns to keep viewers watching past the 3-second mark.",
      icon: <Zap className="h-6 w-6 text-yellow-400" />,
    },
    {
      title: "Vertical 9:16 Reframing",
      desc: "Landscape video to portrait conversion with intelligent speaker tracking keeping the visual centered.",
      icon: <YoutubeIcon className="h-6 w-6 text-red-500" />,
    },
    {
      title: "Animated Karaoke Subtitles",
      desc: "Engage mobile audiences instantly. Auto subtitle generation burns text directly into the video file.",
      icon: <Download className="h-6 w-6 text-emerald-400" />,
    },
    {
      title: "Zero Watermarks",
      desc: "Maintain your content's aesthetic integrity. Every Short you generate is completely yours without third-party logos.",
      icon: <Heart className="h-6 w-6 text-pink-400" />,
    },
  ];

  return (
    <section id="youtube-features" className="py-24 px-4 bg-[#0d0e1a]/50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Designed for <span className="gradient-text">YouTube Creators</span>
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Scale your channel growth. Repurpose horizontal content into multiple vertical shorts to boost reach and attract subscribers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {features.map((feature, idx) => (
            <article key={idx} className="flex flex-col p-6 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
              <div className="mb-4 inline-flex items-center justify-center p-3 rounded-xl bg-white/[0.05] w-fit">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-white/50 leading-relaxed">{feature.desc}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function YoutubeFAQ() {
  const faqs = [
    {
      q: "Can I convert any YouTube video to Shorts?",
      a: "Yes! You can paste links to any public YouTube video that does not have embed restrictions.",
    },
    {
      q: "Do I need to download the YouTube video first?",
      a: "No. You only need to provide the link. Our cloud pipeline will fetch, transcribe, and clip the video directly in the background.",
    },
    {
      q: "Does it support long YouTube streams?",
      a: "Yes. Our AI video clip generator can analyze streams and podcasts of up to 1-2 hours in length to locate engaging clips.",
    },
    {
      q: "Are the generated YouTube Shorts free of watermarks?",
      a: "Yes. All vertical videos are exported in full definition and completely free of any logos or watermarks.",
    },
  ];

  return (
    <section id="youtube-faq" className="py-24 px-4 border-t border-white/[0.05]" aria-labelledby="faq-heading">
      <div className="max-w-3xl mx-auto">
        <h2 id="faq-heading" className="text-3xl font-bold text-white mb-10 text-center">
          <span className="gradient-text">YouTube Shorts Generator</span> FAQ
        </h2>
        <dl className="space-y-4">
          {faqs.map((faq, idx) => (
            <div key={idx} className="glass p-6 rounded-2xl">
              <dt className="text-base sm:text-lg font-medium text-white mb-2">{faq.q}</dt>
              <dd className="text-sm text-white/50 leading-relaxed m-0">{faq.a}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

export function YoutubeSEOContent() {
  return (
    <article id="youtube-seo" className="py-24 px-4 bg-black/40 border-t border-white/[0.05]" aria-labelledby="seo-heading">
      <div className="max-w-4xl mx-auto prose prose-invert prose-violet">
        <h2 id="seo-heading" className="text-2xl font-bold text-white mb-4">
          Grow Your Subscriber Base with a Free YouTube Shorts Generator
        </h2>
        <p className="text-white/60 mb-8 leading-relaxed">
          YouTube Shorts are currently one of the primary drivers of organic growth on the platform. The algorithm pushes vertical video format to hundreds of millions of users daily. By transforming your existing long video uploads into vertical shorts, you can double your impressions and drive viewer traffic back to your main channel page.
        </p>
        <p className="text-white/60 mb-8 leading-relaxed">
          ViralCut is designed specifically to simplify this conversion process. Paste your long video link, let the AI clipping system extract the best moments, edit the automatic captions, and export high-definition portrait MP4 files ready for publication.
        </p>

        <h3 className="text-xl font-semibold text-white mb-3">Explore Other Features</h3>
        <p className="text-sm text-violet-300 space-x-4">
          <Link href="/podcast-to-shorts" className="hover:underline">Podcast to Shorts AI</Link>
          <span>•</span>
          <Link href="/automatic-caption-generator" className="hover:underline">Automatic Caption Generator</Link>
          <span>•</span>
          <Link href="/long-video-to-shorts" className="hover:underline">Long Video to Shorts AI</Link>
          <span>•</span>
          <Link href="/" className="hover:underline">AI Shorts Generator Home</Link>
        </p>
      </div>
    </article>
  );
}
