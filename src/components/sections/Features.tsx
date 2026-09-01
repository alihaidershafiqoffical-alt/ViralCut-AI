import { Crop, Captions, Zap, Shield, FileVideo, Cpu } from "lucide-react";

export default function Features() {
  const features = [
    {
      title: "Smart AI Video Clipping",
      desc: "Our intelligent framing engine tracks active speakers, automatically cropping horizontal landscape footage into perfect 9:16 vertical video.",
      icon: <Crop className="h-6 w-6 text-violet-400" />,
    },
    {
      title: "Automatic Captions",
      desc: "Burn eye-catching, word-by-word animated captions directly into your clips to hook viewers and maximize video retention.",
      icon: <Captions className="h-6 w-6 text-pink-400" />,
    },
    {
      title: "Long Video to Shorts AI",
      desc: "Convert long-form podcasts, streams, or lectures into multiple highly engaging social media shorts in a single run.",
      icon: <Zap className="h-6 w-6 text-emerald-400" />,
    },
    {
      title: "YouTube Shorts Generator",
      desc: "Output optimized portrait clips tailored specifically for the algorithms of YouTube Shorts, TikTok, and Instagram Reels.",
      icon: <FileVideo className="h-6 w-6 text-indigo-400" />,
    },
    {
      title: "Zero Watermarks",
      desc: "Every vertical video you generate is 100% yours to download and publish with absolutely no watermarks or logos.",
      icon: <Shield className="h-6 w-6 text-blue-400" />,
    },
    {
      title: "Fast AI Clip Generator",
      desc: "Powered by serverless GPUs and Faster-Whisper, our pipeline transcribes and edits your clips in just a few minutes.",
      icon: <Cpu className="h-6 w-6 text-rose-400" />,
    },
  ];

  return (
    <section id="features" className="py-24 px-4 bg-[#0d0e1a]/50">
      <div className="max-w-6xl mx-auto">
        
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Powerful <span className="gradient-text">AI Video Clipping</span> Features
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            ViralCut is an all-in-one AI Shorts Generator designed to streamline your short-form content creation workflow.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {features.map((feature, idx) => (
            <article key={idx} className="flex flex-col p-6 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
              <div className="mb-4 inline-flex items-center justify-center p-3 rounded-xl bg-white/[0.05] w-fit" aria-hidden="true">
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
