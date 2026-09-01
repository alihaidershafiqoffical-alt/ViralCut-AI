// =============================================================================
// types/index.ts — Central type definitions for the ViralCut frontend.
// All shared interfaces, enums, and type aliases live here.
// =============================================================================

// ---------------------------------------------------------------------------
// APP STATE — controls which UI panel is visible
// ---------------------------------------------------------------------------

/** The four sequential stages of the ViralCut generation flow. */
export type AppStage = "input" | "settings" | "processing" | "results";

// ---------------------------------------------------------------------------
// VIDEO INPUT
// ---------------------------------------------------------------------------

/** Which tab is active in the VideoInput component. */
export type InputTab = "upload" | "url";

/** A validated video source chosen by the user. */
export interface VideoSource {
  /** "upload" when the user dropped / selected a file; "url" for a pasted link. */
  type: InputTab;
  /** The raw File object (only populated when type === "upload"). */
  file?: File;
  /** The pasted URL string (only populated when type === "url"). */
  url?: string;
  /** Human-readable display name (filename or hostname). */
  displayName: string;
  /** File size in bytes (0 for URL sources). */
  sizeBytes: number;
  /** Backend job/video ID returned after upload or URL ingestion. */
  videoId?: string;
  /** Provider that handled the source (e.g. "youtube", "direct_url"). */
  provider?: string;
}

// ---------------------------------------------------------------------------
// SHORTS SETTINGS
// ---------------------------------------------------------------------------

/** Preset options for the number of Shorts to generate. */
export type ShortCountPreset = 1 | 2 | 3 | 4 | 5 | 10 | "custom";

/** Preset options for the maximum duration of each Short (seconds). */
export type ShortDurationPreset = 15 | 30 | 45 | 60;

/** Configuration options chosen in the ShortsSettings panel. */
export interface ShortsConfig {
  /** How many Shorts to generate. */
  count: ShortCountPreset;
  /** Custom count — only used when `count === "custom"`. */
  customCount: number;
  /** Maximum duration for each Short in seconds. */
  duration: ShortDurationPreset;
  /** Optional topic/title hint for the Gemini AI. */
  topic: string;
  /** Target aspect ratio preset (e.g. 9:16, 4:5, 3:4, 1:1, 2:3). */
  aspectRatio: "9:16" | "4:5" | "3:4" | "1:1" | "2:3";
  /** Optional start timestamp for pre-trimming. */
  startTime?: number;
  /** Optional end timestamp for pre-trimming. */
  endTime?: number;
}

// ---------------------------------------------------------------------------
// TASK / PROCESSING
// ---------------------------------------------------------------------------

/** Backend task lifecycle states (mirrors FastAPI's status enum). */
export type TaskStatus =
  | "pending"
  | "downloading"
  | "extracting_audio"
  | "transcribing"
  | "analyzing"
  | "rendering"
  | "uploading"
  | "completed"
  | "failed";

/** A processing pipeline step shown in the UI during generation. */
export interface PipelineStep {
  id: string;
  label: string;
  /** Maps to a TaskStatus; the step is "active" when the task is at this status. */
  status: TaskStatus;
}

/** The full task object returned by GET /api/tasks/{task_id}. */
export interface Task {
  id: string;
  status: TaskStatus;
  /** Overall progress percentage (0-100). */
  progress: number;
  /** Human-readable description of the current step. */
  currentStep: string;
  videoTitle: string;
  originalUrl?: string;
  createdAt: string;
  completedAt?: string;
  clips?: GeneratedClip[];
  error?: string;
}

// ---------------------------------------------------------------------------
// RESULTS
// ---------------------------------------------------------------------------

/** A single generated Short clip ready for preview and download. */
export interface GeneratedClip {
  id: string;
  /** Sequential number: "Short #1", "Short #2", etc. */
  index: number;
  /** Compelling hook/title generated for the short */
  title?: string;
  /** Duration of the clip in seconds. */
  duration: number;
  /** Active subtitle / caption style used (e.g., 'Karaoke Glow', 'Hormozi Pop') */
  captionStyle?: string;
  /** Pre-signed Cloudflare R2 URL for HLS/MP4 streaming preview. */
  previewUrl: string;
  /** Pre-signed Cloudflare R2 download URL (direct MP4). */
  downloadUrl: string;
  /** Thumbnail image URL (first frame). */
  thumbnailUrl: string;
  /** Score from Gemini (0-1) indicating viral potential. */
  viralScore: number;
  /** Timestamp in seconds where the clip starts in the original video. */
  startTime: number;
  /** Timestamp in seconds where the clip ends in the original video. */
  endTime: number;
}

// ---------------------------------------------------------------------------
// API CONTRACTS (mirroring backend Pydantic schemas)
// ---------------------------------------------------------------------------

/** POST /api/upload/presigned → response body. */
export interface PresignedUrlResponse {
  uploadUrl: string;
  objectKey: string;
}

/** POST /api/tasks → request body. */
export interface CreateTaskRequest {
  sourceType: "upload" | "url";
  sourceKey: string; // R2 object key or raw URL
}

/** POST /api/tasks → response body. */
export interface CreateTaskResponse {
  taskId: string;
  status: TaskStatus;
}

/** GET /api/tasks/{task_id} → response body. */
export type TaskStatusResponse = Task;

// ---------------------------------------------------------------------------
// TRANSCRIPTION SCHEMA — Word-level timestamps & segments
// ---------------------------------------------------------------------------

/** Word-level timestamp with start, end, and confidence score. */
export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
  probability: number;
}

/** Segment-level transcription with index, timestamps, and child words. */
export interface TranscriptSegment {
  id: number;
  text: string;
  start: number;
  end: number;
  words: WordTimestamp[];
}

/** The clean internal transcript schema returned by the backend speech-to-text. */
export interface TranscriptSchema {
  text: string;
  language: string;
  languageProbability: number;
  segments: TranscriptSegment[];
  words: WordTimestamp[];
}

/** Normalized transcription schema containing both raw and clean versions. */
export interface NormalizedTranscriptSchema {
  original: TranscriptSchema;
  normalized: TranscriptSchema;
}

// ---------------------------------------------------------------------------
// VIDEO PREVIEW & CAPTION STYLING TYPES
// ---------------------------------------------------------------------------

export interface AspectRatioPreset {
  width: number;
  height: number;
  label: string;
  cssRatio: string;
}

export interface CaptionSettings {
  font: string;
  fontSize: number;
  fontWeight: string;
  textColor: string;
  outlineColor: string;
  outlineWidth: number;
  shadowColor: string;
  shadowBlur: number;
  highlightColor: string;
  highlightScale: number;
  karaokeActive: boolean;
  alignment: "left" | "center" | "right";
  verticalPosition: number;
  backgroundColor?: string;
  backgroundPadding?: string;
  backgroundRadius?: string;
  animationType: string;
}

export interface CaptionStyle {
  name: string;
  fontFamily: string;
  fontWeight: string;
  color: string;
  highlightColor: string;
  outlineColor: string;
  shadowColor?: string;
  backgroundColor?: string;
  scaleOnActive?: boolean;
}

export interface VideoPreviewProps {
  videoUrl: string;
  aspectRatio: "9:16" | "4:5" | "3:4" | "1:1" | "2:3";
  width?: number;
  height?: number;
  captions?: TranscriptSegment[];
  captionSettings: CaptionSettings;
}
