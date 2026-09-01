import { Wand2, Subtitles, Download } from "lucide-react";

export default function HowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Upload Video",
      desc: "Drag & drop your video file or paste a YouTube link. We accept MP4, MOV, WebM, and direct URLs.",
      icon: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-6 w-6 text-indigo-400"
        >
          <path d="M2.5 7.1C2.6 6.3 3.3 5.6 4.1 5.5C5.9 5.2 12 5.2 12 5.2s6.1 0 7.9.3c.8.1 1.5.8 1.6 1.6.3 1.9.3 5.9.3 5.9s0 4-.3 5.9c-.1.8-.8 1.5-1.6 1.6-1.8.3-7.9.3-7.9.3s-6.1 0-7.9-.3c-.8-.1-1.5-.8-1.6-1.6C2.2 16.1 2.2 12.1 2.2 12.1s0-4 .3-5.9z" />
          <polygon points="9.75 15.02 15.5 12 9.75 8.98 9.75 15.02" />
        </svg>
      ),
    },
    {
      num: "02",
      title: "Choose Shorts",
      desc: "Select how many Shorts you want (e.g. 5 or 10) and the maximum duration for each clip.",
      icon: <Wand2 className="h-6 w-6 text-violet-400" />,
    },
    {
      num: "03",
      title: "AI Finds Best Moments",
      desc: "Our AI scans the transcript for viral hooks, crops to 9:16, and automatically burns animated captions.",
      icon: <Subtitles className="h-6 w-6 text-pink-400" />,
    },
    {
      num: "04",
      title: "Preview & Download",
      desc: "Review your generated Shorts. Download them in high definition, instantly ready to post to TikTok or Reels.",
      icon: <Download className="h-6 w-6 text-emerald-400" />,
    },
  ];

  return (
    <section id="how-it-works" className="py-24 px-4 border-t border-white/[0.05]">
      <div className="max-w-6xl mx-auto">
        
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Convert <span className="gradient-text">Long Video to Shorts</span> in 4 Steps
          </h2>
          <p className="text-white/50 max-w-xl mx-auto">
            Our AI video clip generator transforms podcasts, streams, or webinars into high-retention vertical clips ready for social platforms.
          </p>
        </div>

        <ol className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 list-none p-0 m-0" aria-label="Steps to generate viral shorts">
          {steps.map((step, idx) => (
            <li key={idx}>
              <article className="relative p-6 glass rounded-2xl group hover:-translate-y-1 transition-transform duration-300 h-full">
                <div className="absolute top-4 right-4 text-4xl font-bold text-white/[0.03] pointer-events-none" aria-hidden="true">
                  {step.num}
                </div>
                <div className="h-12 w-12 rounded-xl bg-white/[0.05] flex items-center justify-center mb-6 border border-white/10 group-hover:bg-violet-500/10 transition-colors" aria-hidden="true">
                  {step.icon}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{step.desc}</p>
              </article>
            </li>
          ))}
        </ol>

      </div>
    </section>
  );
}
