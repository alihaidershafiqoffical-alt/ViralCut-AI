"""
app/services/clip_generation.py
-------------------------------
FFmpeg-based clip generation service.
Accurately cuts video segments using frame-accurate seeks, re-encoding to
H.264 video and AAC audio in an MP4 container, with temporary file management.
"""

from __future__ import annotations

import os
import logging
import asyncio
import tempfile
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ClipGenerationError(Exception):
    """Raised when clip generation fails."""
    pass


class FFmpegEncodingConfig(BaseModel):
    """Configuration options for high-quality, mobile-friendly social media encoding."""
    crf: int = Field(default=23, ge=0, le=51, description="Constant Rate Factor (lower is higher quality, standard 18-28).")
    preset: str = Field(default="veryfast", description="FFmpeg speed preset: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow.")
    video_profile: str = Field(default="high", description="H.264 profile: baseline, main, high.")
    video_level: str = Field(default="4.1", description="H.264 level profile.")
    audio_bitrate: str = Field(default="128k", description="Audio bitrate constraint (e.g. 128k, 192k).")
    keyframe_interval: int = Field(default=60, description="GOP size / keyframe interval in frames.")
    max_rate: Optional[str] = Field(default="4M", description="Max video bitrate (e.g. 4M) for constrained quality.")
    buf_size: Optional[str] = Field(default="8M", description="FFmpeg buffer size (e.g. 8M) for constrained quality.")


class ClipGenerationService:
    """
    Handles cutting video files using FFmpeg.
    """

    @classmethod
    async def cut_clip(
        cls,
        source_path: Optional[str] = None,
        start_time: float = 0.0,
        end_time: float = 0.0,
        output_dir: Optional[str] = None,
        config: FFmpegEncodingConfig = FFmpegEncodingConfig(),
        input_path: Optional[str] = None
    ) -> str:
        """
        Cuts a segment from source_path using FFmpeg.

        Parameters
        ----------
        source_path : str
            Path to the source video file on disk.
        start_time : float
            Start timestamp in seconds.
        end_time : float
            End timestamp in seconds.
        output_dir : Optional[str]
            Optional directory to store the cut video in. Defaults to system temp.

        Returns
        -------
        str
            The absolute path of the generated temporary MP4 file.
        """
        src = source_path or input_path
        if not src or not os.path.exists(src):
            raise FileNotFoundError(f"Source file not found at: {src}")

        if start_time < 0:
            raise ValueError(f"Invalid start_time {start_time}: Must be >= 0")
        if end_time <= start_time:
            raise ValueError(f"Invalid bounds: end_time ({end_time}) must be strictly greater than start_time ({start_time})")

        duration = end_time - start_time

        # 1. Create a secure temporary output path
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        temp_fd, temp_path = tempfile.mkstemp(suffix=".mp4", dir=output_dir)
        os.close(temp_fd) # Close file descriptor so FFmpeg can write to it

        from app.core.config import settings

        # 2. Build FFmpeg command (fast seeking with ss before i, frame-accurate re-encoding)
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",                     # Overwrite output
            "-threads", str(settings.FFMPEG_MAX_THREADS), # Limit CPU threads to prevent system starvation
            "-ss", f"{start_time:.3f}",  # Fast seek before input
            "-i", src,
            "-t", f"{duration:.3f}",   # Duration limit
            "-c:v", "libx264",        # H.264 video codec
            "-crf", str(config.crf),   # Quality CRF
            "-preset", config.preset,  # Preset speed
            "-profile:v", config.video_profile,
            "-level:v", config.video_level,
            "-g", str(config.keyframe_interval),
            "-c:a", "aac",            # AAC audio codec
            "-b:a", config.audio_bitrate,
            "-pix_fmt", "yuv420p",     # Standard pixel format for web compatibility
            "-movflags", "+faststart", # Move index to front of MP4 for instant browser playback
        ]

        if config.max_rate and config.buf_size:
            cmd.extend(["-maxrate", config.max_rate, "-bufsize", config.buf_size])

        cmd.append(temp_path)

        logger.info(
            "Generating clip: ss=%.3f, t=%.3f, command=%s",
            start_time, duration, " ".join(cmd)
        )

        # 3. Launch FFmpeg process asynchronously with process timeout protection
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
            cls.cleanup_temp_file(temp_path)
            logger.error("FFmpeg clip cutting timed out after %ds: %s", settings.FFMPEG_PROCESS_TIMEOUT_SECONDS, source_path)
            raise ClipGenerationError(f"Video clip generation timed out after {settings.FFMPEG_PROCESS_TIMEOUT_SECONDS}s.") from exc
        except FileNotFoundError as exc:
            cls.cleanup_temp_file(temp_path)
            raise ClipGenerationError(
                "FFmpeg executable not found. Ensure FFmpeg is installed and added to the system PATH."
            ) from exc
        except Exception as exc:
            cls.cleanup_temp_file(temp_path)
            raise ClipGenerationError(f"Failed to start FFmpeg subprocess: {exc}") from exc

        # 4. Check exit code
        if process.returncode != 0:
            cls.cleanup_temp_file(temp_path)
            error_details = stderr.decode(errors="replace")
            logger.error("FFmpeg cutting failed: %s", error_details)
            raise ClipGenerationError(
                f"FFmpeg failed with exit code {process.returncode}. Output: {error_details[-500:]}"
            )

        logger.info("Successfully generated clip: %s", temp_path)
        return temp_path

    @staticmethod
    def cleanup_temp_file(path: str) -> None:
        """Safely removes a temporary file from disk."""
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info("Cleaned up temporary file: %s", path)
        except Exception as exc:
            logger.warning("Failed to clean up temporary file %s: %s", path, exc)
