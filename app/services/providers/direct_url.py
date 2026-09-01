"""
providers/direct_url.py
------------------------
``DirectUrlProvider`` — handles direct video file URLs hosted on allowlisted
storage domains (Cloudflare R2, GCS, S3).

Resolution strategy
-------------------
Direct URLs need no third-party API to resolve.  The provider performs an
HTTP HEAD request on the URL to verify:
  1. The server responds with a 2xx status.
  2. The ``Content-Type`` header is a supported video MIME type.
  3. The ``Content-Length`` (if provided) is within the size limit.

If the HEAD succeeds, the original URL is returned as ``download_url``.
The actual bytes are then fetched by ``SecureDownloader``.

Security constraints
--------------------
* Only hostnames present in ``ALLOWED_PROVIDERS["direct_url"]`` (config) are
  accepted.  This check is enforced by ``UrlValidationService`` before this
  provider is even called, but ``can_handle`` performs a redundant check as
  defense-in-depth.
* No authentication headers are added.  If the HEAD returns 401/403, an
  ``IngestionError`` is raised — we do NOT attempt to authenticate.
* Redirects during HEAD are followed up to ``MAX_REDIRECTS``, but each
  redirect target is re-validated to ensure it stays on an allowlisted host
  (handled by httpx's redirect hook in SecureDownloader; the HEAD here uses a
  simple follow_redirects=True limited to 3 hops).
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.providers.base import IngestionError, ResolvedMedia, VideoProvider

logger = logging.getLogger(__name__)


class DirectUrlProvider(VideoProvider):
    """
    Handles direct video file URLs on approved storage domains.

    Supported hostnames are configured via ``ALLOWED_PROVIDERS["direct_url"]``
    in config.py, making it easy to add more storage backends without
    touching this class.
    """

    provider_id = "direct_url"
    display_name = "Direct Video URL"

    @property
    def allowed_domains(self) -> set[str]:  # type: ignore[override]
        """Dynamically read from config so additions take effect without restart."""
        return settings.ALLOWED_PROVIDERS.get("direct_url", set())

    def can_handle(self, url: str) -> bool:
        """Return True if the URL hostname is in the direct_url allowlist."""
        try:
            hostname = urlparse(url).hostname or ""
            return hostname.lower() in self.allowed_domains
        except Exception:
            return False

    async def resolve(self, url: str) -> ResolvedMedia:
        """
        Perform a HEAD request to verify the URL is accessible and returns a
        supported Content-Type, then return the URL unchanged as ``download_url``.

        Raises
        ------
        IngestionError(http_status=400)
            URL does not end with a recognised video extension AND the server
            does not return a supported Content-Type.
        IngestionError(http_status=502)
            The HEAD request fails (connection error, timeout, non-2xx status,
            access denied).
        IngestionError(http_status=413)
            Content-Length from HEAD exceeds ``MAX_DOWNLOAD_SIZE_BYTES``.
        """
        # ── HEAD request ────────────────────────────────────────────────────
        timeout = httpx.Timeout(
            connect=settings.URL_CONNECT_TIMEOUT,
            read=settings.URL_READ_TIMEOUT,
        )

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                max_redirects=settings.MAX_REDIRECTS,
                timeout=timeout,
                # Never forward any auth or sensitive headers
                headers={"User-Agent": "ViralCut-Ingestor/1.0"},
            ) as client:
                response = await client.head(url)

        except httpx.TimeoutException as exc:
            logger.warning("HEAD request timed out for %r: %s", url, exc)
            raise IngestionError(
                user_message="The video URL took too long to respond. Please try again.",
                technical_detail=f"httpx timeout on HEAD {url!r}: {exc}",
                http_status=502,
            ) from exc

        except httpx.RequestError as exc:
            logger.warning("HEAD request failed for %r: %s", url, exc)
            raise IngestionError(
                user_message="Could not reach the video URL. Please check the link and try again.",
                technical_detail=f"httpx RequestError on HEAD {url!r}: {exc}",
                http_status=502,
            ) from exc

        # ── Status check ────────────────────────────────────────────────────
        if response.status_code == 401 or response.status_code == 403:
            raise IngestionError(
                user_message=(
                    "Access to that video URL was denied. "
                    "Please ensure the file is publicly accessible."
                ),
                technical_detail=(
                    f"HEAD {url!r} returned {response.status_code} — "
                    "access restricted, no credentials provided."
                ),
                http_status=502,
            )

        if not response.is_success:
            raise IngestionError(
                user_message=(
                    "The video URL returned an error. "
                    "Please check the link and try again."
                ),
                technical_detail=(
                    f"HEAD {url!r} returned non-2xx status {response.status_code}."
                ),
                http_status=502,
            )

        # ── Content-Type check ──────────────────────────────────────────────
        content_type_raw = response.headers.get("content-type", "")
        # Strip quality/charset params: "video/mp4; charset=..." → "video/mp4"
        content_type = content_type_raw.split(";")[0].strip().lower()

        if content_type not in settings.ALLOWED_MIME_TYPES:
            # Fall back to extension sniff as a best-effort hint
            path = urlparse(url).path.lower()
            ext_guess = next(
                (ext for ext in settings.ALLOWED_MIME_TYPES.values() if path.endswith(ext)),
                None,
            )
            if ext_guess is None:
                raise IngestionError(
                    user_message=(
                        "That URL does not point to a supported video file. "
                        "Supported formats: MP4, MOV, WebM, MKV."
                    ),
                    technical_detail=(
                        f"HEAD {url!r} returned Content-Type {content_type_raw!r}, "
                        f"not in ALLOWED_MIME_TYPES."
                    ),
                    http_status=400,
                )
            suggested_extension = ext_guess
            content_type_hint = None
        else:
            suggested_extension = settings.ALLOWED_MIME_TYPES[content_type]
            content_type_hint = content_type

        # ── Content-Length pre-check ─────────────────────────────────────────
        content_length_str = response.headers.get("content-length")
        if content_length_str:
            try:
                content_length = int(content_length_str)
                if content_length > settings.MAX_DOWNLOAD_SIZE_BYTES:
                    limit_gb = settings.MAX_DOWNLOAD_SIZE_BYTES / (1024 ** 3)
                    raise IngestionError(
                        user_message=(
                            f"The video file is too large. "
                            f"Maximum allowed size is {limit_gb:.0f} GB."
                        ),
                        technical_detail=(
                            f"Content-Length {content_length} exceeds "
                            f"MAX_DOWNLOAD_SIZE_BYTES {settings.MAX_DOWNLOAD_SIZE_BYTES}."
                        ),
                        http_status=413,
                    )
            except ValueError:
                pass  # Malformed Content-Length header — downloader will enforce

        logger.info(
            "DirectUrlProvider resolved '%s' (content-type=%s, ext=%s)",
            url,
            content_type_hint or "unknown",
            suggested_extension,
        )

        return ResolvedMedia(
            download_url=url,
            suggested_extension=suggested_extension,
            provider_id=self.provider_id,
            content_type_hint=content_type_hint,
            original_url=url,
        )
