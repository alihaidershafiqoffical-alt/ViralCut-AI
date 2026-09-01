import { Sparkles, Captions, AlignLeft, Palette, Globe, CheckSquare } from "lucide-react";
import Link from "next/link";

export function CaptionsHero() {
  return (
    <section
      id="captions-hero"
      className="relative overflow-hidden pt-36 pb-16 sm:pt-44 sm:pb-20 text-center"
      aria-label="Captions Hero"
    >
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
        <div
          className="absolute -top-24 -left-32 h-[520px] w-[520px] rounded-full
                      bg-pink-700/10 blur-[120px]"
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
            rounded-full border border-pink-500/30
            bg-pink-500/10 px-4 py-1.5
            text-xs font-semibold uppercase tracking-widest text-pink-300
          "
        >
          <Captions className="h-3.5 w-3.5" />
          Automatic Caption Generator
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
        Automatic Caption Generator: Add <span className="gradient-text">Dynamic Subtitles</span>
      </h1>

      <p
        className="
          mx-auto mt-6 max-w-2xl px-4
          text-lg sm:text-xl text-white/60 leading-relaxed
          animate-slide-up
        "
      >
        Transcribe any video automatically. Choose from vibrant kinetic caption styles, customize timing, fonts, and colors to maximize viewer engagement on silent mobile feeds.
      </p>
    </section>
  );
}

export function CaptionsHowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Upload Video",
      desc: "Drag and drop your MP4/MOV video, or paste a YouTube URL to get started.",
    },
    {
      num: "02",
      title: "Auto Transcription",
      desc: "Our high-accuracy Faster-Whisper model converts audio speech to text transcript in seconds.",
    },
    {
      num: "03",
      title: "Style & Font Design",
      desc: "Choose animation presets like Karaoke Glow or Hormozi Pop. Adjust font size and vertical alignment.",
    },
    {
      num: "04",
      title: "Export & Burn In",
      desc: "Preview the video captions in real-time, and download the finished HD video file.",
    },
  ];

  return (
    <section id="captions-how-it-works" className="py-24 px-4 border-t border-white/[0.05]">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Add <span className="gradient-text">Subtitles to Video</span> in 4 Steps
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Quick, accurate, and fully customizable. Increase your watch-time retention by keeping eyes on the screen.
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

export function CaptionsFeatures() {
  const features = [
    {
      title: "Faster-Whisper Transcription",
      desc: "State-of-the-art automatic speech recognition engine transcribes vocals with high word-level accuracy.",
      icon: <AlignLeft className="h-6 w-6 text-pink-400" />,
    },
    {
      title: "Animated Karaoke Presets",
      desc: "Word-by-word highlights styled with active glow effects, matching modern content creation trends.",
      icon: <Palette className="h-6 w-6 text-violet-400" />,
    },
    {
      title: "Multilingual Support",
      desc: "Transcribe speeches across multiple global languages, automatically formatting translation subtitles.",
      icon: <Globe className="h-6 w-6 text-emerald-400" />,
    },
    {
      title: "Subtitle Text Editor",
      desc: "Easy interactive interface to adjust word spelling, fix abbreviations, and fine-tune word timing sync.",
      icon: <CheckSquare className="h-6 w-6 text-indigo-400" />,
    },
    {
      title: "Zero Watermarks",
      desc: "Add subtitles to your videos without distracting watermark tags, keeping your content professional.",
      icon: <Sparkles className="h-6 w-6 text-blue-400" />,
    },
  ];

  return (
    <section id="captions-features" className="py-24 px-4 bg-[#0d0e1a]/50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Advanced <span className="gradient-text">Subtitling Suite</span>
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Design stunning, high-converting video captions that capture attention even when users scroll with audio muted.
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

export function CaptionsFAQ() {
  const faqs = [
    {
      q: "How accurate is the automatic transcription?",
      a: "Our speech recognition uses Faster-Whisper, which is over 95% accurate for clear English dialog, and handles common accents with ease.",
    },
    {
      q: "Can I modify the caption text and timings?",
      a: "Yes! In the editor, you can edit text strings word-by-word and adjust exact frame timings if needed.",
    },
    {
      q: "What design presets are available for captions?",
      a: "We offer presets such as 'Karaoke Glow', 'Hormozi Pop', 'Cyberpunk Neon', and clean minimal layout styles.",
    },
    {
      q: "Are the subtitles burned into the video file?",
      a: "Yes, they are hard-coded into the downloaded MP4 file, guaranteeing that subtitles appear on all media players and social apps.",
    },
  ];

  return (
    <section id="captions-faq" className="py-24 px-4 border-t border-white/[0.05]" aria-labelledby="faq-heading">
      <div className="max-w-3xl mx-auto">
        <h2 id="faq-heading" className="text-3xl font-bold text-white mb-10 text-center">
          <span className="gradient-text">Automatic Caption Generator</span> FAQ
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

export function CaptionsSEOContent() {
  return (
    <article id="captions-seo" className="py-24 px-4 bg-black/40 border-t border-white/[0.05]" aria-labelledby="seo-heading">
      <div className="max-w-4xl mx-auto prose prose-invert prose-violet">
        <h2 id="seo-heading" className="text-2xl font-bold text-white mb-4">
          Boost Engagement with Dynamic Automatic Subtitles
        </h2>
        <p className="text-white/60 mb-8 leading-relaxed">
          Over 80% of short-form videos on mobile platforms like TikTok, Reels, and YouTube Shorts are watched with the sound muted. If your video does not feature highly readable and engaging subtitles, viewers will swipe past in the first few seconds. Typing captions word-by-word is slow and painful.
        </p>
        <p className="text-white/60 mb-8 leading-relaxed">
          Our automatic caption generator eliminates this chore. Our pipeline transcribes the speech track, syncs text timing, and overlays beautiful, responsive text formatting. Customize your branding presets, tweak spellings, and generate high-quality subtitled video clips in minutes.
        </p>

        <h3 className="text-xl font-semibold text-white mb-3">Explore Other Features</h3>
        <p className="text-sm text-violet-300 space-x-4">
          <Link href="/podcast-to-shorts" className="hover:underline">Podcast to Shorts AI</Link>
          <span>•</span>
          <Link href="/youtube-shorts-generator" className="hover:underline">YouTube Shorts Generator</Link>
          <span>•</span>
          <Link href="/long-video-to-shorts" className="hover:underline">Long Video to Shorts AI</Link>
          <span>•</span>
          <Link href="/" className="hover:underline">AI Shorts Generator Home</Link>
        </p>
      </div>
    </article>
  );
}
