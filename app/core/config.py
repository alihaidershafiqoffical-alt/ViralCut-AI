import os
import json
from typing import Dict, List, Set, Optional, Any, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ViralCut Backend"
    API_V1_STR: str = "/api/v1"
    
    # Allowed CORS Origins for production deployment
    ALLOWED_CORS_ORIGINS: List[str] = [
        "https://viralcut.ai",
        "https://www.viralcut.ai",
    ]

    @field_validator("ALLOWED_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.strip().startswith("[") and v.strip().endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, set)):
            return list(v)
        return []

    # ── Storage ────────────────────────────────────────────────────────────────
    TEMP_STORAGE_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp_uploads"
    )
    TEMP_FILE_RETENTION_HOURS: int = 12
    MIN_FREE_DISK_SPACE_GB: float = 5.0

    # ── Upload / file-size constraints ─────────────────────────────────────────
    MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB

    # ── Duration constraints (seconds) ─────────────────────────────────────────
    MIN_DURATION_SECONDS: float = 15.0       # At least 15 s to produce one Short
    MAX_DURATION_SECONDS: float = 10_800.0   # 3 hours max
    MIN_SHORT_DURATION_SECONDS: float = 15.0

    # ── Resolution constraints (pixels) ────────────────────────────────────────
    MIN_WIDTH: int = 480
    MIN_HEIGHT: int = 480
    MAX_WIDTH: int = 7680   # 8 K
    MAX_HEIGHT: int = 4320

    # ── Frame-rate constraints ──────────────────────────────────────────────────
    MIN_FPS: float = 10.0
    MAX_FPS: float = 120.0

    # ── Allowed containers (matched against ffprobe format_name tokens) ─────────
    ALLOWED_CONTAINER_KEYWORDS: List[str] = [
        "mov", "mp4", "m4a", "3gp", "3g2", "mj2",
        "matroska", "webm", "mkv",
    ]

    # ── Allowed video codecs ────────────────────────────────────────────────────
    ALLOWED_VIDEO_CODECS: Set[str] = {
        "h264", "avc1", "hevc", "h265", "hev1", "hvc1",
        "vp8", "vp9", "av01", "av1", "prores", "mpeg4", "mjpeg",
    }

    # ── Allowed audio codecs ────────────────────────────────────────────────────
    ALLOWED_AUDIO_CODECS: Set[str] = {
        "aac", "mp3", "opus", "vorbis", "flac",
        "pcm_s16le", "pcm_s24le", "pcm_s32le", "alac", "ac3", "eac3",
    }

    # ── Allowed MIME types (maps header → safe extension) ───────────────────────
    ALLOWED_MIME_TYPES: Dict[str, str] = {
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/webm": ".webm",
        "video/x-matroska": ".mkv",
    }

    # ── URL ingestion — provider allowlist ──────────────────────────────────────
    # Maps provider_id → set of exact hostnames that provider handles.
    # Only URLs whose hostname (or its registered domain) appears here are accepted.
    # To add a new provider later, add an entry here AND register a VideoProvider
    # subclass with the ProviderRegistry.
    ALLOWED_PROVIDERS: Dict[str, Set[str]] = {
        "youtube": {
            "www.youtube.com",
            "youtube.com",
            "youtu.be",
            "m.youtube.com",
        },
        "direct_url": {
            # Cloudflare R2 public bucket (replace with your actual domain)
            "pub-viralcut.r2.dev",
            # GCS / S3 — for integration tests only; remove in production
            "storage.googleapis.com",
            "s3.amazonaws.com",
        },
    }

    # ── URL ingestion — SSRF protection ────────────────────────────────────────
    # RFC-1918 private, loopback, link-local, and other non-routable CIDRs.
    # Any URL whose hostname resolves to one of these is rejected before download.
    SSRF_BLOCKED_NETWORKS: List[str] = [
        "0.0.0.0/8",          # "This" network
        "10.0.0.0/8",         # RFC-1918 class A
        "100.64.0.0/10",      # Carrier-grade NAT
        "127.0.0.0/8",        # Loopback
        "169.254.0.0/16",     # Link-local (AWS metadata endpoint lives here)
        "172.16.0.0/12",      # RFC-1918 class B
        "192.0.0.0/24",       # IETF protocol assignments
        "192.168.0.0/16",     # RFC-1918 class C
        "198.18.0.0/15",      # Benchmarking
        "198.51.100.0/24",    # TEST-NET-2
        "203.0.113.0/24",     # TEST-NET-3
        "224.0.0.0/4",        # Multicast
        "240.0.0.0/4",        # Reserved
        "255.255.255.255/32", # Broadcast
        "::1/128",            # IPv6 loopback
        "fc00::/7",           # IPv6 unique-local
        "fe80::/10",          # IPv6 link-local
    ]

    # ── URL ingestion — TLDs that are always internal ───────────────────────────
    BLOCKED_INTERNAL_TLD_SUFFIXES: Set[str] = {
        ".local",
        ".internal",
        ".localhost",
        ".corp",
        ".home",
        ".lan",
    }

    # ── URL ingestion — HTTP client settings ────────────────────────────────────
    URL_CONNECT_TIMEOUT: int = 10    # seconds to establish TCP connection
    URL_READ_TIMEOUT: int = 300      # seconds to receive response body
    MAX_REDIRECTS: int = 3           # max HTTP redirect hops
    MAX_DOWNLOAD_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB hard abort

    # ── Whisper Transcription ──────────────────────────────────────────────────
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "auto"
    WHISPER_COMPUTE_TYPE: str = "default"

    # ── Celery & Redis ─────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # ── Gemini Integration ─────────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── Anonymous Resource Protection Constraints ──────────────────────────────
    MAX_ANONYMOUS_FILE_SIZE_BYTES: int = 500 * 1024 * 1024  # 500 MB max for anonymous public tier
    MAX_ANONYMOUS_DURATION_SECONDS: float = 1800.0          # 30 minutes max video length
    MAX_CONCURRENT_JOBS_GLOBAL: int = 10                    # 10 active heavy rendering jobs globally
    MAX_CONCURRENT_JOBS_PER_IP: int = 2                     # Max 2 concurrent jobs per IP
    MAX_QUEUE_CAPACITY: int = 50                            # Max 50 queued jobs before 503 backpressure
    WORKER_TASK_TIME_LIMIT_SECONDS: int = 600               # 10 minutes hard worker timeout
    WORKER_TASK_SOFT_TIME_LIMIT_SECONDS: int = 540          # 9 minutes soft worker timeout (graceful abort)
    FFMPEG_PROCESS_TIMEOUT_SECONDS: float = 180.0           # 3 minutes max per FFmpeg sub-operation
    FFMPEG_MAX_THREADS: int = 4                             # Max CPU threads per FFmpeg encode process

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure the temp storage directory exists
os.makedirs(settings.TEMP_STORAGE_DIR, exist_ok=True)
