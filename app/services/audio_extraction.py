"""
audio_extraction.py
-------------------
Python service to extract speech audio from a video using FFmpeg,
optimized for Faster-Whisper transcription.
"""

from __future__ import annotations

import logging
import os
import subprocess
import uuid

from app.core.config import settings
from app.services.storage import StorageService
from app.services.video_metadata import FFprobeError, VideoMetadataService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AudioExtractionError(Exception):
    """Base exception class for all audio extraction errors."""
    pass


class NoAudioStreamError(AudioExtractionError):
    """Raised when the input video file does not contain an audio stream."""
    pass


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AudioExtractionService:
    """
    Service responsible for extracting, converting, and normalizing speech audio
    from video files for subsequent AI processing (Faster-Whisper STT).
    """

    @classmethod
    def extract_audio(
        cls,
        video_path: str,
        start_time: Optional[float] = None,
        duration: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """
        Extract audio from a video file and convert it to mono, 16kHz, 16-bit PCM WAV.
        """
        # Ensure input file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Source video file not found at: {video_path}")

        # Calculate duration if end_time given
        if duration is None and end_time is not None and start_time is not None:
            duration = max(0.1, end_time - start_time)

        # ── 1. Validate stream metadata ─────────────────────────────────────
        try:
            metadata = VideoMetadataService.extract_metadata(video_path)
            if not metadata.has_audio:
                raise NoAudioStreamError(
                    "The source video contains no audio stream to extract."
                )
        except FFprobeError as exc:
            raise AudioExtractionError(
                f"Failed to analyze video metadata before audio extraction: {exc}"
            ) from exc

        # Determine job_id from video_path directory structure if possible
        parent_dir = os.path.dirname(video_path)
        parent_name = os.path.basename(parent_dir)
        if parent_name.startswith("job_"):
            job_id = parent_name[4:]
        else:
            job_id = str(uuid.uuid4())
        audio_path = StorageService.get_file_path(job_id, ".wav")

        # ── 3. Build FFmpeg command ─────────────────────────────────────────
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-threads", str(settings.FFMPEG_MAX_THREADS),
        ]

        if start_time is not None and start_time >= 0:
            cmd.extend(["-ss", f"{start_time:.3f}"])

        cmd.extend(["-i", video_path])

        if duration is not None and duration > 0:
            cmd.extend(["-t", f"{duration:.3f}"])

        cmd.extend([
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_path,
        ])

        # ── 4. Run FFmpeg command ───────────────────────────────────────────
        try:
            logger.info(
                "Extracting speech audio from '%s' to '%s' (16kHz mono PCM).",
                video_path,
                audio_path,
            )
            # Limit processing time to 180 seconds to prevent hanging indefinitely
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.returncode != 0:
                cls._cleanup_file(audio_path)
                err_details = result.stderr or result.stdout or "No error output captured."
                logger.error(
                    "FFmpeg audio extraction failed with exit code %d: %s",
                    result.returncode,
                    err_details,
                )
                raise AudioExtractionError(
                    f"FFmpeg process exited with code {result.returncode}. Details: {err_details}"
                )

            # Confirm file actually exists on success
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                cls._cleanup_file(audio_path)
                raise AudioExtractionError(
                    "FFmpeg finished successfully, but output audio file is missing or empty."
                )

            return audio_path

        except subprocess.TimeoutExpired as exc:
            cls._cleanup_file(audio_path)
            logger.error("FFmpeg audio extraction timed out for file: %s", video_path)
            raise AudioExtractionError(
                "FFmpeg audio extraction execution timed out (limit: 180s)."
            ) from exc

        except FileNotFoundError as exc:
            cls._cleanup_file(audio_path)
            logger.error("FFmpeg executable not found in system PATH.")
            raise AudioExtractionError(
                "FFmpeg is not installed or not available in the system PATH."
            ) from exc

        except Exception as exc:
            cls._cleanup_file(audio_path)
            if not isinstance(exc, AudioExtractionError):
                logger.exception("Unexpected error during audio extraction:")
                raise AudioExtractionError(
                    f"An unexpected error occurred during audio extraction: {exc}"
                ) from exc
            raise

    @staticmethod
    def _cleanup_file(path: str) -> None:
        """Safely delete file if it exists, logging any issues."""
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.debug("Cleaned up temporary file: %s", path)
        except OSError as exc:
            logger.warning("Failed to clean up temporary file '%s': %s", path, exc)
