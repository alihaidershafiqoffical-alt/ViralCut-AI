"""
app/tasks.py
------------
Celery background rendering tasks for video processing.
Executes trimming, aspect ratio vertical crops, karaoke subtitle burn-ins, and encodes output clips.
Updates job progress state in Redis.
"""

from __future__ import annotations

import os
import logging
import asyncio
from typing import Dict, List, Any

from app.core.config import settings
from app.core.celery_app import celery_app
from app.services.job_manager import JobManagerService, JobStatus
from app.services.clip_generation import ClipGenerationService, FFmpegEncodingConfig
from app.services.video_transformation import VideoTransformationService, PRESETS
from app.services.transcription import WordSegment, TranscriptionService
from app.services.captions import CaptionGeneratorService
from app.services.caption_styling import CaptionStyle
from app.services.caption_rendering import CaptionRenderingService

# Video processing pipeline imports
from app.services.url_downloader import SecureDownloader
from app.services.providers import registry
from app.services.url_validation import UrlValidationService
from app.services.video_metadata import VideoMetadataService
from app.services.video_validation import VideoValidationService
from app.services.audio_extraction import AudioExtractionService
from app.services.transcript_normalization import TranscriptNormalizationService
from app.services.video_analysis import VideoAnalysisService
from app.services.feasibility import ShortsFeasibilityService
from app.services.ranking import ShortsRankingService
from app.services.cleanup import CleanupService
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


# Helper to run async functions in Celery synchronous workers
def run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.render_video_task", bind=True)
def render_video_task(
    self,
    job_id: str,
    video_path: str,
    start_time: float,
    end_time: float,
    aspect_ratio: str,
    caption_style_name: str,
    caption_settings: Dict[str, Any],
    words_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Asynchronous Celery task that processes video trimming, cropping, subtitle rendering,
    and burns the final Short output in a background worker.
    """
    logger.info("Starting background rendering task [job=%s, task_id=%s]", job_id, self.request.id)
    JobManagerService.update_progress(job_id, 10, "Trimming video clip bounds...", JobStatus.PROCESSING)

    temp_files = []
    try:
        # 1. Parameter Validation
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Source video not found: {video_path}")

        # 2. Trim Clip using ClipGenerationService
        output_dir = os.path.dirname(video_path)
        
        JobManagerService.update_progress(job_id, 25, "Cutting video segment...", JobStatus.PROCESSING)
        
        # Async cut
        trimmed_path = run_async(
            ClipGenerationService.cut_clip(
                input_path=video_path,
                start_time=start_time,
                end_time=end_time,
                output_dir=output_dir
            )
        )
        temp_files.append(trimmed_path)

        # 3. Generate Timed Captions Subtitle file
        JobManagerService.update_progress(job_id, 50, "Generating timed subtitle overlay files...", JobStatus.PROCESSING)
        
        # Filter raw words belonging to this segment and shift timestamps relative to clip start
        shifted_words = []
        for wd in words_data:
            w_start = wd["start"]
            w_end = wd["end"]
            if w_start >= start_time and w_end <= end_time:
                # Shift start and end times to match trimmed clip timeline (starting at 0)
                shifted_words.append(
                    WordSegment(
                        word=wd["word"],
                        start=max(0.0, w_start - start_time),
                        end=max(0.0, w_end - start_time),
                        probability=wd.get("probability", 0.99)
                    )
                )

        # Build visual CaptionGroup objects
        caption_groups = CaptionGeneratorService.generate_captions(
            words=shifted_words,
            max_words=6,
            max_duration=2.5,
            max_gap=1.0
        )

        # Construct CaptionStyle config from incoming settings overrides
        custom_style = CaptionStyle(
            name=caption_style_name,
            font_family=caption_settings.get("font", "Outfit"),
            font_size=caption_settings.get("fontSize", 42),
            font_weight=caption_settings.get("fontWeight", "bold"),
            font_color=caption_settings.get("textColor", "#FFFFFF"),
            position_y_pct=caption_settings.get("verticalPosition", 78),
            stroke_color=caption_settings.get("outlineColor", "#000000"),
            stroke_width=caption_settings.get("outlineWidth", 1.5),
            shadow_color=caption_settings.get("shadowColor", "rgba(0,0,0,0.5)"),
            shadow_blur=caption_settings.get("shadowBlur", 1.0),
            highlight_color=caption_settings.get("highlightColor", "#00FF00"),
            highlight_scale=caption_settings.get("highlightScale", 1.15),
            animation_type=caption_settings.get("animationType", "pop")
        )

        # Save ASS file
        ass_path = os.path.join(output_dir, f"{job_id}_subtitles.ass")
        CaptionRenderingService.save_ass_file(caption_groups, custom_style, ass_path)
        temp_files.append(ass_path)

        # 4. Apply Aspect Preset Reframing and Subtitle Burning
        JobManagerService.update_progress(job_id, 75, "Applying aspect ratio crop and burning subtitles...", JobStatus.PROCESSING)
        
        target_preset = PRESETS.get(aspect_ratio)
        if not target_preset:
            raise ValueError(f"Unsupported aspect ratio preset: {aspect_ratio}")

        # Async transform with subtitles path attached
        final_video_path = run_async(
            VideoTransformationService.transform_video(
                source_path=trimmed_path,
                target_preset=target_preset,
                output_dir=output_dir,
                crop_mode="auto",
                subtitles_path=ass_path,
                config=FFmpegEncodingConfig()
            )
        )

        logger.info("Rendering complete. Output stored at: %s", final_video_path)
        
        # Output URL / path registration (simulating local relative path or cloud storage download link)
        output_url = f"/clips/{os.path.basename(final_video_path)}"
        
        JobManagerService.mark_complete(job_id, [output_url])
        return {"status": "completed", "output_urls": [output_url]}

    except Exception as exc:
        logger.exception("Error during background rendering task execution: %s", exc)
        CleanupService.cleanup_failed_job(job_id)
        JobManagerService.mark_failed(job_id, str(exc))
        return {"status": "failed", "error": str(exc)}

    finally:
        # Clean up temporary intermediate files (trimmed path, subtitle ASS files)
        # Keep the final transformed video intact
        for tf in temp_files:
            try:
                if os.path.exists(tf):
                    os.remove(tf)
                    logger.debug("Cleaned up temp task file: %s", tf)
            except OSError as cleanup_err:
                logger.warning("Failed to clean up temp file %s: %s", tf, cleanup_err)


import time

class PipelineProfiler:
    """Profiles execution latency across all 9 video pipeline stages."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.start_time = time.time()
        self.timings: Dict[str, float] = {}
        self._stage_start = time.time()
        self._current_stage = "Initialization"

    def mark_stage(self, stage_name: str):
        now = time.time()
        if self._current_stage:
            elapsed = round(now - self._stage_start, 2)
            self.timings[self._current_stage] = elapsed
            logger.info("[Profiler | job=%s] Stage '%s' finished in %.2fs", self.job_id, self._current_stage, elapsed)
        self._current_stage = stage_name
        self._stage_start = now

    def finish(self) -> Dict[str, float]:
        self.mark_stage("Finalizing")
        total = round(time.time() - self.start_time, 2)
        self.timings["Total Pipeline Time"] = total
        logger.info(
            "[Profiler | job=%s] Complete Pipeline Summary: %s (Total: %.2fs)",
            self.job_id,
            ", ".join(f"{k}: {v}s" for k, v in self.timings.items()),
            total
        )
        return self.timings


def execute_video_pipeline(
    job_id: str,
    video_source: str,
    is_url: bool,
    target_count: int = 3,
    clip_duration: float = 30.0,
    aspect_ratio: str = "9:16",
    topic: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    High-Performance video processing pipeline executing all 9 stages:
    1. Uploading / Ingestion
    2. Analyzing video metadata
    3. Fast speech audio extraction (16kHz mono, optionally range pre-trimmed)
    4. Fast Whisper STT (greedy beam_size=1, VAD-filtered)
    5. AI moments detection & ranking
    6. Candidate selection & timestamp refinement
    7. Single-pass 9:16 vertical cutting & rendering
    8. High-contrast static subtitle burning
    9. Finalizing & stage metrics recording
    """
    # Clamp target count to maximum of 4
    target_count = min(4, max(1, target_count))

    profiler = PipelineProfiler(job_id)
    logger.info("Starting optimized video pipeline task [job=%s, aspect_ratio=%s, topic=%s, start_time=%s, end_time=%s]", job_id, aspect_ratio, topic, start_time, end_time)
    JobManagerService.update_progress(job_id, 5, "Initializing processing pipeline...", JobStatus.PROCESSING, stage="Uploading")

    temp_files = []
    video_path = None
    try:
        # ── Stage 1: Uploading / Ingestion ──────────────────────────────────
        profiler.mark_stage("Uploading")
        JobManagerService.update_progress(job_id, 10, "Retrieving video file...", JobStatus.PROCESSING, stage="Uploading")
        if is_url:
            clean_url = UrlValidationService.validate(video_source)
            resolved = run_async(registry.resolve(clean_url))
            download_result = run_async(
                SecureDownloader.download(
                    url=resolved.download_url,
                    job_id=job_id,
                    extension=resolved.suggested_extension,
                    content_type_hint=resolved.content_type_hint
                )
            )
            video_path = download_result["file_path"]
            temp_files.append(video_path)
        else:
            video_dir = StorageService.get_job_dir(video_source)
            if not os.path.exists(video_dir):
                raise FileNotFoundError(f"Uploaded video file '{video_source}' not found.")
            candidates = [
                os.path.join(video_dir, f)
                for f in os.listdir(video_dir)
                if os.path.isfile(os.path.join(video_dir, f)) and not f.endswith(".wav") and not f.endswith(".aac")
            ]
            if not candidates:
                raise FileNotFoundError(f"Uploaded video file '{video_source}' not found.")
            video_path = candidates[0]

        # ── Stage 2: Analyzing video ────────────────────────────────────────
        profiler.mark_stage("Analyzing video")
        JobManagerService.update_progress(job_id, 20, "Analyzing video format and codec metadata...", JobStatus.PROCESSING, stage="Analyzing video")
        metadata = VideoMetadataService.extract_metadata(video_path)
        VideoValidationService.validate_strict(metadata)

        # Calculate analysis duration boundaries
        analysis_duration = metadata.duration_seconds
        if start_time is not None and end_time is not None:
            analysis_duration = max(1.0, end_time - start_time)

        # ── Stage 3: Extracting audio ───────────────────────────────────────
        profiler.mark_stage("Extracting audio")
        JobManagerService.update_progress(job_id, 30, "Extracting audio track for speech recognition...", JobStatus.PROCESSING, stage="Extracting audio")
        audio_path = AudioExtractionService.extract_audio(
            video_path,
            start_time=start_time,
            end_time=end_time
        )
        temp_files.append(audio_path)

        # ── Stage 4: Transcribing ───────────────────────────────────────────
        profiler.mark_stage("Transcribing")
        JobManagerService.update_progress(job_id, 45, "Running speech-to-text transcription...", JobStatus.PROCESSING, stage="Transcribing")
        trans_res = TranscriptionService.transcribe(audio_path, word_timestamps=True, beam_size=1)
        norm_res = TranscriptNormalizationService.normalize(trans_res)

        # ── Stage 5: AI analysis ────────────────────────────────────────────
        profiler.mark_stage("AI analysis")
        JobManagerService.update_progress(job_id, 60, "Identifying viral moments...", JobStatus.PROCESSING, stage="AI analysis")
        analysis_res = run_async(
            VideoAnalysisService.analyze_video(
                transcript=norm_res.normalized,
                video_duration=analysis_duration,
                target_count=target_count,
                clip_duration=clip_duration,
                topic_focus=topic
            )
        )

        # AI Judge pass
        JobManagerService.update_progress(job_id, 70, "Evaluating hook strength...", JobStatus.PROCESSING, stage="AI Judge")
        from app.services.ai_judge import AIJudgeService
        judged_candidates = run_async(
            AIJudgeService.evaluate_candidates(analysis_res.shorts)
        )

        # ── Stage 6: Selecting clips ────────────────────────────────────────
        profiler.mark_stage("Selecting clips")
        JobManagerService.update_progress(job_id, 75, "Ranking and selecting top moments...", JobStatus.PROCESSING, stage="Selecting clips")
        
        from app.services.ranking import ShortsRankingService
        ranked_all = ShortsRankingService.rank_candidates(candidates=judged_candidates)

        from app.services.diversity_selector import DiversitySelectorService
        ranked_moments = run_async(
            DiversitySelectorService.select_diverse_shorts(
                candidates=ranked_all,
                requested_count=target_count,
                video_duration=analysis_duration
            )
        )
        
        from app.services.timestamp_refinement import TimestampRefinementService
        ranked_moments = TimestampRefinementService.refine_timestamps(
            candidates=ranked_moments,
            transcription_result=trans_res,
            video_duration=analysis_duration,
            buffer_seconds=0.1
        )

        # ── Stage 7 & 8: Single-Pass 9:16 Shorts Generation & Subtitles ───────
        profiler.mark_stage("Generating Shorts")
        JobManagerService.update_progress(job_id, 85, "Generating vertical Shorts with subtitles...", JobStatus.PROCESSING, stage="Generating Shorts")
        
        target_preset = PRESETS.get(aspect_ratio, PRESETS["9:16"])
        final_clips = []
        for idx, moment in enumerate(ranked_moments):
            step_pct = 85 + int((idx / max(1, len(ranked_moments))) * 10)
            JobManagerService.update_progress(
                job_id,
                step_pct,
                f"Rendering Short {idx + 1}/{len(ranked_moments)}: {moment.title}...",
                JobStatus.PROCESSING,
                stage="Generating Shorts"
            )

            # Generate subtitles ASS file for this moment (relative to output segment 0.0)
            moment_shifted_words = []
            for w in norm_res.normalized.words:
                if w.start >= moment.start and w.end <= moment.end:
                    moment_shifted_words.append(
                        WordSegment(
                            word=w.word,
                            start=max(0.0, w.start - moment.start),
                            end=max(0.0, w.end - moment.start),
                            probability=w.probability
                        )
                    )

            caption_groups = CaptionGeneratorService.generate_captions(
                words=moment_shifted_words,
                max_words=5,
                max_duration=2.0,
                max_gap=0.8
            )

            # High-contrast, clean static subtitle style for ultra-fast MVP rendering
            static_style = CaptionStyle(
                name="Static_Clean",
                font_family="Outfit",
                font_size=38,
                font_weight="bold",
                font_color="#FFFFFF",
                position_y_pct=76,
                stroke_color="#000000",
                stroke_width=2.0,
                shadow_color="rgba(0,0,0,0.7)",
                shadow_blur=1.5,
                animation_type="none"
            )

            ass_moment_path = StorageService.get_file_path(job_id, f"{job_id}_moment_{idx}.ass")
            CaptionRenderingService.save_ass_file(caption_groups, static_style, ass_moment_path)
            temp_files.append(ass_moment_path)

            # Align timestamps to original video bounds
            ss_offset = start_time or 0.0
            ss_start = moment.start + ss_offset
            ss_end = moment.end + ss_offset

            # SINGLE-PASS FAST RENDER: Trim + 9:16 Crop + Scale + Subtitle Burn in 1 FFmpeg process
            final_short_path = run_async(
                VideoTransformationService.transform_video(
                    source_path=video_path,
                    start_time=ss_start,
                    end_time=ss_end,
                    target_preset=target_preset,
                    output_dir=StorageService.get_job_dir(job_id),
                    crop_mode="auto",
                    subtitles_path=ass_moment_path,
                    config=FFmpegEncodingConfig(preset="veryfast", crf=23)
                )
            )

            final_clips.append({
                "index": idx + 1,
                "title": moment.title,
                "hook": moment.hook,
                "summary": moment.summary,
                "score": moment.score,
                "start": ss_start,
                "end": ss_end,
                "videoUrl": f"/clips/{os.path.basename(final_short_path)}",
                "words": [w.model_dump() for w in moment_shifted_words]
            })

            # Progressively store intermediate completed Shorts
            JobManagerService.update_progress(
                job_id=job_id,
                progress=step_pct,
                step_label=f"Generated Short {idx + 1}/{len(ranked_moments)}.",
                status=JobStatus.PROCESSING,
                clips=final_clips,
                stage="Generating Shorts"
            )

        # ── Stage 9: Finalizing ─────────────────────────────────────────────
        stage_timings = profiler.finish()
        JobManagerService.update_progress(job_id, 98, "Finalizing Shorts package...", JobStatus.PROCESSING, stage="Finalizing")
        JobManagerService.mark_complete(job_id, final_clips)
        logger.info("Pipeline completed successfully [job=%s, clips=%d, timings=%s]", job_id, len(final_clips), stage_timings)
        return {"status": "completed", "clips": final_clips, "timings": stage_timings}

    except Exception as exc:
        logger.exception("Error executing video processing pipeline task [job=%s]: %s", job_id, exc)
        CleanupService.cleanup_failed_job(job_id)
        friendly_error = "Video processing failed. Please verify that the file contains clear audible speech, is not corrupted, and complies with duration constraints."
        JobManagerService.mark_failed(job_id, friendly_error)
        return {"status": "failed", "error": friendly_error}

    finally:
        # Secure clean up of intermediate temporary files (audio extraction, ASS files)
        for tf in temp_files:
            try:
                if os.path.exists(tf):
                    os.remove(tf)
                    logger.debug("Cleaned up intermediate pipeline file: %s", tf)
            except OSError as cleanup_err:
                logger.warning("Failed to clean up pipeline file %s: %s", tf, cleanup_err)


@celery_app.task(name="app.tasks.process_video_pipeline_task", bind=True)
def process_video_pipeline_task(
    self,
    job_id: str,
    video_source: str,
    is_url: bool,
    target_count: int = 3,
    clip_duration: float = 30.0,
    aspect_ratio: str = "9:16",
    topic: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None
) -> Dict[str, Any]:
    return execute_video_pipeline(
        job_id=job_id,
        video_source=video_source,
        is_url=is_url,
        target_count=target_count,
        clip_duration=clip_duration,
        aspect_ratio=aspect_ratio,
        topic=topic,
        start_time=start_time,
        end_time=end_time
    )


# ─────────────────────────────────────────────────────────────────────────────
# Celery Periodic / Dedicated Cleanup Tasks
# ─────────────────────────────────────────────────────────────────────────────

@celery_app.task(name="app.tasks.cleanup_expired_worker_task")
def cleanup_expired_worker_task(max_age_seconds: int = None) -> Dict[str, Any]:
    """
    Periodic worker task that sweeps and deletes all temporary video files,
    extracted audio, intermediate cuts, subtitles, and final clips past retention.
    """
    if max_age_seconds is None:
        max_age_seconds = settings.TEMP_FILE_RETENTION_HOURS * 3600
    logger.info("Executing periodic cleanup worker task (retention=%ds)", max_age_seconds)
    result = CleanupService.cleanup_expired_jobs(max_age_seconds=max_age_seconds)
    orphaned_cleaned = CleanupService.sweep_orphaned_intermediate_files(max_age_seconds=3600)
    result["orphaned_intermediate_deleted"] = orphaned_cleaned
    logger.info("Periodic cleanup completed: %s", result)
    return result


@celery_app.task(name="app.tasks.cleanup_job_task")
def cleanup_job_task(job_id: str, delete_final_clips: bool = True) -> Dict[str, Any]:
    """
    Worker task to clean up a specific job's files on demand (e.g. on expiration or deletion).
    """
    logger.info("Executing worker cleanup for job %s (delete_final=%s)", job_id, delete_final_clips)
    return CleanupService.cleanup_job_files(job_id=job_id, delete_final_clips=delete_final_clips)


