"""
api/routers/jobs.py
-------------------
FastAPI Router for cryptographically secure, anonymous Job Status inspection,
transcript access, individual Short clip streaming, and temporary ZIP downloads.

Security guarantees:
- High-entropy unguessable Job IDs & CSPRNG access tokens
- Access control validation (Header or Query token)
- Constant-time verification preventing timing side-channel attacks
- 404 returned on unauthorized requests to prevent job enumeration
- Zero filesystem path exposure
"""

import re
import os
import logging
from typing import Optional, List, Any, Literal
from fastapi import APIRouter, Request, HTTPException, Path, Query, Depends, BackgroundTasks, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict

from app.core.config import settings
from app.core.security import AnonymousSecurityService, extract_access_token
from app.core.rate_limiter import rate_limit, RateLimitRule
from app.services.job_manager import JobManagerService, JobStatus
from app.services.archive import ArchiveService
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter()

# High-entropy Safe Job ID pattern (e.g. vc_job_...)
SAFE_JOB_ID_REGEX = r"^[a-zA-Z0-9_-]{1,128}$"


class SafeClipMetadata(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None
    preview_url: Optional[str] = Field(default=None, alias="previewUrl")
    download_url: Optional[str] = Field(default=None, alias="downloadUrl")
    viral_score: Optional[float] = Field(default=None, alias="viralScore")
    start: Optional[float] = None
    end: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)


class JobStatusResponse(BaseModel):
    """
    Public schema for real-time video processing job status.
    Guaranteed safe for anonymous public consumers (no stack traces, no internal filesystem paths).
    """
    job_id: str = Field(..., alias="jobId", description="Unique identifier for the processing job.")
    status: Literal["queued", "processing", "completed", "failed", "expired"] = Field(
        ..., description="Current job lifecycle status."
    )
    current_stage: str = Field(
        ..., alias="currentStage", description="Current human-readable pipeline stage."
    )
    progress: int = Field(
        ..., ge=0, le=100, description="Overall progress percentage from 0 to 100."
    )
    generated_shorts_count: int = Field(
        default=0, alias="generatedShortsCount", description="Number of viral shorts generated so far."
    )
    target_count: int = Field(
        default=3, alias="targetCount", description="Total requested number of Shorts."
    )
    has_error: bool = Field(
        default=False, alias="hasError", description="Whether the job encountered a terminal or blocking error."
    )
    error_state: Optional[str] = Field(
        default=None, alias="errorState", description="Sanitized, user-friendly error message (no stack traces)."
    )
    is_completed: bool = Field(
        default=False, alias="isCompleted", description="Whether the job has reached a terminal completed state."
    )
    status_message: str = Field(
        ..., alias="statusMessage", description="Friendly status description for end users."
    )
    clips: List[SafeClipMetadata] = Field(
        default_factory=list, description="List of generated clip metadata."
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "jobId": "vc_job_9b1deb4d3b7d4bad9bdd2b0d7b3dcb6d",
                "status": "processing",
                "currentStage": "Generating Shorts",
                "progress": 85,
                "generatedShortsCount": 3,
                "hasError": False,
                "errorState": None,
                "isCompleted": False,
                "statusMessage": "Cropping to 9:16 vertical layout with active speaker tracking…",
                "clips": []
            }
        }
    )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get real-time processing job status (Secure Anonymous Access)",
    description="Retrieves the current progress, active stage, and generated shorts count for a video task. Requires valid token if protected.",
    dependencies=[Depends(rate_limit(RateLimitRule.STATUS_POLL))],
    status_code=status.HTTP_200_OK
)
def get_job_status(
    job_id: str = Path(
        ...,
        pattern=SAFE_JOB_ID_REGEX,
        description="The unique Job ID returned during upload or task dispatch."
    ),
    token: Optional[str] = Depends(extract_access_token)
) -> JobStatusResponse:
    """
    Secure endpoint for anonymous clients to poll processing status.
    - Validates Job ID format to prevent injection.
    - Constant-time token verification prevents timing attacks and user impersonation.
    - Strips all internal file paths and server stack traces.
    """
    if not re.match(SAFE_JOB_ID_REGEX, job_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Job ID format."
        )

    # Constant-time token verification
    job_data = JobManagerService.verify_job_access(job_id, token)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested processing job was not found or access token is invalid."
        )

    raw_status = job_data.get("status", "queued")
    if raw_status == "pending":
        job_status = "queued"
    elif raw_status in ("queued", "processing", "completed", "failed", "expired"):
        job_status = raw_status
    else:
        job_status = "processing"

    progress = int(job_data.get("progress", 0))
    progress = max(0, min(100, progress))

    stage = job_data.get("stage") or "Uploading"
    status_msg = job_data.get("statusMessage") or job_data.get("currentStep") or "Processing your video…"

    # Error sanitization
    raw_error = job_data.get("error")
    sanitized_error = JobManagerService.sanitize_error(raw_error) if raw_error else None
    has_error = bool(sanitized_error or job_status == "failed")

    # Output clips count
    raw_clips = job_data.get("clips") or []
    shorts_count = len(raw_clips)

    # Completion state
    is_completed = (job_status == "completed") or (progress >= 100 and not has_error)

    # Build safe tokenized clip URLs (no filesystem paths)
    token_param = f"?token={token}" if token else ""
    safe_clips: List[SafeClipMetadata] = []
    for c in raw_clips:
        if isinstance(c, dict):
            c_id = c.get("id") or str(c.get("index", "1"))
            c_title = c.get("title")
            c_name = os.path.basename(c.get("path") or c.get("videoUrl") or f"short_{c_id}.mp4")
            
            preview_endpoint = f"/api/v1/jobs/{job_id}/clips/{c_name}{token_param}"
            download_endpoint = f"/api/v1/jobs/{job_id}/clips/{c_name}/download{token_param}"

            safe_clips.append(
                SafeClipMetadata(
                    id=c_id,
                    title=c_title,
                    duration=c.get("duration"),
                    previewUrl=preview_endpoint,
                    downloadUrl=download_endpoint,
                    viralScore=c.get("viralScore") or c.get("viral_score") or c.get("score"),
                    start=c.get("start"),
                    end=c.get("end")
                )
            )
        elif isinstance(c, str):
            clip_filename = os.path.basename(c)
            safe_clips.append(
                SafeClipMetadata(
                    id=clip_filename,
                    title=clip_filename,
                    previewUrl=f"/api/v1/jobs/{job_id}/clips/{clip_filename}{token_param}",
                    downloadUrl=f"/api/v1/jobs/{job_id}/clips/{clip_filename}/download{token_param}"
                )
            )

    return JobStatusResponse(
        jobId=job_id,
        status=job_status,
        currentStage=stage,
        progress=progress,
        generatedShortsCount=shorts_count,
        targetCount=int(job_data.get("targetCount", 3)),
        hasError=has_error,
        errorState=sanitized_error,
        isCompleted=is_completed,
        statusMessage=status_msg,
        clips=safe_clips
    )


@router.get(
    "/{job_id}/clips/{clip_filename}",
    summary="Secure streaming preview for an individual generated Short",
    description="Streams an individual generated Short clip. Access is strictly scoped to the authorized token holder.",
    status_code=status.HTTP_200_OK
)
def get_clip_preview(
    job_id: str = Path(..., pattern=SAFE_JOB_ID_REGEX),
    clip_filename: str = Path(..., description="Filename of the requested clip"),
    token: Optional[str] = Depends(extract_access_token)
):
    """
    Streams an individual video Short to the authorized client.
    Guarantees that other anonymous users cannot view clips from foreign jobs.
    """
    # 1. Authorize token
    job_data = JobManagerService.verify_job_access(job_id, token)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found or access expired."
        )

    # 2. Sanitize filename (prevent path traversal)
    clean_name = os.path.basename(clip_filename)
    clip_path = StorageService.get_file_path(job_id, clean_name)

    if not os.path.isfile(clip_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested video clip is no longer available."
        )

    return FileResponse(
        path=clip_path,
        media_type="video/mp4",
        filename=clean_name
    )


@router.get(
    "/{job_id}/clips/{clip_filename}/download",
    summary="Download an individual generated Short clip as MP4 attachment",
    description="Downloads an individual Short with Content-Disposition attachment header.",
    dependencies=[Depends(rate_limit(RateLimitRule.DOWNLOAD))],
    status_code=status.HTTP_200_OK
)
def download_clip_file(
    job_id: str = Path(..., pattern=SAFE_JOB_ID_REGEX),
    clip_filename: str = Path(..., description="Filename of the requested clip"),
    token: Optional[str] = Depends(extract_access_token)
):
    """
    Downloads an individual video Short.
    """
    job_data = JobManagerService.verify_job_access(job_id, token)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found or access expired."
        )

    clean_name = os.path.basename(clip_filename)
    clip_path = StorageService.get_file_path(job_id, clean_name)

    if not os.path.isfile(clip_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested video clip is no longer available."
        )

    from app.services.analytics import AnalyticsService
    AnalyticsService.track_event("short_downloaded")

    return FileResponse(
        path=clip_path,
        media_type="video/mp4",
        filename=clean_name,
        headers={"Content-Disposition": f'attachment; filename="{clean_name}"'}
    )


@router.get(
    "/{job_id}/download-all",
    summary="Download all generated Shorts in a single ZIP archive",
    description="Packages only verified generated videos into a temporary ZIP, streams to the client, and automatically deletes the archive post-download.",
    dependencies=[Depends(rate_limit(RateLimitRule.DOWNLOAD))],
    status_code=status.HTTP_200_OK
)
def download_all_shorts_zip(
    background_tasks: BackgroundTasks,
    job_id: str = Path(
        ...,
        pattern=SAFE_JOB_ID_REGEX,
        description="The unique Job ID whose generated Shorts should be packaged."
    ),
    token: Optional[str] = Depends(extract_access_token)
):
    """
    Streams all generated Shorts in a temporary ZIP archive:
    - Verifies anonymous token authorization
    - Includes only valid generated video files
    - Sanitizes entry names inside the archive
    - Cleans up the temporary ZIP file immediately after streaming completes
    """
    if not re.match(SAFE_JOB_ID_REGEX, job_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Job ID format."
        )

    # Verify authorization
    job_data = JobManagerService.verify_job_access(job_id, token)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or access token is invalid."
        )

    if job_data.get("status") == "expired":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The requested video assets have expired."
        )

    clips = job_data.get("clips") or []
    if not clips:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generated video clips are available for this job yet."
        )

    # Create temporary ZIP archive
    try:
        zip_path = ArchiveService.create_shorts_archive(
            clips=clips,
            job_id=job_id,
            video_title=job_data.get("videoTitle")
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The generated video files are no longer available on disk."
        )
    except Exception as err:
        logger.error("Failed to create ZIP archive for job %s: %s", job_id, err, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate ZIP archive at this time."
        )

    # Schedule immediate post-stream cleanup
    background_tasks.add_task(ArchiveService.cleanup_archive, zip_path)

    from app.services.analytics import AnalyticsService
    AnalyticsService.track_event("zip_downloaded")

    safe_download_name = f"viralcut_shorts_{ArchiveService.sanitize_filename(job_id, 'package')}.zip"
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=safe_download_name,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_download_name}"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


@router.post(
    "/{job_id}/cancel",
    summary="Cancel active job and immediately purge all temporary files",
    description="Aborts an ongoing video processing task, releases concurrency slots, and deletes all disk assets.",
    status_code=status.HTTP_200_OK
)
def cancel_job(
    job_id: str = Path(..., pattern=SAFE_JOB_ID_REGEX),
    token: Optional[str] = Depends(extract_access_token)
):
    """
    Cancels an active job and purges temporary files.
    """
    from app.services.cleanup import CleanupService
    from app.services.concurrency_guard import ConcurrencyGuardService

    job_data = JobManagerService.verify_job_access(job_id, token)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or access token invalid."
        )

    # 1. Update status
    JobManagerService.mark_failed(job_id, "Job was cancelled by the user.")
    
    # 2. Release concurrency capacity
    ConcurrencyGuardService.release_capacity(job_id)

    # 3. Purge all files immediately
    cleanup_res = CleanupService.cleanup_failed_job(job_id)

    return {
        "jobId": job_id,
        "status": "cancelled",
        "message": "Job cancelled and temporary files were cleaned up.",
        "cleanedFiles": cleanup_res.get("deleted_files", 0)
    }


class ProcessRequest(BaseModel):
    videoSource: str = Field(..., description="YouTube URL or uploaded video ID.")
    isUrl: bool = Field(..., description="True if source is a URL, False if uploaded file.")
    targetCount: int = Field(default=3, ge=1, le=4, description="Target number of Shorts to generate (max 4 per request).")
    clipDuration: float = Field(default=30.0, ge=15.0, le=60.0, description="Max clip duration in seconds.")
    aspectRatio: str = Field(default="9:16", description="Target aspect preset ratio (e.g. 9:16, 4:5, 3:4, 1:1, 2:3).")
    topic: Optional[str] = Field(default=None, description="Optional topic focus for AI analysis.")
    startTime: Optional[float] = Field(default=None, ge=0.0, description="Optional start time to pre-trim the video.")
    endTime: Optional[float] = Field(default=None, ge=0.0, description="Optional end time to pre-trim the video.")


class ProcessResponse(BaseModel):
    jobId: str
    accessToken: str
    status: str
    message: str


@router.post(
    "/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit(RateLimitRule.JOB_CREATE))]
)
def process_video_pipeline(
    request: Request,
    body: ProcessRequest,
    background_tasks: BackgroundTasks
) -> ProcessResponse:
    """
    Triggers the overall background processing pipeline task (Celery).
    Downloads (if URL), transcribes, detects highlights, and crops clips.
    Falls back gracefully to FastAPI BackgroundTasks if Celery/Redis is offline.
    """
    from app.tasks import process_video_pipeline_task, execute_video_pipeline
    from app.services.concurrency_guard import ConcurrencyGuardService
    
    # 1. Generate job credentials
    job_id, access_token, token_hash = AnonymousSecurityService.create_job_credentials()
    
    # 2. Check overall storage availability status
    if StorageService.get_storage_status() == "TEMPORARILY_UNAVAILABLE":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporary storage is currently busy. Please try again later."
        )

    # 3. Check global queue/concurrency limits
    client_ip = request.client.host if request.client else "127.0.0.1"
    ConcurrencyGuardService.check_and_reserve_capacity(job_id, client_ip)
        
    # 4. Create job record in Redis / Memory
    JobManagerService.create_job(job_id, body.videoSource if body.isUrl else "Uploaded Video", token_hash=token_hash, target_count=body.targetCount)
    
    # 4. Enqueue task in Celery background worker with BackgroundTasks fallback
    try:
        process_video_pipeline_task.delay(
            job_id=job_id,
            video_source=body.videoSource,
            is_url=body.isUrl,
            target_count=body.targetCount,
            clip_duration=body.clipDuration,
            aspect_ratio=body.aspectRatio,
            topic=body.topic,
            start_time=body.startTime,
            end_time=body.endTime,
        )
        logger.info("Enqueued Celery background pipeline task [job=%s, source=%s]", job_id, body.videoSource)
    except Exception as err:
        logger.warning("Celery broker unreachable (%s). Fallback to FastAPI BackgroundTasks.", err)
        background_tasks.add_task(
            execute_video_pipeline,
            job_id=job_id,
            video_source=body.videoSource,
            is_url=body.isUrl,
            target_count=body.targetCount,
            clip_duration=body.clipDuration,
            aspect_ratio=body.aspectRatio,
            topic=body.topic,
            start_time=body.startTime,
            end_time=body.endTime,
        )
    
    return ProcessResponse(
        jobId=job_id,
        accessToken=access_token,
        status="queued",
        message="Video processing has been queued in the background."
    )

