import { FileVideo, Video, Sliders, Shield, Zap } from "lucide-react";
import Link from "next/link";

export function LongVideoHero() {
  return (
    <section
      id="long-video-hero"
      className="relative overflow-hidden pt-36 pb-16 sm:pt-44 sm:pb-20 text-center"
      aria-label="Long Video Hero"
    >
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
        <div
          className="absolute -top-24 -left-32 h-[520px] w-[520px] rounded-full
                      bg-violet-700/10 blur-[120px]"
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
            rounded-full border border-violet-500/30
            bg-violet-500/10 px-4 py-1.5
            text-xs font-semibold uppercase tracking-widest text-violet-300
          "
        >
          <FileVideo className="h-3.5 w-3.5" />
          Long Video to Shorts Engine
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
        Long Video to Shorts: Repurpose <span className="gradient-text">Courses & Streams</span>
      </h1>

      <p
        className="
          mx-auto mt-6 max-w-2xl px-4
          text-lg sm:text-xl text-white/60 leading-relaxed
          animate-slide-up
        "
      >
        Turn hours of long-form courses, webinars, and live streams into multiple viral Shorts automatically. AI detects highlights, reframes layout coordinates, and burns subtitles.
      </p>
    </section>
  );
}

export function LongVideoHowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Upload Long Video",
      desc: "Drag and drop your lecture, webinar, or stream file (supports files up to 2GB).",
    },
    {
      num: "02",
      title: "Choose Moment Settings",
      desc: "Specify how many highlights to extract and the maximum duration for each clip.",
    },
    {
      num: "03",
      title: "AI Highlight Processing",
      desc: "The AI parses the long transcript to isolate high-retention topics, cropping visual frames dynamically.",
    },
    {
      num: "04",
      title: "Download HD Clips",
      desc: "Review your generated vertical shorts, edit subtitle timings, and export watermark-free.",
    },
  ];

  return (
    <section id="long-video-how-it-works" className="py-24 px-4 border-t border-white/[0.05]">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Convert <span className="gradient-text">Long Video to Shorts</span> in 4 Steps
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Multiply your content output. Transform one piece of long-form content into a month of vertical distribution materials.
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

export function LongVideoFeatures() {
  const features = [
    {
      title: "2GB File Size Uploads",
      desc: "Easily upload larger video files including long streams, lectures, and corporate webinars.",
      icon: <Video className="h-6 w-6 text-violet-400" />,
    },
    {
      title: "AI Hook Detection",
      desc: "Our model identifies key summary topics, definitions, jokes, or visual changes to clip natural segments.",
      icon: <Zap className="h-6 w-6 text-emerald-400" />,
    },
    {
      title: "Intelligent Frame Crop",
      desc: "The AI video clip generator adjusts crop coordinates dynamically, tracking face movements to center visual subjects.",
      icon: <Sliders className="h-6 w-6 text-pink-400" />,
    },
    {
      title: "Karaoke Caption Presets",
      desc: "Burn eye-catching dynamic text styling into vertical video files automatically to hold mobile attention.",
      icon: <FileVideo className="h-6 w-6 text-indigo-400" />,
    },
    {
      title: "Zero Watermarks",
      desc: "All generated vertical shorts are exported cleanly in high definition, ready for commercial publishing.",
      icon: <Shield className="h-6 w-6 text-blue-400" />,
    },
  ];

  return (
    <section id="long-video-features" className="py-24 px-4 bg-[#0d0e1a]/50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Built for <span className="gradient-text">Long-Form Content</span>
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Say goodbye to scrubbing timelines. Let artificial intelligence edit hours of footage into vertical clips automatically.
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

export function LongVideoFAQ() {
  const faqs = [
    {
      q: "What is the maximum duration and file size supported?",
      a: "We support video uploads up to 2GB in file size, and YouTube links of any length, letting you process 1 to 2 hour streams easily.",
    },
    {
      q: "How does the AI determine the best highlights?",
      a: "Our pipeline creates a transcript via Faster-Whisper, and a specialized Gemini model searches the text for retention hooks, summaries, and high-interest dialogue.",
    },
    {
      q: "Can I use the output on TikTok and Reels?",
      a: "Yes. The exported video files are formatted in 1080x1920 portrait format, complete with automatic captions, matching all vertical social specs.",
    },
    {
      q: "Do I need to sign up to convert long video to shorts?",
      a: "No, ViralCut is completely frictionless. Just drop a video file or link to test the editor without any signup prompts.",
    },
  ];

  return (
    <section id="long-video-faq" className="py-24 px-4 border-t border-white/[0.05]" aria-labelledby="faq-heading">
      <div className="max-w-3xl mx-auto">
        <h2 id="faq-heading" className="text-3xl font-bold text-white mb-10 text-center">
          <span className="gradient-text">Long Video to Shorts</span> FAQ
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

export function LongVideoSEOContent() {
  return (
    <article id="long-video-seo" className="py-24 px-4 bg-black/40 border-t border-white/[0.05]" aria-labelledby="seo-heading">
      <div className="max-w-4xl mx-auto prose prose-invert prose-violet">
        <h2 id="seo-heading" className="text-2xl font-bold text-white mb-4">
          Turn Webinars and Streams into Viral Content Distribution Channels
        </h2>
        <p className="text-white/60 mb-8 leading-relaxed">
          Creating long-form videos like online courses, streams, or live webinars requires massive time and effort. However, getting users to sit through an hour-long recording is difficult. Converting these long videos to Shorts lets you market your core material in bite-sized portions across YouTube, TikTok, and Reels.
        </p>
        <p className="text-white/60 mb-8 leading-relaxed">
          ViralCut automates this pipeline. Our AI video clipping tool extracts key definitions, summaries, and questions, automatically cropping the horizontal footage into vertical 9:16 layout. Animated subtitles are automatically burned in, ensuring viewers understand your clips even with their mobile audio muted.
        </p>

        <h3 className="text-xl font-semibold text-white mb-3">Explore Other Features</h3>
        <p className="text-sm text-violet-300 space-x-4">
          <Link href="/podcast-to-shorts" className="hover:underline">Podcast to Shorts AI</Link>
          <span>•</span>
          <Link href="/youtube-shorts-generator" className="hover:underline">YouTube Shorts Generator</Link>
          <span>•</span>
          <Link href="/automatic-caption-generator" className="hover:underline">Automatic Caption Generator</Link>
          <span>•</span>
          <Link href="/" className="hover:underline">AI Shorts Generator Home</Link>
        </p>
      </div>
    </article>
  );
}
