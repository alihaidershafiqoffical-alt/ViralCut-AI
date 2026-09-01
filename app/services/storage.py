import os
import uuid
import shutil
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from app.core.security import AnonymousSecurityService

class StorageProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available (healthy, has disk space, etc.)."""
        pass

    @abstractmethod
    def get_job_dir(self, job_id: str) -> str:
        """Get the absolute path to the unique job directory."""
        pass

    @abstractmethod
    def get_file_path(self, job_id: str, filename_or_ext: str) -> str:
        """Get the absolute path to a file inside the job's directory."""
        pass

    @abstractmethod
    async def save_upload_chunked(self, upload_file: UploadFile, job_id: str, extension: str) -> dict:
        """Stream upload file in chunks and validate size and disk capacity."""
        pass

    @abstractmethod
    def delete_job_files(self, job_id: str, delete_final_clips: bool = False) -> dict:
        """Delete files inside the job directory."""
        pass

    @abstractmethod
    def check_capacity(self, requested_bytes: int) -> bool:
        """Check if storage has enough capacity for the requested bytes."""
        pass


class LocalStorageProvider(StorageProvider):
    @property
    def provider_id(self) -> str:
        return "local"

    def is_available(self) -> bool:
        try:
            os.makedirs(settings.TEMP_STORAGE_DIR, exist_ok=True)
            total, used, free = shutil.disk_usage(settings.TEMP_STORAGE_DIR)
            free_gb = free / (1024 * 1024 * 1024)
            return free_gb >= settings.MIN_FREE_DISK_SPACE_GB
        except Exception:
            return False

    def get_job_dir(self, job_id: str) -> str:
        job_dir = os.path.join(settings.TEMP_STORAGE_DIR, f"job_{job_id}")
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    def get_file_path(self, job_id: str, filename_or_ext: str) -> str:
        job_dir = self.get_job_dir(job_id)
        # If it is just an extension like '.mp4'
        if filename_or_ext.startswith('.') or (len(filename_or_ext) <= 4 and '.' not in filename_or_ext):
            clean_ext = filename_or_ext.lower().strip()
            if not clean_ext.startswith('.'):
                clean_ext = f".{clean_ext}"
            return os.path.join(job_dir, f"{job_id}{clean_ext}")
        else:
            return os.path.join(job_dir, filename_or_ext)

    def check_capacity(self, requested_bytes: int) -> bool:
        try:
            os.makedirs(settings.TEMP_STORAGE_DIR, exist_ok=True)
            total, used, free = shutil.disk_usage(settings.TEMP_STORAGE_DIR)
            # Check if there is enough space (we need at least requested_bytes, plus minimum safety threshold)
            safety_bytes = int(settings.MIN_FREE_DISK_SPACE_GB * 1024 * 1024 * 1024)
            # Estimate processing requires 3x file size
            required_space = requested_bytes * 3
            return (free - requested_bytes) >= safety_bytes and free > required_space
        except Exception:
            return False

    async def save_upload_chunked(self, upload_file: UploadFile, job_id: str, extension: str) -> dict:
        file_path = self.get_file_path(job_id, extension)
        total_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        try:
            with open(file_path, "wb") as buffer:
                while True:
                    chunk = await upload_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    total_size += len(chunk)
                    
                    # 1. Validate max file size
                    if total_size > settings.MAX_FILE_SIZE_BYTES:
                        buffer.close()
                        shutil.rmtree(self.get_job_dir(job_id), ignore_errors=True)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="File size exceeds the maximum limit of 2GB."
                        )
                    
                    # 2. Check disk capacity during upload stream
                    if not self.check_capacity(len(chunk)):
                        buffer.close()
                        shutil.rmtree(self.get_job_dir(job_id), ignore_errors=True)
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Temporary storage is currently busy. Please try again later."
                        )
                    
                    buffer.write(chunk)
                    
            return {
                "job_id": job_id,
                "size_bytes": total_size,
            }
            
        except Exception as e:
            shutil.rmtree(self.get_job_dir(job_id), ignore_errors=True)
            raise e

    def delete_job_files(self, job_id: str, delete_final_clips: bool = False) -> dict:
        job_dir = self.get_job_dir(job_id)
        if not os.path.exists(job_dir):
            return {"job_id": job_id, "found_files": 0, "deleted_files": 0}

        deleted_count = 0
        found_files = 0
        
        try:
            if delete_final_clips:
                for r, d, fs in os.walk(job_dir):
                    found_files += len(fs)
                shutil.rmtree(job_dir)
                deleted_count = found_files
            else:
                for fname in os.listdir(job_dir):
                    fpath = os.path.join(job_dir, fname)
                    if os.path.isfile(fpath):
                        found_files += 1
                        # If not final clip, delete it
                        if "final" not in fname.lower() and not fname.endswith(".zip"):
                            os.remove(fpath)
                            deleted_count += 1
        except Exception:
            pass

        return {
            "job_id": job_id,
            "found_files": found_files,
            "deleted_files": deleted_count
        }


class FutureCloudStorageProvider(StorageProvider):
    """
    Placeholder for a future cloud-storage provider (e.g., Cloudflare R2, Supabase Storage, Backblaze B2).
    """
    @property
    def provider_id(self) -> str:
        return "cloud_placeholder"

    def is_available(self) -> bool:
        return False

    def get_job_dir(self, job_id: str) -> str:
        raise NotImplementedError("Cloud storage is not configured yet.")

    def get_file_path(self, job_id: str, filename_or_ext: str) -> str:
        raise NotImplementedError("Cloud storage is not configured yet.")

    async def save_upload_chunked(self, upload_file: UploadFile, job_id: str, extension: str) -> dict:
        raise NotImplementedError("Cloud storage is not configured yet.")

    def delete_job_files(self, job_id: str, delete_final_clips: bool = False) -> dict:
        raise NotImplementedError("Cloud storage is not configured yet.")

    def check_capacity(self, requested_bytes: int) -> bool:
        return False


class StorageManager:
    def __init__(self):
        self._providers = {
            "local": LocalStorageProvider(),
            "cloud": FutureCloudStorageProvider()
        }
        self._default_provider = "local"

    def get_provider(self) -> StorageProvider:
        provider = self._providers.get(self._default_provider)
        if provider and provider.is_available():
            return provider
        
        # Fallback to local storage if configured default is unavailable
        local_provider = self._providers["local"]
        return local_provider


# Global StorageManager instance
storage_manager = StorageManager()


# StorageService delegator class matching legacy static interfaces
class StorageService:
    @staticmethod
    def generate_job_id() -> str:
        return AnonymousSecurityService.generate_cryptographic_id()

    @staticmethod
    def get_job_dir(job_id: str) -> str:
        return storage_manager.get_provider().get_job_dir(job_id)

    @staticmethod
    def get_file_path(job_id: str, filename_or_ext: str) -> str:
        return storage_manager.get_provider().get_file_path(job_id, filename_or_ext)

    @staticmethod
    async def save_upload_chunked(upload_file: UploadFile, job_id: str, extension: str) -> dict:
        return await storage_manager.get_provider().save_upload_chunked(upload_file, job_id, extension)

    @staticmethod
    def delete_job_files(job_id: str, delete_final_clips: bool = False) -> dict:
        return storage_manager.get_provider().delete_job_files(job_id, delete_final_clips)

    @staticmethod
    def check_capacity(requested_bytes: int) -> bool:
        return storage_manager.get_provider().check_capacity(requested_bytes)

    @staticmethod
    def get_storage_status() -> str:
        try:
            # 1. Check if local directory exists and is accessible
            temp_dir = settings.TEMP_STORAGE_DIR
            os.makedirs(temp_dir, exist_ok=True)
            total, used, free = shutil.disk_usage(temp_dir)
            free_gb = free / (1024 * 1024 * 1024)
            if free_gb < 1.0:  # Less than 1GB free is critical
                return "TEMPORARILY_UNAVAILABLE"
            
            # 2. Check concurrency guard for active jobs count
            try:
                from app.services.concurrency_guard import ConcurrencyGuardService, REDIS_GLOBAL_ACTIVE_KEY
                redis = ConcurrencyGuardService.get_redis()
                if redis:
                    global_active_count = redis.scard(REDIS_GLOBAL_ACTIVE_KEY)
                    if global_active_count >= settings.MAX_CONCURRENT_JOBS_GLOBAL:
                        return "BUSY"
            except Exception:
                pass

            # 3. Check if free space is below safety threshold
            if free_gb < settings.MIN_FREE_DISK_SPACE_GB:
                return "BUSY"
                
            return "READY"
        except Exception:
            return "TEMPORARILY_UNAVAILABLE"
