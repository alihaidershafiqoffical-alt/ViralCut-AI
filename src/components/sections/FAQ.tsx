export default function FAQ() {
  const faqs = [
    {
      q: "What is an AI Shorts Generator and how does it work?",
      a: "An AI Shorts Generator is an online tool that uses artificial intelligence to convert long video to Shorts. It analyzes the transcript and audio cues of a long video to find the most engaging segments, crops the video to a vertical 9:16 layout, and burns automatic captions directly onto the video. With ViralCut, you simply paste a link or upload a file, and our AI video clipping engine does the rest.",
    },
    {
      q: "Can I use ViralCut as a YouTube Shorts generator?",
      a: "Yes! ViralCut is specifically designed as a YouTube Shorts generator, TikTok clip maker, and Instagram Reels creator. The clips are generated in 1080x1920 portrait aspect ratio, complete with engaging automatic captions, making them perfectly formatted and ready to upload to any vertical video platform.",
    },
    {
      q: "How does the AI handle video clipping and framing?",
      a: "Our advanced AI video clipping system uses intelligent facial and speaker tracking to identify where the active speaker is in the original horizontal frame. It then dynamically adjusts the vertical crop window so that the subject remains centered, preventing important details from being cut off.",
    },
    {
      q: "Is there a limit on long video to Shorts conversion?",
      a: "We support long-form video uploads up to 2GB in size, as well as direct YouTube links of any length. Our AI video clip generator will scan the entire length of the video to locate the absolute best retention hooks and create multiple high-quality Shorts from it.",
    },
    {
      q: "Are the automatic captions customizable?",
      a: "Yes! Our automatic captions are transcribed using Faster-Whisper for near-perfect accuracy. Once the clips are ready, you can customize the caption text, correct spelling, adjust timing, and choose from multiple animated styles like 'Karaoke Glow' or 'Hormozi Pop' to match your personal brand.",
    },
  ];

  return (
    <section id="faq" className="py-24 px-4 border-t border-white/[0.05]" aria-labelledby="faq-heading">
      <div className="max-w-3xl mx-auto">
        <h2 id="faq-heading" className="text-3xl font-bold text-white mb-10 text-center">
          <span className="gradient-text">AI Shorts Generator</span> FAQ
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

