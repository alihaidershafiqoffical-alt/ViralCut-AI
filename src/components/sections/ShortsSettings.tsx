// =============================================================================
// components/sections/ShortsSettings.tsx — Configuration panel shown after
// the user selects a video source. Lets them pick count, duration, and topic.
// =============================================================================
"use client";

import { useState } from "react";
import { Settings2, Wand2 } from "lucide-react";
import type {
  VideoSource,
  ShortsConfig,
  ShortCountPreset,
  ShortDurationPreset,
} from "@/types/index";
import { formatFileSize } from "@/lib/formatters";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const COUNT_PRESETS: ShortCountPreset[]       = [1, 2, 3, 4];
const DURATION_PRESETS: ShortDurationPreset[] = [15, 30, 45, 60];
type AspectRatioPresetKey = "9:16" | "4:5" | "3:4" | "1:1" | "2:3";
const ASPECT_PRESETS: AspectRatioPresetKey[] = ["9:16", "4:5", "3:4", "1:1", "2:3"];

const ASPECT_LABELS: Record<AspectRatioPresetKey, string> = {
  "9:16": "9:16 (Vertical)",
  "4:5": "4:5 (Social)",
  "3:4": "3:4 (Portrait)",
  "1:1": "1:1 (Square)",
  "2:3": "2:3 (Classic)",
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface Props {
  source: VideoSource;
  onBack: () => void;
  onGenerate: (config: ShortsConfig) => void;
}

// ---------------------------------------------------------------------------
// Sub-component: Pill selector row
// ---------------------------------------------------------------------------
interface PillGroupProps<T extends string | number> {
  label: string;
  description?: string;
  options: T[];
  selected: T;
  onSelect: (v: T) => void;
  formatLabel?: (v: T) => string;
}
function PillGroup<T extends string | number>({
  label,
  description,
  options,
  selected,
  onSelect,
  formatLabel,
}: PillGroupProps<T>) {
  return (
    <div className="space-y-2.5">
      <div>
        <p className="text-sm font-semibold text-white/80">{label}</p>
        {description && (
          <p className="text-xs text-white/35 mt-0.5">{description}</p>
        )}
      </div>
      <div className="flex flex-wrap gap-2" role="group" aria-label={label}>
        {options.map((opt) => (
          <button
            key={String(opt)}
            type="button"
            role="radio"
            aria-checked={selected === opt}
            onClick={() => onSelect(opt)}
            className={`pill ${selected === opt ? "pill-active" : ""}`}
          >
            {formatLabel ? formatLabel(opt) : String(opt)}
          </button>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------
export default function ShortsSettings({ source, onBack, onGenerate }: Props) {
  const [config, setConfig] = useState<ShortsConfig>({
    count: 3,
    customCount: 3,
    duration: 30,
    topic: "",
    aspectRatio: "9:16",
  });

  const [enableTrim, setEnableTrim] = useState(false);
  const [trimStart, setTrimStart] = useState<number>(0);
  const [trimEnd, setTrimEnd] = useState<number>(60);

  function setCount(count: ShortCountPreset)       { setConfig((c) => ({ ...c, count })); }
  function setDuration(duration: ShortDurationPreset) { setConfig((c) => ({ ...c, duration })); }
  function setAspectRatio(aspectRatio: AspectRatioPresetKey) { setConfig((c) => ({ ...c, aspectRatio })); }
  function setCustomCount(e: React.ChangeEvent<HTMLInputElement>) {
    const v = Math.min(4, Math.max(1, parseInt(e.target.value, 10) || 1));
    setConfig((c) => ({ ...c, customCount: v }));
  }
  function setTopic(e: React.ChangeEvent<HTMLInputElement>) {
    setConfig((c) => ({ ...c, topic: e.target.value }));
  }

  const effectiveCount = config.count === "custom" ? config.customCount : config.count;

  const handleGenerateClick = () => {
    const finalConfig: ShortsConfig = {
      ...config,
      startTime: enableTrim ? trimStart : undefined,
      endTime: enableTrim ? trimEnd : undefined,
    };
    onGenerate(finalConfig);
  };

  return (
    <section
      id="shorts-settings"
      className="mx-auto max-w-2xl w-full px-4 animate-slide-up"
      aria-label="Shorts generation settings"
    >
      {/* ── Card ── */}
      <div className="glass rounded-2xl p-6 sm:p-8 space-y-7">

        {/* Header row */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Settings2 className="h-4 w-4 text-violet-400" aria-hidden="true" />
              <h2 className="text-base font-semibold text-white">
                Configure Your Shorts
              </h2>
            </div>
            {/* Source summary */}
            <p className="text-xs text-white/35 truncate max-w-[280px]">
              {source.type === "upload"
                ? `${source.displayName} · ${formatFileSize(source.sizeBytes)}`
                : source.displayName}
            </p>
          </div>

          <button
            type="button"
            onClick={onBack}
            className="text-xs text-white/35 hover:text-white/70 underline transition-colors shrink-0"
          >
            Change video
          </button>
        </div>

        {/* ── Divider ── */}
        <hr className="border-white/[0.07]" />

        {/* ── How many Shorts? ── */}
        <PillGroup
          label="How many Shorts?"
          description="Number of clips to generate from your video."
          options={COUNT_PRESETS}
          selected={config.count}
          onSelect={setCount}
          formatLabel={(v) => (v === "custom" ? "Custom" : String(v))}
        />

        {/* Custom count input — shown only when "Custom" is selected */}
        {config.count === "custom" && (
          <div className="flex items-center gap-3 animate-slide-down pl-1">
            <label htmlFor="custom-count" className="text-sm text-white/50 whitespace-nowrap">
              Exact number:
            </label>
            <input
              id="custom-count"
              type="number"
              min={1}
              max={20}
              value={config.customCount}
              onChange={setCustomCount}
              className="
                w-24 rounded-lg bg-white/[0.05] border border-white/10
                px-3 py-2 text-sm text-white text-center
                focus:outline-none focus:ring-2 focus:ring-violet-500/60
              "
            />
            <span className="text-xs text-white/30">(1 – 20)</span>
          </div>
        )}

        {/* ── Short Duration ── */}
        <PillGroup
          label="Max Duration per Short"
          description="Clips will be trimmed to this length or shorter."
          options={DURATION_PRESETS}
          selected={config.duration}
          onSelect={setDuration}
          formatLabel={(v) => `${v}s`}
        />

        {/* ── Target Aspect Ratio ── */}
        <PillGroup
          label="Target Aspect Ratio"
          description="Output resolution layout for your Short clips."
          options={ASPECT_PRESETS}
          selected={config.aspectRatio}
          onSelect={setAspectRatio}
          formatLabel={(v) => ASPECT_LABELS[v]}
        />

        {/* ── Topic hint ── */}
        <div className="space-y-2.5">
          <div>
            <label
              htmlFor="topic-input"
              className="text-sm font-semibold text-white/80"
            >
              Video Topic{" "}
              <span className="font-normal text-white/30">(optional)</span>
            </label>
            <p className="text-xs text-white/35 mt-0.5">
              Helps the AI focus on the most relevant segments.
            </p>
          </div>
          <input
            id="topic-input"
            type="text"
            value={config.topic}
            onChange={setTopic}
            maxLength={100}
            placeholder="e.g. Startup lessons, React tutorial, Productivity tips..."
            className="
              w-full rounded-xl bg-white/[0.04] border border-white/10
              px-4 py-3 text-sm text-white placeholder-white/20
              focus:outline-none focus:ring-2 focus:ring-violet-500/60 focus:border-transparent
              transition-all duration-200
            "
          />
        </div>

        {/* ── Trim Video Segment (For Long Videos) ── */}
        <div className="space-y-3.5 p-4 rounded-xl bg-white/[0.02] border border-white/5">
          <div className="flex items-center gap-2">
            <input
              id="trim-video-checkbox"
              type="checkbox"
              checked={enableTrim}
              onChange={(e) => setEnableTrim(e.target.checked)}
              className="rounded border-white/10 text-violet-600 focus:ring-violet-500/60 bg-white/[0.05] h-4 w-4"
            />
            <label htmlFor="trim-video-checkbox" className="text-sm font-semibold text-white/80 cursor-pointer">
              Process specific segment only (Pre-Trim Video)
            </label>
          </div>
          <p className="text-xs text-white/35">
            Perfect for long videos: transcribes and extracts clips only from your chosen range.
          </p>

          {enableTrim && (
            <div className="grid grid-cols-2 gap-4 animate-slide-down pt-1.5">
              <div className="space-y-1.5">
                <label htmlFor="trim-start-input" className="text-xs text-white/50">
                  Start Time (seconds)
                </label>
                <input
                  id="trim-start-input"
                  type="number"
                  min={0}
                  value={trimStart}
                  onChange={(e) => setTrimStart(Math.max(0, parseFloat(e.target.value) || 0))}
                  className="w-full rounded-lg bg-white/[0.04] border border-white/10 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500/60"
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="trim-end-input" className="text-xs text-white/50">
                  End Time (seconds)
                </label>
                <input
                  id="trim-end-input"
                  type="number"
                  min={1}
                  value={trimEnd}
                  onChange={(e) => setTrimEnd(Math.max(1, parseFloat(e.target.value) || 0))}
                  className="w-full rounded-lg bg-white/[0.04] border border-white/10 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500/60"
                />
              </div>
            </div>
          )}
        </div>

        {/* ── Generate CTA ── */}
        <button
          type="button"
          onClick={handleGenerateClick}
          className="
            gradient-cta w-full rounded-xl py-4 px-6
            text-base font-semibold text-white
            shadow-xl shadow-violet-900/40
            flex items-center justify-center gap-2.5
          "
        >
          <Wand2 className="h-5 w-5" aria-hidden="true" />
          Generate {effectiveCount} Short{effectiveCount !== 1 ? "s" : ""}{" "}
          · {config.duration}s max
        </button>
      </div>
    </section>
  );
}
