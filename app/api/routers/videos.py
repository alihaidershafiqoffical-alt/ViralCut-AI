"""
api/routers/videos.py
---------------------
FASTAPI Router for video endpoints with cryptographically secure anonymous access.
Handles uploading files, spawning background rendering tasks (Celery/Redis),
and issuing unguessable Job IDs and Access Tokens.
"""

from __future__ import annotations

import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import AnonymousSecurityService, extract_access_token
from app.core.rate_limiter import rate_limit, RateLimitRule
from app.services.storage import StorageService
from app.services.job_manager import JobManagerService, JobStatus
from app.tasks import render_video_task

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    videoId: str = Field(..., description="Cryptographically random Video/Job ID.")
    accessToken: str = Field(..., description="256-bit secret access token for anonymous ownership.")
    message: str
    size_bytes: int
    format: str


class CaptionSettingsSchema(BaseModel):
    font: str = Field(default="Outfit")
    fontSize: float = Field(default=42)
    fontWeight: str = Field(default="bold")
    textColor: str = Field(default="#FFFFFF")
    outlineColor: str = Field(default="#000000")
    outlineWidth: float = Field(default=1.5)
    shadowColor: str = Field(default="rgba(0,0,0,0.5)")
    shadowBlur: float = Field(default=1.0)
    highlightColor: str = Field(default="#00FF00")
    highlightScale: float = Field(default=1.15)
    karaokeActive: bool = Field(default=True)
    alignment: str = Field(default="center")
    verticalPosition: float = Field(default=78)
    backgroundColor: Optional[str] = None
    backgroundPadding: Optional[str] = None
    backgroundRadius: Optional[str] = None
    animationType: str = Field(default="pop")


class WordTimestampSchema(BaseModel):
    word: str
    start: float
    end: float
    probability: float = 0.99


class RenderRequest(BaseModel):
    videoId: str = Field(..., description="Uploaded video key.")
    clipId: str = Field(..., description="Index key of the candidate Short clip.")
    startTime: float = Field(..., description="Start trim bounds in seconds.")
    endTime: float = Field(..., description="End trim bounds in seconds.")
    aspectRatio: str = Field(default="9:16", description="Target aspect preset ratio (e.g. 9:16, 1:1).")
    captionStyle: str = Field(default="Karaoke", description="Caption preset style key.")
    captionSettings: CaptionSettingsSchema = Field(default_factory=CaptionSettingsSchema)
    words: List[WordTimestampSchema] = Field(default_factory=list, description="Word level timestamps bounds.")


class RenderResponse(BaseModel):
    jobId: str
    accessToken: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/storage-status",
    status_code=status.HTTP_200_OK,
    summary="Get temporary storage availability status"
)
def get_storage_status() -> Dict[str, str]:
    """
    Check availability of the temporary storage.
    Returns: READY, BUSY, or TEMPORARILY_UNAVAILABLE.
    """
    return {"status": StorageService.get_storage_status()}


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(RateLimitRule.UPLOAD))]
)
async def upload_video(request: Request, file: UploadFile = File(...)) -> UploadResponse:
    """
    Handle video uploads securely.
    - Validates MIME type
    - Streams to temporary storage
    - Validates size limit during stream
    - Uses non-predictable CSPRNG ID and generates a secret 256-bit access token
    - Protected by anonymous IP rate limiting
    """
    from app.services.analytics import AnalyticsService
    AnalyticsService.track_event("upload_started")

    # Check overall storage status before accepting
    storage_status = StorageService.get_storage_status()
    if storage_status == "TEMPORARILY_UNAVAILABLE":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporary storage is currently busy. Please try again later."
        )

    # Check request content-length if available
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            file_size = int(content_length)
            # Make sure we don't exceed max file size (2GB)
            if file_size > settings.MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size exceeds the maximum limit of 2GB."
                )
            # Check capacity in storage safety system
            if not StorageService.check_capacity(file_size):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Temporary storage is currently busy. Please try again later."
                )
        except ValueError:
            pass

    # 1. Validate MIME type or fallback to extension
    content_type = file.content_type
    safe_extension = None
    
    if content_type and content_type in settings.ALLOWED_MIME_TYPES:
        safe_extension = settings.ALLOWED_MIME_TYPES[content_type]
    elif file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        valid_extensions = {v: v for v in settings.ALLOWED_MIME_TYPES.values()}
        if ext in valid_extensions:
            safe_extension = ext

    if not safe_extension:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported format. Allowed types: MP4, MOV, WebM, MKV."
        )
    
    # 3. Generate cryptographic credentials
    job_id, access_token, token_hash = AnonymousSecurityService.create_job_credentials()
    
    # 4. Save file chunked (size validation happens here)
    upload_metadata = await StorageService.save_upload_chunked(file, job_id, safe_extension)
    
    # 5. Initialize job record with access token hash
    JobManagerService.create_job(job_id=job_id, video_title="Uploaded Video", token_hash=token_hash)
 
    AnalyticsService.track_event("upload_completed")

    # 6. Return structured safe metadata with access token
    return UploadResponse(
        videoId=upload_metadata["job_id"],
        accessToken=access_token,
        message="Upload successful.",
        size_bytes=upload_metadata["size_bytes"],
        format=safe_extension.lstrip('.')
    )


@router.post(
    "/render",
    response_model=RenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit(RateLimitRule.JOB_CREATE))]
)
def render_video_clip(body: RenderRequest) -> RenderResponse:
    """
    Triggers the asynchronous background task to trim, crop, reframe,
    and burn styled captions onto the video clip.
    Returns 202 Accepted immediately with secure access credentials.
    """
    # 1. Resolve local video file path from the job-isolated directory
    video_dir = StorageService.get_job_dir(body.videoId)
    if not os.path.exists(video_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video file '{body.videoId}' not found or access expired."
        )
    candidates = [
        os.path.join(video_dir, f)
        for f in os.listdir(video_dir)
        if os.path.isfile(os.path.join(video_dir, f)) and not f.endswith(".wav") and not f.endswith(".aac")
    ]
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video file '{body.videoId}' not found or access expired."
        )
    video_path = candidates[0]
    
    # 2. Generate unique cryptographic render Job ID & access token
    render_job_id, access_token, token_hash = AnonymousSecurityService.create_job_credentials()
    
    # 3. Setup initial Job status in Redis with token hash
    JobManagerService.create_job(render_job_id, os.path.basename(video_path), token_hash=token_hash)
    
    # 4. Enqueue task in Celery worker queue
    render_video_task.delay(
        job_id=render_job_id,
        video_path=video_path,
        start_time=body.startTime,
        end_time=body.endTime,
        aspect_ratio=body.aspectRatio,
        caption_style_name=body.captionStyle,
        caption_settings=body.captionSettings.model_dump(),
        words_data=[w.model_dump() for w in body.words]
    )

    logger.info("Enqueued Celery background render task [job=%s, video=%s]", render_job_id, body.videoId)

    return RenderResponse(
        jobId=render_job_id,
        accessToken=access_token,
        status=JobStatus.QUEUED.value,
        message="Video rendering task has been queued successfully."
    )


@router.get("/tasks/{job_id}", response_model=Dict[str, Any])
def get_task_status(
    job_id: str,
    token: Optional[str] = Depends(extract_access_token)
) -> Dict[str, Any]:
    """
    Polls the current progress status, active step, and output URLs of a background rendering job.
    Enforces anonymous token ownership.
    """
    job_data = JobManagerService.verify_job_access(job_id, token)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rendering task not found or access token invalid."
        )
    # Strip internal token hash before returning
    safe_data = {k: v for k, v in job_data.items() if k != "tokenHash"}
    return safe_data
