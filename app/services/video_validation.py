"""
video_validation.py
-------------------
Comprehensive video validation service for ViralCut.

Design principles:
  - All thresholds are sourced from config.py — no magic numbers here.
  - ValidationIssue keeps user-facing messages strictly separate from
    technical/diagnostic details that should never reach the end user.
  - validate() is non-fail-fast: it collects ALL issues before returning,
    so the UI can surface every problem in one pass.
  - validate_strict() raises VideoValidationError on the first issue found,
    which is convenient for router/endpoint use.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.core.config import settings
from app.services.video_metadata import VideoMetadata

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error codes — machine-readable identifiers for the frontend
# ---------------------------------------------------------------------------

class ValidationErrorCode(str, Enum):
    FILE_TOO_LARGE       = "FILE_TOO_LARGE"
    DURATION_TOO_SHORT   = "DURATION_TOO_SHORT"
    DURATION_TOO_LONG    = "DURATION_TOO_LONG"
    UNSUPPORTED_CONTAINER = "UNSUPPORTED_CONTAINER"
    NO_VIDEO_STREAM      = "NO_VIDEO_STREAM"
    NO_AUDIO_STREAM      = "NO_AUDIO_STREAM"
    RESOLUTION_TOO_LOW   = "RESOLUTION_TOO_LOW"
    RESOLUTION_TOO_HIGH  = "RESOLUTION_TOO_HIGH"
    FPS_TOO_LOW          = "FPS_TOO_LOW"
    FPS_TOO_HIGH         = "FPS_TOO_HIGH"
    UNSUPPORTED_VIDEO_CODEC = "UNSUPPORTED_VIDEO_CODEC"
    UNSUPPORTED_AUDIO_CODEC = "UNSUPPORTED_AUDIO_CODEC"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class ValidationIssue(BaseModel):
    """
    A single validation failure.

    ``message``          — human-readable, safe to display directly to users.
    ``technical_detail`` — diagnostic info for logs/internal tooling only.
                           Never expose this field in API responses.
    ``code``             — stable enum value for programmatic frontend handling.
    """
    code: ValidationErrorCode
    message: str
    technical_detail: str


class ValidationResult(BaseModel):
    """
    The outcome of a full validation pass.

    ``is_valid`` is True only when ``issues`` is empty.
    ``issues``   contains every problem found (all checks always run).
    """
    is_valid: bool
    issues: List[ValidationIssue]

    @property
    def user_messages(self) -> List[str]:
        """Convenience: list of all user-facing messages."""
        return [issue.message for issue in self.issues]

    @property
    def first_message(self) -> Optional[str]:
        """Convenience: first user-facing message, or None if valid."""
        return self.issues[0].message if self.issues else None


# ---------------------------------------------------------------------------
# Exception (for strict / fail-fast usage)
# ---------------------------------------------------------------------------

class VideoValidationError(Exception):
    """
    Raised by ``validate_strict()`` when validation fails.

    Attributes
    ----------
    result : ValidationResult
        Full result object; inspect ``.issues`` for all failures.
    """
    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        super().__init__(result.first_message or "Video validation failed.")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class VideoValidationService:
    """
    Stateless service that validates a ``VideoMetadata`` object against the
    constraints defined in ``app.core.config.Settings``.

    All thresholds are read from ``settings`` at call time, so hot-reloaded
    config changes are picked up automatically.
    """

    @classmethod
    def validate(
        cls,
        metadata: VideoMetadata,
        *,
        requested_shorts: Optional[int] = None,
    ) -> ValidationResult:
        """
        Run all validation checks and return a ``ValidationResult``.

        This method is non-fail-fast: every check always runs so the caller
        receives a complete picture of all problems in one pass.

        Parameters
        ----------
        metadata:
            Populated ``VideoMetadata`` from ``VideoMetadataService``.
        requested_shorts:
            Optional number of Shorts the user wants to generate.
            When provided, the "too short" message becomes context-aware,
            e.g. "too short to generate 3 Shorts".
        """
        issues: List[ValidationIssue] = []

        # ── 1. Maximum file size ────────────────────────────────────────────
        if metadata.file_size_bytes > settings.MAX_FILE_SIZE_BYTES:
            limit_gb = settings.MAX_FILE_SIZE_BYTES / (1024 ** 3)
            actual_mb = metadata.file_size_bytes / (1024 ** 2)
            issues.append(ValidationIssue(
                code=ValidationErrorCode.FILE_TOO_LARGE,
                message=(
                    f"The uploaded video is too large. "
                    f"Please upload a file smaller than {limit_gb:.0f} GB."
                ),
                technical_detail=(
                    f"File size {actual_mb:.1f} MB exceeds limit of "
                    f"{settings.MAX_FILE_SIZE_BYTES / (1024 ** 2):.0f} MB."
                ),
            ))

        # ── 2. Minimum duration ─────────────────────────────────────────────
        if metadata.duration_seconds < settings.MIN_DURATION_SECONDS:
            min_sec = settings.MIN_DURATION_SECONDS

            if requested_shorts and requested_shorts > 1:
                shorts_phrase = f"{requested_shorts} Shorts"
            else:
                shorts_phrase = "a Short"

            if min_sec < 60:
                min_human = f"{int(min_sec)} seconds"
            else:
                min_human = f"{int(min_sec // 60)} minute{'s' if min_sec >= 120 else ''}"

            issues.append(ValidationIssue(
                code=ValidationErrorCode.DURATION_TOO_SHORT,
                message=(
                    f"The uploaded video is too short to generate {shorts_phrase}. "
                    f"Please upload a video that is at least {min_human} long."
                ),
                technical_detail=(
                    f"Duration {metadata.duration_seconds:.2f}s is below the "
                    f"minimum of {min_sec}s."
                ),
            ))

        # ── 3. Maximum duration ─────────────────────────────────────────────
        if metadata.duration_seconds > settings.MAX_DURATION_SECONDS:
            max_hours = settings.MAX_DURATION_SECONDS / 3600
            issues.append(ValidationIssue(
                code=ValidationErrorCode.DURATION_TOO_LONG,
                message=(
                    f"The uploaded video is too long. "
                    f"Please upload a video shorter than {max_hours:.0f} hours."
                ),
                technical_detail=(
                    f"Duration {metadata.duration_seconds:.2f}s exceeds the "
                    f"maximum of {settings.MAX_DURATION_SECONDS}s."
                ),
            ))

        # ── 4. Supported container ──────────────────────────────────────────
        container_tokens = {
            tok.strip().lower()
            for tok in metadata.container_format.replace(",", " ").split()
        }
        allowed_keywords = {k.lower() for k in settings.ALLOWED_CONTAINER_KEYWORDS}
        if not container_tokens.intersection(allowed_keywords):
            friendly_formats = "MP4, MOV, MKV, or WebM"
            issues.append(ValidationIssue(
                code=ValidationErrorCode.UNSUPPORTED_CONTAINER,
                message=(
                    f"This video container is not supported. "
                    f"Please upload a {friendly_formats} file."
                ),
                technical_detail=(
                    f"Container '{metadata.container_format}' has no overlap with "
                    f"allowed keywords: {sorted(allowed_keywords)}."
                ),
            ))

        # ── 5. Video stream existence ───────────────────────────────────────
        if metadata.width <= 0 or metadata.height <= 0:
            issues.append(ValidationIssue(
                code=ValidationErrorCode.NO_VIDEO_STREAM,
                message=(
                    "The uploaded file does not appear to contain a valid video. "
                    "Please check your file and try again."
                ),
                technical_detail=(
                    f"Invalid video dimensions reported by ffprobe: "
                    f"{metadata.width}×{metadata.height}."
                ),
            ))

        # ── 6. Audio availability ───────────────────────────────────────────
        if not metadata.has_audio:
            issues.append(ValidationIssue(
                code=ValidationErrorCode.NO_AUDIO_STREAM,
                message=(
                    "The video has no audio track. "
                    "Audio is required to generate AI Shorts."
                ),
                technical_detail="No audio stream detected by ffprobe.",
            ))

        # ── 7. Minimum resolution ───────────────────────────────────────────
        if metadata.width > 0 and metadata.height > 0:
            if metadata.width < settings.MIN_WIDTH or metadata.height < settings.MIN_HEIGHT:
                issues.append(ValidationIssue(
                    code=ValidationErrorCode.RESOLUTION_TOO_LOW,
                    message=(
                        f"The video resolution is too low "
                        f"({metadata.width}×{metadata.height}). "
                        f"Please upload a video with at least "
                        f"{settings.MIN_WIDTH}×{settings.MIN_HEIGHT} resolution."
                    ),
                    technical_detail=(
                        f"Resolution {metadata.width}×{metadata.height} is below the "
                        f"minimum of {settings.MIN_WIDTH}×{settings.MIN_HEIGHT}."
                    ),
                ))

            # ── 8. Maximum resolution ───────────────────────────────────────
            if metadata.width > settings.MAX_WIDTH or metadata.height > settings.MAX_HEIGHT:
                issues.append(ValidationIssue(
                    code=ValidationErrorCode.RESOLUTION_TOO_HIGH,
                    message=(
                        f"The video resolution is extremely high "
                        f"({metadata.width}×{metadata.height}). "
                        f"Please upload a video up to "
                        f"{settings.MAX_WIDTH}×{settings.MAX_HEIGHT}."
                    ),
                    technical_detail=(
                        f"Resolution {metadata.width}×{metadata.height} exceeds the "
                        f"maximum of {settings.MAX_WIDTH}×{settings.MAX_HEIGHT}."
                    ),
                ))

        # ── 9. Minimum FPS ──────────────────────────────────────────────────
        if metadata.fps < settings.MIN_FPS:
            issues.append(ValidationIssue(
                code=ValidationErrorCode.FPS_TOO_LOW,
                message=(
                    f"The video frame rate is too low ({metadata.fps:.1f} fps). "
                    f"Please upload a standard video recorded at "
                    f"{settings.MIN_FPS:.0f} fps or higher."
                ),
                technical_detail=(
                    f"FPS {metadata.fps:.3f} is below the minimum of {settings.MIN_FPS}."
                ),
            ))

        # ── 10. Maximum FPS ─────────────────────────────────────────────────
        if metadata.fps > settings.MAX_FPS:
            issues.append(ValidationIssue(
                code=ValidationErrorCode.FPS_TOO_HIGH,
                message=(
                    f"The video frame rate is unusually high ({metadata.fps:.1f} fps). "
                    f"Please upload a video recorded at {settings.MAX_FPS:.0f} fps or lower."
                ),
                technical_detail=(
                    f"FPS {metadata.fps:.3f} exceeds the maximum of {settings.MAX_FPS}."
                ),
            ))

        # ── 11. Video codec compatibility ───────────────────────────────────
        video_codec = metadata.video_codec.lower()
        allowed_video_codecs = {c.lower() for c in settings.ALLOWED_VIDEO_CODECS}
        if video_codec not in allowed_video_codecs:
            issues.append(ValidationIssue(
                code=ValidationErrorCode.UNSUPPORTED_VIDEO_CODEC,
                message=(
                    "This video uses an unsupported video codec. "
                    "Please convert the video to H.264 (MP4) and try again."
                ),
                technical_detail=(
                    f"Video codec '{metadata.video_codec}' is not in the allowed "
                    f"list: {sorted(allowed_video_codecs)}."
                ),
            ))

        # ── 12. Audio codec compatibility (only if audio is present) ────────
        if metadata.has_audio and metadata.audio_codec:
            audio_codec = metadata.audio_codec.lower()
            allowed_audio_codecs = {c.lower() for c in settings.ALLOWED_AUDIO_CODECS}
            if audio_codec not in allowed_audio_codecs:
                issues.append(ValidationIssue(
                    code=ValidationErrorCode.UNSUPPORTED_AUDIO_CODEC,
                    message=(
                        "This video uses an unsupported audio codec. "
                        "Please re-encode the audio as AAC or MP3 and try again."
                    ),
                    technical_detail=(
                        f"Audio codec '{metadata.audio_codec}' is not in the allowed "
                        f"list: {sorted(allowed_audio_codecs)}."
                    ),
                ))

        is_valid = len(issues) == 0

        if not is_valid:
            logger.warning(
                "Video validation failed with %d issue(s): %s",
                len(issues),
                [i.code for i in issues],
            )

        return ValidationResult(is_valid=is_valid, issues=issues)

    @classmethod
    def validate_strict(
        cls,
        metadata: VideoMetadata,
        *,
        requested_shorts: Optional[int] = None,
    ) -> None:
        """
        Run all validation checks. Raises ``VideoValidationError`` if any
        check fails, carrying the full ``ValidationResult`` for inspection.

        Use this in request handlers where you want a single exception to
        propagate and be translated into an HTTP error response.
        """
        result = cls.validate(metadata, requested_shorts=requested_shorts)
        if not result.is_valid:
            raise VideoValidationError(result)
