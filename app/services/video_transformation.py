"""
app/services/video_transformation.py
-----------------------------------
FFmpeg-based video transformation pipeline.
Converts arbitrary landscape or portrait videos into vertical presets or configurable aspect ratios.
Supports center-cropping and letterboxing/pillarboxing padding options.
De-couples coordinates calculations using a pluggable ReframingProvider architecture for future AI auto-reframing.
"""

from __future__ import annotations

import os
import logging
import asyncio
import tempfile
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.clip_generation import FFmpegEncodingConfig

logger = logging.getLogger(__name__)


class VideoTransformationError(Exception):
    """Raised when video transformation pipeline fails."""
    pass


# ---------------------------------------------------------------------------
# Presets Definitions
# ---------------------------------------------------------------------------

class VideoPreset(BaseModel):
    """A configuration preset for target video output specifications."""
    name: str = Field(..., description="Name of the preset.")
    aspect_ratio: float = Field(..., description="Target aspect ratio (width / height).")
    width: int = Field(..., description="Target width in pixels.")
    height: int = Field(..., description="Target height in pixels.")


SHORTS_9_16 = VideoPreset(name="SHORTS_9_16", aspect_ratio=9.0/16.0, width=1080, height=1920)
INSTAGRAM_4_5 = VideoPreset(name="INSTAGRAM_4_5", aspect_ratio=4.0/5.0, width=1080, height=1350)
PORTRAIT_3_4 = VideoPreset(name="PORTRAIT_3_4", aspect_ratio=3.0/4.0, width=1080, height=1440)
SQUARE_1_1 = VideoPreset(name="SQUARE_1_1", aspect_ratio=1.0/1.0, width=1080, height=1080)
PORTRAIT_2_3 = VideoPreset(name="PORTRAIT_2_3", aspect_ratio=2.0/3.0, width=1080, height=1620)

PRESETS = {
    "9:16": SHORTS_9_16,
    "4:5": INSTAGRAM_4_5,
    "3:4": PORTRAIT_3_4,
    "1:1": SQUARE_1_1,
    "2:3": PORTRAIT_2_3
}


# ---------------------------------------------------------------------------
# Pluggable Reframing Strategy Architecture (AI-Ready)
# ---------------------------------------------------------------------------

class ReframingProvider(ABC):
    """
    Abstract Base Class for reframing coordinates calculations.
    Subclasses can implement different algorithms (e.g. Center-crop, AI Face detection tracking).
    """

    @abstractmethod
    def calculate_crop_filter(
        self,
        src_w: int,
        src_h: int,
        target_ratio: float,
        target_w: int,
        target_h: int
    ) -> str:
        """
        Generates the FFmpeg video filter expression for cropping.
        """
        pass


class CenterCropProvider(ReframingProvider):
    """
    MVP Reframing strategy. Calculates static coordinates keeping the target frame centered.
    """

    def calculate_crop_filter(
        self,
        src_w: int,
        src_h: int,
        target_ratio: float,
        target_w: int,
        target_h: int
    ) -> str:
        src_aspect = float(src_w) / float(src_h)

        if src_aspect > target_ratio:
            # Source is wider than target aspect (e.g. landscape 16:9 to vertical 9:16)
            # Crop width, keep height. Center x.
            crop_w = int(round(src_h * target_ratio))
            crop_h = src_h
            x = int(round((src_w - crop_w) / 2))
            y = 0
        else:
            # Source is taller than target aspect (e.g. 1:1 square to 9:16 vertical)
            # Crop height, keep width. Center y.
            crop_w = src_w
            crop_h = int(round(src_w / target_ratio))
            x = 0
            y = int(round((src_h - crop_h) / 2))

        logger.debug(
            "Center Crop: source=%dx%d, target_ratio=%.3f, crop_box=%dx%d at (%d,%d)",
            src_w, src_h, target_ratio, crop_w, crop_h, x, y
        )

        return f"crop={crop_w}:{crop_h}:{x}:{y},scale={target_w}:{target_h}"


# ---------------------------------------------------------------------------
# Core Transformation Service
# ---------------------------------------------------------------------------

class VideoTransformationService:
    """
    Manages metadata queries and runs FFmpeg transformation pipelines.
    """

    @classmethod
    async def get_video_dimensions(cls, video_path: str) -> Tuple[int, int]:
        """
        Extracts width and height of the video track using ffprobe.
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            video_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
        except FileNotFoundError as exc:
            raise VideoTransformationError(
                "ffprobe executable not found. Ensure FFmpeg is installed and added to the PATH."
            ) from exc
        except Exception as exc:
            raise VideoTransformationError(f"Failed to run ffprobe: {exc}") from exc

        if process.returncode != 0:
            raise VideoTransformationError(
                f"ffprobe failed with exit code {process.returncode}. Error: {stderr.decode(errors='replace')}"
            )

        output_str = stdout.decode().strip()
        if not output_str:
            raise VideoTransformationError("ffprobe returned empty dimensions output.")

        try:
            parts = output_str.split(",")
            width = int(parts[0].strip())
            height = int(parts[1].strip())
            return width, height
        except Exception as exc:
            raise VideoTransformationError(
                f"Failed to parse video dimensions from ffprobe output '{output_str}': {exc}"
            ) from exc

    @classmethod
    def determine_optimal_mode(cls, src_w: int, src_h: int, target_ratio: float) -> str:
        """
        Decides whether to crop or pad based on aspect mismatch, avoiding unnecessary cropping
        when letterboxing/pillarboxing is more appropriate (e.g. source 1080x1080 to 9:16).
        """
        src_ratio = float(src_w) / float(src_h)
        
        # 1. Close enough to target aspect ratio -> crop directly (negligible loss)
        if abs(src_ratio - target_ratio) <= 0.05:
            return "crop"

        # 2. Square source (src_ratio == 1.0) and vertical target (e.g. 9:16 target_ratio ~0.562)
        # Cropping 9:16 out of a square removes 44% of vertical context, so padding is better.
        if abs(src_ratio - 1.0) <= 0.02 and target_ratio < 0.8:
            return "pad"

        # 3. Otherwise, use cropping to fill standard vertical dimensions (user focus)
        return "crop"

    @classmethod
    def generate_ffmpeg_filters(
        cls,
        src_w: int,
        src_h: int,
        target_ratio: float,
        target_w: int,
        target_h: int,
        mode: str = "crop",
        fps: Optional[float] = None,
        reframing_provider: ReframingProvider = CenterCropProvider()
    ) -> str:
        """
        Generates FFmpeg filter chain strings combining crop/pad logic with optional FPS filters.
        """
        filters = []

        if mode == "auto":
            mode = cls.determine_optimal_mode(src_w, src_h, target_ratio)
            logger.info("Auto crop_mode selected transformation strategy: %s", mode)

        if mode == "crop":
            crop_filter = reframing_provider.calculate_crop_filter(
                src_w=src_w,
                src_h=src_h,
                target_ratio=target_ratio,
                target_w=target_w,
                target_h=target_h
            )
            filters.append(crop_filter)
        elif mode == "pad":
            # Scale to fit inside target area, then pad with black background
            pad_filter = (
                f"scale=w='if(gte(iw/ih,{target_ratio:.4f}),{target_w},-1)':"
                f"h='if(gte(iw/ih,{target_ratio:.4f}),-1,{target_h})',"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"
            )
            filters.append(pad_filter)
        else:
            raise ValueError(f"Unsupported transformation mode: {mode}. Use 'crop', 'pad', or 'auto'.")

        # Frame rate configuration (preserves input fps unless explicit)
        if fps is not None:
            filters.append(f"fps=fps={fps}")

        return ",".join(filters)

    @classmethod
    async def transform_video(
        cls,
        source_path: str,
        target_preset: VideoPreset,
        output_dir: Optional[str] = None,
        crop_mode: str = "auto",
        fps: Optional[float] = None,
        reframing_provider: ReframingProvider = CenterCropProvider(),
        config: FFmpegEncodingConfig = FFmpegEncodingConfig(),
        subtitles_path: Optional[str] = None,
        start_time: Optional[float] = None,
        duration: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> str:
        """
        Converts input video according to the provided preset specifications, with optional subtitle burn-in.
        Supports single-pass seeking and trimming when start_time and duration/end_time are provided.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found at: {source_path}")

        # Calculate duration if end_time given
        if duration is None and end_time is not None and start_time is not None:
            duration = max(0.1, end_time - start_time)

        # 1. Inspect dimensions
        width, height = await cls.get_video_dimensions(source_path)

        # 2. Compile FFmpeg filters
        filter_chain = cls.generate_ffmpeg_filters(
            src_w=width,
            src_h=height,
            target_ratio=target_preset.aspect_ratio,
            target_w=target_preset.width,
            target_h=target_preset.height,
            mode=crop_mode,
            fps=fps,
            reframing_provider=reframing_provider
        )

        if subtitles_path:
            escaped_path = subtitles_path.replace("\\", "/").replace(":", r"\:")
            filter_chain += f",subtitles=filename='{escaped_path}'"

        # 3. Setup temporary file
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        temp_fd, temp_path = tempfile.mkstemp(suffix=".mp4", dir=output_dir)
        os.close(temp_fd)

        # 4. Transcode using libx264/aac (ensuring frame rate & audio sync)
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-threads", str(settings.FFMPEG_MAX_THREADS),
        ]

        # Fast seeking before input if trimming is requested
        if start_time is not None and start_time >= 0:
            cmd.extend(["-ss", f"{start_time:.3f}"])

        cmd.extend(["-i", source_path])

        if duration is not None and duration > 0:
            cmd.extend(["-t", f"{duration:.3f}"])

        cmd.extend([
            "-vf", filter_chain,
            "-c:v", "libx264",
            "-crf", str(config.crf),
            "-preset", config.preset,
            "-profile:v", config.video_profile,
            "-level:v", config.video_level,
            "-g", str(config.keyframe_interval),
            "-c:a", "aac",
            "-b:a", config.audio_bitrate,
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ])

        if config.max_rate and config.buf_size:
            cmd.extend(["-maxrate", config.max_rate, "-bufsize", config.buf_size])

        cmd.append(temp_path)

        logger.info(
            "Running preset transform '%s': target=%dx%d, command=%s",
            target_preset.name, target_preset.width, target_preset.height, " ".join(cmd)
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.FFMPEG_PROCESS_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError as exc:
            try:
                process.kill()
            except Exception:
                pass
            cls.cleanup_file(temp_path)
            logger.error("FFmpeg transformation timed out after %ds: %s", settings.FFMPEG_PROCESS_TIMEOUT_SECONDS, source_path)
            raise VideoTransformationError(f"Video transformation timed out after {settings.FFMPEG_PROCESS_TIMEOUT_SECONDS}s.") from exc
        except Exception as exc:
            cls.cleanup_file(temp_path)
            raise VideoTransformationError(f"Failed to start FFmpeg transformation: {exc}") from exc

        if process.returncode != 0:
            cls.cleanup_file(temp_path)
            err_output = stderr.decode(errors="replace")
            logger.error("FFmpeg transformation failed: %s", err_output)
            raise VideoTransformationError(
                f"FFmpeg preset conversion failed (code {process.returncode}). Output: {err_output[-500:]}"
            )

        return temp_path

    @staticmethod
    def cleanup_file(path: str) -> None:
        """Removes a file from disk safely."""
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as exc:
            logger.warning("Failed to clean up file %s: %s", path, exc)


# ---------------------------------------------------------------------------
# Reusable Aspect-Ratio Conversion Module Utility
# ---------------------------------------------------------------------------

async def convert_to_aspect_ratio(
    input_path: str,
    output_path: str,
    target_ratio: float,
    target_width: int,
    target_height: int,
    crop_mode: str = "center",
    fps: Optional[float] = None,
    reframing_provider: ReframingProvider = CenterCropProvider(),
    config: FFmpegEncodingConfig = FFmpegEncodingConfig(),
    subtitles_path: Optional[str] = None
) -> str:
    """
    Module level utility wrapper to convert a video to any target aspect ratio.

    Parameters
    ----------
    input_path : str
        Source video path.
    output_path : str
        Target output video path on disk.
    target_ratio : float
        Target aspect ratio (width / height).
    target_width : int
        Output width limit.
    target_height : int
        Output height limit.
    crop_mode : str, optional
        Modes: 'center' (map to crop), 'crop', 'pad', 'auto'. Defaults to 'center'.
    fps : Optional[float], optional
        Configurable frame rate limit. Defaults to input frame rate.
    reframing_provider : ReframingProvider, optional
        Coordinate generation strategy. Defaults to CenterCropProvider.

    Returns
    -------
    str
        The output path on success.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found at: {input_path}")

    # Map center crop parameter
    mode = "crop" if crop_mode == "center" else crop_mode

    # Fetch dimensions
    width, height = await VideoTransformationService.get_video_dimensions(input_path)

    # Compile filters
    filter_chain = VideoTransformationService.generate_ffmpeg_filters(
        src_w=width,
        src_h=height,
        target_ratio=target_ratio,
        target_w=target_width,
        target_h=target_height,
        mode=mode,
        fps=fps,
        reframing_provider=reframing_provider
    )

    if subtitles_path:
        escaped_path = subtitles_path.replace("\\", "/").replace(":", "\\:")
        filter_chain += f",subtitles='{escaped_path}'"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf", filter_chain,
        "-c:v", "libx264",
        "-crf", str(config.crf),
        "-preset", config.preset,
        "-profile:v", config.video_profile,
        "-level:v", config.video_level,
        "-g", str(config.keyframe_interval),
        "-c:a", "aac",
        "-b:a", config.audio_bitrate,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]

    if config.max_rate and config.buf_size:
        cmd.extend(["-maxrate", config.max_rate, "-bufsize", config.buf_size])

    cmd.append(output_path)

    logger.info("Executing aspect ratio conversion utility to %s", output_path)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
    except Exception as exc:
        raise VideoTransformationError(f"Failed to execute aspect ratio conversion: {exc}") from exc

    if process.returncode != 0:
        err_out = stderr.decode(errors="replace")
        raise VideoTransformationError(
            f"Aspect ratio utility failed (code {process.returncode}). Output: {err_out[-500:]}"
        )

    return output_path
