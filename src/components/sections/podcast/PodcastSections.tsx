import { Mic, Users, Headphones, Volume2, ShieldAlert } from "lucide-react";
import Link from "next/link";

export function PodcastHero() {
  return (
    <section
      id="podcast-hero"
      className="relative overflow-hidden pt-36 pb-16 sm:pt-44 sm:pb-20 text-center"
      aria-label="Podcast Hero"
    >
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
        <div
          className="absolute -top-24 -left-32 h-[520px] w-[520px] rounded-full
                      bg-violet-700/20 blur-[120px]"
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
          <Mic className="h-3.5 w-3.5" />
          Podcast to Shorts AI Engine
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
        Podcast to Shorts: Turn Episodes into <span className="gradient-text">Viral Clips</span>
      </h1>

      <p
        className="
          mx-auto mt-6 max-w-2xl px-4
          text-lg sm:text-xl text-white/60 leading-relaxed
          animate-slide-up
        "
      >
        Convert long podcast audio and video episodes into high-retention social clips. Our AI detects active speakers, tracks conversation flow, and generates ready-to-post Shorts automatically.
      </p>
    </section>
  );
}

export function PodcastHowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Import Podcast URL",
      desc: "Paste your video podcast link from YouTube or upload your raw MP4/MOV file.",
    },
    {
      num: "02",
      title: "Set Clip Length",
      desc: "Configure how many Shorts to generate and set your desired maximum duration per clip.",
    },
    {
      num: "03",
      title: "AI Finds Guest Hooks",
      desc: "The AI parses dialog to clip key arguments, tracking speaker faces to crop to vertical portrait layout.",
    },
    {
      num: "04",
      title: "Edit & Download",
      desc: "Fine-tune transcript captions, style the layout, and export watermark-free HD video.",
    },
  ];

  return (
    <section id="podcast-how-it-works" className="py-24 px-4 border-t border-white/[0.05]">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Convert <span className="gradient-text">Podcast to Shorts</span> in 4 Steps
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Scale your podcast marketing effortlessly. Turn a single guest interview into a week&apos;s worth of short clips.
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

export function PodcastFeatures() {
  const features = [
    {
      title: "Active Speaker Detection",
      desc: "Intelligent AI tracking centers the frame on whoever is currently speaking, handling dynamic back-and-forth guest conversations.",
      icon: <Users className="h-6 w-6 text-violet-400" />,
    },
    {
      title: "Topic Highlight Finder",
      desc: "Natural language AI identifies natural topic changes, jokes, and major interview hooks to segment the long video.",
      icon: <Mic className="h-6 w-6 text-pink-400" />,
    },
    {
      title: "Podcast Caption Styles",
      desc: "Generate professional podcast subtitles with bold text and emojis, styled in popular show formats to increase watch time.",
      icon: <Headphones className="h-6 w-6 text-emerald-400" />,
    },
    {
      title: "Audio Noise Reduction",
      desc: "Preserve crystal clear dialogue. AI enhances the spoken vocal track so your shorts sound perfect on mobile speakers.",
      icon: <Volume2 className="h-6 w-6 text-indigo-400" />,
    },
    {
      title: "Zero Watermarks",
      desc: "Get clean vertical exports. Publish podcast highlights under your own brand with zero third-party watermark tags.",
      icon: <ShieldAlert className="h-6 w-6 text-blue-400" />,
    },
  ];

  return (
    <section id="podcast-features" className="py-24 px-4 bg-[#0d0e1a]/50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Optimized for <span className="gradient-text">Show Growth</span>
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Everything you need to turn deep-dive conversation episodes into virally shareable visual snippets.
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

export function PodcastFAQ() {
  const faqs = [
    {
      q: "Does the podcast to shorts tool support multiple guests?",
      a: "Yes. Our active speaker detection tracks faces and frames whoever is talking, dynamically panning or splitting when guests interact.",
    },
    {
      q: "How long of an episode can I import?",
      a: "We support YouTube URLs of any length, and local file uploads of up to 2GB, allowing you to easily process 1 to 2 hour podcast episodes.",
    },
    {
      q: "Can I customize the generated podcast captions?",
      a: "Absolutely. Once the clips are ready, you can choose from different text layouts, fonts, colors, and correct any specific names in the transcription.",
    },
    {
      q: "Is there any watermark on the output?",
      a: "No, all exports are completely clean and exported in pristine HD format, leaving you with ready-to-post, professional shorts.",
    },
  ];

  return (
    <section id="podcast-faq" className="py-24 px-4 border-t border-white/[0.05]" aria-labelledby="faq-heading">
      <div className="max-w-3xl mx-auto">
        <h2 id="faq-heading" className="text-3xl font-bold text-white mb-10 text-center">
          <span className="gradient-text">Podcast to Shorts</span> FAQ
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

export function PodcastSEOContent() {
  return (
    <article id="podcast-seo" className="py-24 px-4 bg-black/40 border-t border-white/[0.05]" aria-labelledby="seo-heading">
      <div className="max-w-4xl mx-auto prose prose-invert prose-violet">
        <h2 id="seo-heading" className="text-2xl font-bold text-white mb-4">
          Convert Long Podcast Episodes Into Viral Vertical Clips
        </h2>
        <p className="text-white/60 mb-8 leading-relaxed">
          Marketing long podcast episodes can be incredibly challenging. While audiences love deep, long-form content, discovery algorithms on platforms like YouTube, TikTok, and Instagram are heavily biased towards portrait short-form video. That is where our podcast to shorts AI engine comes in. It analyzes your audio file or YouTube recording, clips the most engaging portions, and reframes them for 9:16 layout.
        </p>
        <p className="text-white/60 mb-8 leading-relaxed">
          By publishing bite-sized vertical segments with animated subtitles, you can attract new listeners, capture attention on mobile scroll feeds, and funnel organic traffic back to your main episode.
        </p>

        <h3 className="text-xl font-semibold text-white mb-3">Explore Other Features</h3>
        <p className="text-sm text-violet-300 space-x-4">
          <Link href="/youtube-shorts-generator" className="hover:underline">YouTube Shorts Generator</Link>
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
