"""
providers/youtube.py
--------------------
``YouTubeProvider`` — resolves public YouTube video URLs to a direct CDN
stream URL using yt-dlp's Python API in restricted, no-auth mode.

Security constraints
--------------------
* No cookies are passed.  ``cookiefile`` and ``cookiesfrombrowser`` options
  are explicitly set to None/absent.
* ``noplaylist=True`` prevents playlist expansion (unbounded downloads).
* ``quiet=True`` suppresses all yt-dlp console output.
* ``no_warnings=True`` keeps logs clean.
* If yt-dlp raises ``DownloadError`` (video private, deleted, geo-blocked),
  the exception is wrapped in ``IngestionError`` with http_status=502.
* The resolved URL is an HTTPS CDN link; it passes through SecureDownloader's
  full SSRF and size checks before any bytes are fetched.

This provider intentionally does NOT:
  - Log in to YouTube.
  - Use any account credentials or session tokens.
  - Bypass age-gates, geo-restrictions, or any other access control.
  - Extract or cache cookies from any browser.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from app.services.providers.base import IngestionError, ResolvedMedia, VideoProvider

logger = logging.getLogger(__name__)

# yt-dlp is optional — imported inside the method so the rest of the app
# still starts if the package isn't installed (just with this provider broken).
try:
    import yt_dlp  # type: ignore[import]
    _YT_DLP_AVAILABLE = True
except ImportError:
    _YT_DLP_AVAILABLE = False
    logger.warning(
        "yt-dlp is not installed.  YouTubeProvider will be non-functional. "
        "Install it with: pip install yt-dlp"
    )


class YouTubeProvider(VideoProvider):
    """
    Resolves public YouTube video URLs to a direct CDN stream link.

    Supported hostnames
    -------------------
    www.youtube.com, youtube.com, m.youtube.com, youtu.be
    """

    provider_id = "youtube"
    display_name = "YouTube"
    allowed_domains = {
        "www.youtube.com",
        "youtube.com",
        "m.youtube.com",
        "youtu.be",
    }

    def can_handle(self, url: str) -> bool:
        """Return True if the URL hostname belongs to YouTube."""
        try:
            hostname = urlparse(url).hostname or ""
            return hostname.lower() in self.allowed_domains
        except Exception:
            return False

    async def resolve(self, url: str) -> ResolvedMedia:
        """
        Extract the best-quality direct stream URL for a public YouTube video.

        Raises
        ------
        IngestionError(http_status=400)
            yt-dlp is not installed.
        IngestionError(http_status=502)
            Video is private, deleted, geo-blocked, or otherwise inaccessible.
        IngestionError(http_status=400)
            URL is a playlist — playlists are not supported.
        """
        if not _YT_DLP_AVAILABLE:
            raise IngestionError(
                user_message="YouTube video ingestion is temporarily unavailable.",
                technical_detail="yt-dlp is not installed on this server.",
                http_status=400,
            )

        ydl_opts = {
            # ── Output / display ──────────────────────────────────────────
            "quiet": True,
            "no_warnings": True,
            # ── Playlist safety ───────────────────────────────────────────
            # Prevents a single video URL from silently expanding into
            # hundreds of videos from a playlist.
            "noplaylist": True,
            # ── Authentication — intentionally disabled ───────────────────
            # NEVER set cookiefile, cookiesfrombrowser, username, or password.
            # We only access publicly available content.
            # ── Format selection ──────────────────────────────────────────
            # Best single file that carries both video and audio (avoids the
            # need to merge streams), capped at 1080p, MP4 preferred.
            "format": (
                "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]"
                "/best[ext=mp4][height<=1080]"
                "/best[height<=1080]"
                "/best"
            ),
            # ── Extract only; do NOT download ─────────────────────────────
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.debug("yt-dlp extracting info for: %s", url)
                info = ydl.extract_info(url, download=False)

                if info is None:
                    raise IngestionError(
                        user_message="Could not retrieve video information. The video may be unavailable.",
                        technical_detail=f"yt-dlp returned None for URL: {url!r}",
                        http_status=502,
                    )

                # Reject playlists (extra safety guard beyond noplaylist=True)
                if info.get("_type") == "playlist":
                    raise IngestionError(
                        user_message=(
                            "Playlist URLs are not supported. "
                            "Please paste the URL of a single video."
                        ),
                        technical_detail=f"yt-dlp resolved URL as playlist: {url!r}",
                        http_status=400,
                    )

                download_url: str | None = info.get("url")
                if not download_url:
                    raise IngestionError(
                        user_message="Could not retrieve a download link for this video.",
                        technical_detail=(
                            f"yt-dlp info dict missing 'url' key for: {url!r}. "
                            f"Available keys: {list(info.keys())}"
                        ),
                        http_status=502,
                    )

                # Safety: confirm resolved URL is still HTTPS
                if not download_url.startswith("https://"):
                    raise IngestionError(
                        user_message="Could not retrieve a secure download link for this video.",
                        technical_detail=(
                            f"yt-dlp returned a non-HTTPS URL: {download_url[:60]!r}"
                        ),
                        http_status=502,
                    )

                ext = info.get("ext", "mp4")
                content_type_map = {
                    "mp4": "video/mp4",
                    "webm": "video/webm",
                    "mkv": "video/x-matroska",
                    "mov": "video/quicktime",
                }
                content_type_hint = content_type_map.get(ext.lower())

                logger.info(
                    "YouTubeProvider resolved '%s' → %s (ext=%s)",
                    url,
                    download_url[:60] + "…",
                    ext,
                )

                return ResolvedMedia(
                    download_url=download_url,
                    suggested_extension=f".{ext}",
                    provider_id=self.provider_id,
                    content_type_hint=content_type_hint,
                    original_url=url,
                )

        except IngestionError:
            raise  # Already wrapped — let it propagate

        except yt_dlp.utils.DownloadError as exc:
            error_msg = str(exc).lower()

            # Map common yt-dlp errors to user-friendly messages.
            if "private" in error_msg:
                user_msg = "This video is private and cannot be accessed."
            elif "not available" in error_msg or "unavailable" in error_msg:
                user_msg = "This video is unavailable."
            elif "geo" in error_msg or "blocked" in error_msg or "restricted" in error_msg:
                user_msg = (
                    "This video is not available in the server's region "
                    "or has restricted access."
                )
            elif "members only" in error_msg or "join" in error_msg:
                user_msg = "This video is for channel members only."
            elif "age" in error_msg:
                user_msg = "This video has age restrictions that prevent access."
            else:
                user_msg = (
                    "Could not retrieve this video. "
                    "Please check that the video is publicly accessible and try again."
                )

            logger.warning(
                "yt-dlp DownloadError for %r: %s", url, exc
            )
            raise IngestionError(
                user_message=user_msg,
                technical_detail=f"yt-dlp DownloadError: {exc}",
                http_status=502,
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected yt-dlp error for %r", url)
            raise IngestionError(
                user_message="An unexpected error occurred while processing the video URL.",
                technical_detail=f"Unexpected yt-dlp error: {exc}",
                http_status=502,
            ) from exc
