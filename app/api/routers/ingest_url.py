"""
api/routers/ingest_url.py
-------------------------
POST /api/v1/videos/ingest-url

Orchestrates the full URL ingestion pipeline:
  1. URL validation (syntax + SSRF pre-check + domain allowlist)
  2. Provider resolution (YouTube / Direct URL)
  3. Secure download (post-DNS SSRF check, streaming, size abort)
  4. Media verification (ffprobe metadata extraction)
  5. Content validation (duration, resolution, codec checks)
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, field_validator, Field, ConfigDict

from app.core.rate_limiter import rate_limit, RateLimitRule
from app.services.providers import registry
from app.services.providers.base import IngestionError, UnsupportedProviderError
from app.services.storage import StorageService
from app.services.url_downloader import DownloadError, SecureDownloader
from app.services.url_validation import UrlValidationError, UrlValidationService
from app.services.video_metadata import FFprobeError, VideoMetadataService
from app.services.video_validation import VideoValidationError, VideoValidationService

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class UrlIngestRequest(BaseModel):
    """
    Body accepted by POST /ingest-url.
    """
    url: str

    @field_validator("url", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class UrlIngestResponse(BaseModel):
    """Successful ingestion response. Safe to return directly to the client."""
    jobId: str = Field(..., alias="jobId")
    provider: str
    message: str
    size_bytes: int = Field(..., alias="sizeBytes")

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/ingest-url",
    response_model=UrlIngestResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(RateLimitRule.URL_INGEST))],
    summary="Ingest a video from a URL",
    description=(
        "Validates, downloads, and verifies a video from an approved external "
        "source. Supported providers: YouTube (public videos only), and direct "
        "video links from approved storage domains."
    ),
)
async def ingest_url(body: UrlIngestRequest) -> UrlIngestResponse:
    job_id = StorageService.generate_job_id()

    # ── Stage 1: URL Validation ─────────────────────────────────────────────
    try:
        clean_url = UrlValidationService.validate(body.url)
    except UrlValidationError as exc:
        logger.warning(
            "URL validation failed [job=%s code=%s]: %s",
            job_id, exc.code, exc.technical_detail,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        )

    # ── Stage 2: Provider Resolution ────────────────────────────────────────
    try:
        resolved = await registry.resolve(clean_url)
    except UnsupportedProviderError as exc:
        logger.warning(
            "No provider matched URL [job=%s]: %s", job_id, exc.technical_detail
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.user_message,
        )
    except IngestionError as exc:
        logger.warning(
            "Provider resolution failed [job=%s]: %s", job_id, exc.technical_detail
        )
        raise HTTPException(
            status_code=exc.http_status,
            detail=exc.user_message,
        )

    # ── Stage 3: Secure Download ─────────────────────────────────────────────
    try:
        download_result = await SecureDownloader.download(
            url=resolved.download_url,
            job_id=job_id,
            extension=resolved.suggested_extension,
            content_type_hint=resolved.content_type_hint,
        )
    except DownloadError as exc:
        logger.warning(
            "Download failed [job=%s provider=%s]: %s",
            job_id, resolved.provider_id, exc.technical_detail,
        )
        raise HTTPException(
            status_code=exc.http_status,
            detail=exc.user_message,
        )

    file_path: str = download_result["file_path"]

    # ── Stage 4: Media Verification (ffprobe) ───────────────────────────────
    try:
        metadata = VideoMetadataService.extract_metadata(file_path)
    except FFprobeError as exc:
        logger.warning(
            "FFprobe extraction failed [job=%s]: %s", job_id, str(exc)
        )
        _safe_cleanup(file_path, job_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "The downloaded file could not be read as a valid video. "
                "Please try a different URL."
            ),
        )

    # ── Stage 5: Content Validation ──────────────────────────────────────────
    try:
        VideoValidationService.validate_strict(metadata)
    except VideoValidationError as exc:
        logger.warning(
            "Video validation failed [job=%s issues=%s]: %s",
            job_id,
            [i.code for i in exc.result.issues],
            exc.result.user_messages,
        )
        _safe_cleanup(file_path, job_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.result.first_message,
        )

    # ── Success ──────────────────────────────────────────────────────────────
    logger.info(
        "Ingestion complete [job=%s provider=%s size=%d duration=%.1fs]",
        job_id,
        resolved.provider_id,
        download_result["size_bytes"],
        metadata.duration_seconds,
    )

    return UrlIngestResponse(
        jobId=job_id,
        provider=resolved.provider_id,
        message="Video ingested and queued for processing.",
        sizeBytes=download_result["size_bytes"],
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _safe_cleanup(file_path: str, job_id: str) -> None:
    """Remove the downloaded file if validation fails. Best-effort."""
    import os
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug("Cleaned up failed-validation file [job=%s]", job_id)
    except OSError as exc:
        logger.warning(
            "Could not clean up file %r [job=%s]: %s", file_path, job_id, exc
        )
