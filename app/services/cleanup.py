"""
app/services/cleanup.py
-----------------------
Lifecycle Automated Temporary File Cleanup Service.

Handles:
- Upload -> Process -> Generate -> Download -> Expire -> Delete
- Directory-based job isolation folders
- Source videos, extracted audio, intermediates, and ZIP packages
- Configurable retention hours through environment variables
"""

from __future__ import annotations

import os
import re
import time
import shutil
import logging
from typing import List, Dict, Any, Optional, Set
from app.core.config import settings
from app.services.job_manager import JobManagerService, JobStatus
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

# Default expiration retention (4 hours)
DEFAULT_EXPIRATION_SECONDS = 14400
# Default orphaned intermediate files max age (1 hour)
ORPHANED_TEMP_MAX_AGE_SECONDS = 3600


class CleanupService:
    """
    Service responsible for cleaning up temporary and expired files across the video pipeline lifecycle.
    """

    @staticmethod
    def get_storage_dir() -> str:
        """Returns the configured temporary storage directory."""
        return settings.TEMP_STORAGE_DIR

    @classmethod
    def find_job_files(cls, job_id: str, include_final_clips: bool = False) -> List[str]:
        """
        Locates all filesystem assets associated with a specific job_id in its job directory.
        """
        job_dir = StorageService.get_job_dir(job_id)
        if not os.path.exists(job_dir):
            return []

        matched_files: List[str] = []
        try:
            for fname in os.listdir(job_dir):
                fpath = os.path.join(job_dir, fname)
                if not os.path.isfile(fpath):
                    continue

                if include_final_clips:
                    matched_files.append(fpath)
                else:
                    # Exclude final clips when keeping final results (ZIPs are intermediate)
                    is_final = "final" in fname.lower()
                    if not is_final:
                        matched_files.append(fpath)
        except OSError as err:
            logger.warning("Error reading job directory %s during file search: %s", job_dir, err)

        return matched_files

    @classmethod
    def cleanup_file(cls, file_path: str) -> bool:
        """Safely removes a single file from disk."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("Successfully deleted file: %s", file_path)
                return True
        except OSError as err:
            logger.warning("Failed to delete file %s: %s", file_path, err)
        return False

    @classmethod
    def cleanup_job_files(cls, job_id: str, delete_final_clips: bool = False) -> Dict[str, Any]:
        """
        Removes all source videos, audio extracts, subtitles, ZIPs, and intermediate files for a job.
        If delete_final_clips=True (e.g. upon expiration or failure), also removes output clips and the folder.
        """
        job_dir = StorageService.get_job_dir(job_id)
        if not os.path.exists(job_dir):
            return {
                "job_id": job_id,
                "found_files": 0,
                "deleted_files": 0
            }

        deleted_count = 0
        found_files = 0

        try:
            if delete_final_clips:
                # Delete the entire job directory recursively
                for root, dirs, files in os.walk(job_dir):
                    found_files += len(files)
                
                shutil.rmtree(job_dir, ignore_errors=True)
                deleted_count = found_files
                logger.info("Deleted entire job directory recursively for job %s", job_id)
            else:
                # Delete only intermediate files, keep final clips and ZIP package
                files = cls.find_job_files(job_id, include_final_clips=False)
                found_files = len(files)
                for f in files:
                    if cls.cleanup_file(f):
                        deleted_count += 1
                logger.info("Cleaned up %d/%d intermediate files for job %s", deleted_count, found_files, job_id)
        except Exception as e:
            logger.warning("Error cleaning up job files for %s: %s", job_id, e)

        return {
            "job_id": job_id,
            "found_files": found_files,
            "deleted_files": deleted_count
        }

    @classmethod
    def cleanup_failed_job(cls, job_id: str) -> Dict[str, Any]:
        """
        Immediately purges ALL files and the folder associated with a failed job.
        Guarantees no storage leaks on pipeline errors.
        """
        logger.info("Triggering full failure cleanup for job: %s", job_id)
        return cls.cleanup_job_files(job_id=job_id, delete_final_clips=True)

    @classmethod
    def cleanup_expired_jobs(cls, max_age_seconds: int = None) -> Dict[str, Any]:
        """
        Scans for expired job directories and orphaned loose files,
        deletes them, and updates job states to EXPIRED in Redis.
        """
        if max_age_seconds is None:
            max_age_seconds = settings.TEMP_FILE_RETENTION_HOURS * 3600

        temp_dir = cls.get_storage_dir()
        if not os.path.exists(temp_dir):
            return {"expired_jobs_cleaned": 0, "files_deleted": 0}

        now = time.time()
        files_deleted = 0
        jobs_cleaned = 0

        try:
            for fname in os.listdir(temp_dir):
                fpath = os.path.join(temp_dir, fname)
                
                # Check if directory is a job isolated folder: job_<job_id>
                if os.path.isdir(fpath) and fname.startswith("job_"):
                    job_id = fname[4:]
                    try:
                        mtime = os.path.getmtime(fpath)
                        is_expired = False
                        
                        # Verify status via JobManagerService if possible
                        try:
                            job_data = JobManagerService.get_job(job_id)
                            if job_data:
                                expires_at = job_data.get("expiresAt")
                                if expires_at and now > expires_at:
                                    is_expired = True
                                elif (now - job_data.get("updatedAt", mtime)) > max_age_seconds:
                                    is_expired = True
                            else:
                                if (now - mtime) > max_age_seconds:
                                    is_expired = True
                        except Exception:
                            if (now - mtime) > max_age_seconds:
                                is_expired = True

                        if is_expired:
                            num_files = 0
                            for r, d, fs in os.walk(fpath):
                                num_files += len(fs)
                            
                            shutil.rmtree(fpath, ignore_errors=True)
                            files_deleted += num_files
                            jobs_cleaned += 1
                            logger.info("Cleaned up expired job directory: %s (%d files)", fname, num_files)
                            
                            try:
                                JobManagerService.mark_expired(job_id)
                            except Exception:
                                pass
                    except Exception as e:
                        logger.warning("Failed to clean up job directory %s: %s", fpath, e)
                
                elif os.path.isfile(fpath):
                    # Clean up loose files
                    try:
                        mtime = os.path.getmtime(fpath)
                        if (now - mtime) > max_age_seconds:
                            if cls.cleanup_file(fpath):
                                files_deleted += 1
                    except OSError:
                        pass
        except Exception as err:
            logger.warning("Error during expired files cleanup: %s", err)

        return {
            "expired_jobs_cleaned": jobs_cleaned,
            "files_deleted": files_deleted
        }

    @classmethod
    def sweep_orphaned_intermediate_files(cls, max_age_seconds: int = ORPHANED_TEMP_MAX_AGE_SECONDS) -> int:
        """
        Cleans up lingering intermediate audio (.wav, .aac), subtitle (.ass), trimmed segments,
        and ZIP packages that have exceeded their transient TTL.
        """
        temp_dir = cls.get_storage_dir()
        if not os.path.exists(temp_dir):
            return 0

        now = time.time()
        deleted = 0
        intermediate_exts = {".wav", ".mp3", ".aac", ".ass", ".srt", ".tmp"}

        try:
            for root, dirs, files in os.walk(temp_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    ext = os.path.splitext(fname)[1].lower()
                    
                    is_intermediate = ext in intermediate_exts or "_trimmed" in fname or "_moment_" in fname
                    if is_intermediate:
                        try:
                            mtime = os.path.getmtime(fpath)
                            if (now - mtime) > max_age_seconds:
                                if cls.cleanup_file(fpath):
                                    deleted += 1
                        except OSError:
                            pass
        except Exception as err:
            logger.warning("Error during orphaned files sweep: %s", err)

        return deleted
