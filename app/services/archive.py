"""
app/services/archive.py
-----------------------
Service for packaging generated Shorts into temporary ZIP archives.
Ensures:
- Only verified video files are included
- Safe, sanitized file names inside the archive
- Efficient streaming and zero permanent storage
- Immediate post-download cleanup and TTL sweeps
"""

from __future__ import annotations

import os
import re
import time
import zipfile
import tempfile
import logging
from typing import List, Dict, Any, Optional, Generator
from app.core.config import settings
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

# Allowed video extensions to include in the ZIP package
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv"}

# Temporary zip prefix
ZIP_PREFIX = "viralcut_shorts_"
# Max age for stale archive cleanup (10 minutes)
ARCHIVE_TTL_SECONDS = 600


class ArchiveService:
    """
    Manages packaging and streaming of temporary ZIP archives for generated Shorts.
    """

    @staticmethod
    def sanitize_filename(filename: str, fallback: str = "short.mp4") -> str:
        """
        Sanitizes a filename to ensure safety inside ZIP archives:
        - Removes directory traversal (../, \\)
        - Removes forbidden OS characters (< > : " / \\ | ? *)
        - Enforces valid video extension
        - Limits length
        """
        if not filename:
            return fallback

        # Strip directory components
        base = os.path.basename(filename)
        # Normalize name and extension
        name, ext = os.path.splitext(base)
        ext = ext.lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            ext = ".mp4"

        # Remove unsafe characters
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name).strip()
        safe_name = re.sub(r'[\s]+', '_', safe_name)

        if not safe_name:
            safe_name = "viralcut_short"

        # Truncate overly long names
        if len(safe_name) > 60:
            safe_name = safe_name[:60]

        return f"{safe_name}{ext}"

    @classmethod
    def is_valid_video_file(cls, file_path: str) -> bool:
        """Verifies that the file exists and has an approved video extension."""
        if not os.path.isfile(file_path):
            return False
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ALLOWED_VIDEO_EXTENSIONS

    @classmethod
    def create_shorts_archive(
        cls,
        clips: List[Dict[str, Any] | str],
        job_id: str,
        video_title: Optional[str] = None
    ) -> str:
        """
        Packages only valid generated video files into a temporary ZIP archive.
        Returns the absolute path to the temporary ZIP file.
        Uses ZIP_STORED (no re-compression) for high-speed streaming without CPU overhead.
        """
        cls.cleanup_stale_archives()

        temp_dir = StorageService.get_job_dir(job_id)

        # Create temporary zip with unique prefix inside job directory
        safe_job_id = re.sub(r'[^a-zA-Z0-9_-]', '', job_id) or "job"
        zip_filename = f"{ZIP_PREFIX}{safe_job_id}_{int(time.time())}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        valid_files_count = 0

        # Open ZIP file for writing
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_STORED) as zip_file:
            for idx, clip in enumerate(clips, start=1):
                raw_path = None
                clip_title = None

                if isinstance(clip, dict):
                    raw_path = (
                        clip.get("path") or
                        clip.get("filePath") or
                        clip.get("videoUrl") or
                        clip.get("video_url") or
                        clip.get("previewUrl") or
                        clip.get("downloadUrl")
                    )
                    clip_title = clip.get("title")
                elif isinstance(clip, str):
                    raw_path = clip

                if not raw_path:
                    continue

                # Resolve relative URL to local file path in the job directory
                local_path = raw_path
                if local_path.startswith("/clips/") or local_path.startswith("/api/") or not os.path.isabs(local_path):
                    local_path = StorageService.get_file_path(job_id, os.path.basename(local_path))

                # Filter strictly: only valid existing video files
                if not cls.is_valid_video_file(local_path):
                    logger.warning("Skipping non-video or missing file during ZIP creation: %s", local_path)
                    continue

                # Build clean internal name inside the archive
                ext = os.path.splitext(local_path)[1]
                if clip_title:
                    safe_entry_name = cls.sanitize_filename(f"{idx:02d}_{clip_title}{ext}")
                else:
                    safe_entry_name = f"viralcut_short_{idx:02d}{ext}"

                # Write directly to ZIP archive
                zip_file.write(local_path, arcname=safe_entry_name)
                valid_files_count += 1
                logger.debug("Added %s as '%s' to ZIP archive", local_path, safe_entry_name)

        if valid_files_count == 0:
            # Clean up empty zip
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise FileNotFoundError("No valid generated video clips available to package into archive.")

        logger.info("Successfully created temporary ZIP archive (%d clips) at %s", valid_files_count, zip_path)
        return zip_path

    @staticmethod
    def cleanup_archive(zip_path: str) -> None:
        """Safely removes the temporary ZIP file from disk immediately after download."""
        try:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
                logger.info("Temporary ZIP archive deleted post-download: %s", zip_path)
        except Exception as err:
            logger.warning("Failed to delete temporary ZIP %s: %s", zip_path, err)

    @classmethod
    def cleanup_stale_archives(cls, max_age_seconds: int = ARCHIVE_TTL_SECONDS) -> int:
        """Sweeps and removes any orphaned temporary ZIP archives older than TTL."""
        temp_dir = settings.TEMP_STORAGE_DIR
        if not os.path.exists(temp_dir):
            return 0

        now = time.time()
        cleaned_count = 0

        try:
            for fname in os.listdir(temp_dir):
                if fname.startswith(ZIP_PREFIX) and fname.endswith(".zip"):
                    fpath = os.path.join(temp_dir, fname)
                    try:
                        mtime = os.path.getmtime(fpath)
                        if (now - mtime) > max_age_seconds:
                            os.remove(fpath)
                            cleaned_count += 1
                            logger.debug("Cleaned up expired temporary ZIP: %s", fname)
                    except OSError:
                        pass
        except Exception as e:
            logger.warning("Error during stale archive sweep: %s", e)

        return cleaned_count
