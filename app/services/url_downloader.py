"""
url_downloader.py
-----------------
``SecureDownloader`` — the only component permitted to write remote bytes to
disk in the ViralCut ingestion pipeline.

Security model
--------------
Every call to ``download()`` enforces the following invariants:

1.  **HTTPS-only input**: The URL is re-checked for the https scheme even
    though UrlValidationService already verified it.  Defense-in-depth.

2.  **Post-DNS SSRF check**: The resolved hostname is looked up via DNS
    *before* the first byte is sent.  Every IP in the answer set is tested
    against SSRF_BLOCKED_NETWORKS.  This catches DNS-based SSRF where an
    attacker registers a public domain that resolves to a private IP.

3.  **No credentials forwarded**: The httpx client is created with a minimal,
    explicit header set.  No ``Authorization``, ``Cookie``, or ``X-*`` headers
    are ever added.

4.  **Redirect safety**: Each redirect target URL is scheme-checked (HTTPS)
    and its resolved IP is re-validated against the SSRF block list before the
    client follows it.

5.  **Streaming with size abort**: Bytes are written to a temporary file in
    chunks.  If the running total exceeds ``MAX_DOWNLOAD_SIZE_BYTES``, the
    connection is dropped, the partial file is deleted, and a ``DownloadError``
    is raised.

6.  **Content-Type enforcement**: The ``Content-Type`` response header must be
    in ``ALLOWED_MIME_TYPES`` before any bytes are persisted.

7.  **Atomic temp-file naming**: The file is written as ``<job_id>.partial``
    and renamed to ``<job_id><ext>`` only on success.  A failed download never
    leaves a valid-looking file on disk.

8.  **Timeout**: Both connection and read phases are independently time-bounded.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import socket
from typing import Optional

import httpx

from app.core.config import settings
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class DownloadError(Exception):
    """
    Raised when ``SecureDownloader.download()`` cannot complete safely.

    Attributes
    ----------
    user_message : str
        Safe text suitable for returning to the client.
    technical_detail : str
        Full diagnostic detail — log server-side only.
    http_status : int
        Suggested HTTP status code.
    """

    def __init__(
        self,
        user_message: str,
        technical_detail: str,
        http_status: int = 502,
    ) -> None:
        self.user_message = user_message
        self.technical_detail = technical_detail
        self.http_status = http_status
        super().__init__(user_message)


# ---------------------------------------------------------------------------
# Internal SSRF helpers
# ---------------------------------------------------------------------------

def _build_blocked_networks() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    return [
        ipaddress.ip_network(cidr, strict=False)
        for cidr in settings.SSRF_BLOCKED_NETWORKS
    ]


def _is_ip_blocked(ip_str: str) -> bool:
    """Return True if *ip_str* falls in a blocked network."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(addr in net for net in _build_blocked_networks())


def _ssrf_check_hostname(hostname: str) -> None:
    """
    Resolve *hostname* via DNS and verify every returned IP is routable.

    Raises ``DownloadError`` (http_status=422) if any IP is in a blocked
    private/reserved range.

    This is the post-DNS check that complements the pre-check in
    ``UrlValidationService`` (which only blocks literal IPs).
    """
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise DownloadError(
            user_message="Could not resolve the video URL's hostname.",
            technical_detail=f"DNS resolution failed for '{hostname}': {exc}",
            http_status=502,
        ) from exc

    for _, _, _, _, sockaddr in addr_infos:
        ip = sockaddr[0]
        if _is_ip_blocked(ip):
            raise DownloadError(
                user_message=(
                    "That URL points to an address that is not permitted."
                ),
                technical_detail=(
                    f"SSRF block: hostname '{hostname}' resolved to "
                    f"private/reserved IP '{ip}'."
                ),
                http_status=422,
            )


# ---------------------------------------------------------------------------
# SecureDownloader
# ---------------------------------------------------------------------------

class SecureDownloader:
    """
    Stateless downloader that streams a remote URL to a local temp file.

    Call ``download(url, job_id, extension)`` from a router or Celery task.
    The file will be placed at the path returned by ``StorageService.get_file_path``.
    """

    @staticmethod
    async def download(
        url: str,
        job_id: str,
        extension: str,
        content_type_hint: Optional[str] = None,
    ) -> dict:
        """
        Stream *url* to a temporary file and return basic file metadata.

        Parameters
        ----------
        url:
            Direct HTTPS URL to the video resource.
        job_id:
            UUID string used to name the temp file.
        extension:
            File extension (including the dot, e.g. ``".mp4"``).
        content_type_hint:
            Optional expected MIME type from the provider (used for early
            Content-Type validation; the actual response header takes priority).

        Returns
        -------
        dict
            ``{"job_id": str, "size_bytes": int, "file_path": str}``
            Note: ``file_path`` is for internal use only — never return it
            to the client.

        Raises
        ------
        DownloadError
            On any security or I/O failure.  The caller maps this to the
            appropriate HTTP error response.
        """
        # ── 1. Scheme re-check ──────────────────────────────────────────────
        if not url.startswith("https://"):
            raise DownloadError(
                user_message="Only secure HTTPS URLs can be downloaded.",
                technical_detail=f"Non-HTTPS URL reached downloader: {url[:80]!r}",
                http_status=400,
            )

        # ── 2. Post-DNS SSRF check ──────────────────────────────────────────
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if not hostname:
            raise DownloadError(
                user_message="Invalid video URL.",
                technical_detail=f"No hostname extractable from URL: {url[:80]!r}",
                http_status=400,
            )

        _ssrf_check_hostname(hostname)

        # ── 3. Set up file paths ────────────────────────────────────────────
        partial_path = StorageService.get_file_path(job_id, ".partial")
        final_path = StorageService.get_file_path(job_id, extension)

        # ── 4. Configure httpx client ───────────────────────────────────────
        # Explicit, minimal headers only — no credentials, no cookies.
        client_headers = {
            "User-Agent": "ViralCut-Ingestor/1.0",
            "Accept": "video/*,*/*;q=0.8",
        }
        timeout = httpx.Timeout(
            connect=settings.URL_CONNECT_TIMEOUT,
            read=settings.URL_READ_TIMEOUT,
        )

        total_bytes = 0
        chunk_size = 1024 * 1024  # 1 MB chunks

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                max_redirects=settings.MAX_REDIRECTS,
                timeout=timeout,
                headers=client_headers,
                event_hooks={
                    "request": [SecureDownloader._on_request],
                    "response": [SecureDownloader._on_redirect_response],
                },
            ) as client:
                async with client.stream("GET", url) as response:

                    # ── 5. Check HTTP status ────────────────────────────────
                    if response.status_code in (401, 403):
                        raise DownloadError(
                            user_message=(
                                "Access to that video was denied. "
                                "Please ensure the video is publicly accessible."
                            ),
                            technical_detail=(
                                f"GET {url!r} returned {response.status_code}. "
                                "No credentials were provided."
                            ),
                            http_status=502,
                        )

                    if not response.is_success:
                        raise DownloadError(
                            user_message="The video URL returned an error. Please try again.",
                            technical_detail=(
                                f"GET {url!r} returned {response.status_code}."
                            ),
                            http_status=502,
                        )

                    # ── 6. Content-Type validation ──────────────────────────
                    content_type_raw = response.headers.get("content-type", "")
                    content_type = content_type_raw.split(";")[0].strip().lower()

                    if content_type not in settings.ALLOWED_MIME_TYPES:
                        raise DownloadError(
                            user_message=(
                                "The downloaded content is not a supported video format. "
                                "Supported formats: MP4, MOV, WebM, MKV."
                            ),
                            technical_detail=(
                                f"Response Content-Type '{content_type_raw}' is not in "
                                f"ALLOWED_MIME_TYPES for {url!r}."
                            ),
                            http_status=415,
                        )

                    # ── 7. Streaming download with size abort ───────────────
                    with open(partial_path, "wb") as fh:
                        async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                            total_bytes += len(chunk)

                            if total_bytes > settings.MAX_DOWNLOAD_SIZE_BYTES:
                                limit_gb = settings.MAX_DOWNLOAD_SIZE_BYTES / (1024 ** 3)
                                raise DownloadError(
                                    user_message=(
                                        f"The video file is too large. "
                                        f"Maximum allowed size is {limit_gb:.0f} GB."
                                    ),
                                    technical_detail=(
                                        f"Download aborted at {total_bytes} bytes — "
                                        f"exceeds MAX_DOWNLOAD_SIZE_BYTES "
                                        f"{settings.MAX_DOWNLOAD_SIZE_BYTES}."
                                    ),
                                    http_status=413,
                                )

                            fh.write(chunk)

            # ── 8. Atomic rename on success ─────────────────────────────────
            os.replace(partial_path, final_path)

            logger.info(
                "Download complete: job_id=%s size_bytes=%d path=%s",
                job_id,
                total_bytes,
                final_path,
            )

            return {
                "job_id": job_id,
                "size_bytes": total_bytes,
                "file_path": final_path,  # Internal use only
            }

        except DownloadError:
            # Clean up partial file before re-raising
            _safe_remove(partial_path)
            raise

        except httpx.TimeoutException as exc:
            _safe_remove(partial_path)
            logger.warning("Download timed out for %r: %s", url, exc)
            raise DownloadError(
                user_message="The video download timed out. Please try again later.",
                technical_detail=f"httpx timeout for {url!r}: {exc}",
                http_status=504,
            ) from exc

        except httpx.RequestError as exc:
            _safe_remove(partial_path)
            logger.warning("Download request error for %r: %s", url, exc)
            raise DownloadError(
                user_message="A network error occurred while downloading the video.",
                technical_detail=f"httpx RequestError for {url!r}: {exc}",
                http_status=502,
            ) from exc

        except Exception as exc:
            _safe_remove(partial_path)
            logger.exception("Unexpected download error for %r", url)
            raise DownloadError(
                user_message="An unexpected error occurred while downloading the video.",
                technical_detail=f"Unexpected error: {exc}",
                http_status=500,
            ) from exc

    # ── httpx event hooks ───────────────────────────────────────────────────

    @staticmethod
    async def _on_request(request: httpx.Request) -> None:
        """
        Log outgoing requests.  Ensure no auth headers have slipped in.
        This runs before every request and every redirect.
        """
        # Paranoid safety guard: remove any auth-like headers if somehow present
        for header in ("authorization", "cookie", "x-api-key", "proxy-authorization"):
            if header in request.headers:
                del request.headers[header]
                logger.warning(
                    "Removed disallowed header '%s' from outgoing request to %s",
                    header,
                    request.url,
                )

    @staticmethod
    async def _on_redirect_response(response: httpx.Response) -> None:
        """
        Validate redirect targets to prevent SSRF via redirect chains.
        Called by httpx before following each redirect.
        """
        if response.is_redirect:
            location = response.headers.get("location", "")
            if location:
                # Ensure redirect is still HTTPS
                if not location.startswith("https://"):
                    raise DownloadError(
                        user_message="The video URL redirected to an unsecured address.",
                        technical_detail=(
                            f"Redirect to non-HTTPS location: {location[:80]!r}"
                        ),
                        http_status=502,
                    )

                # SSRF check on redirect target hostname
                from urllib.parse import urlparse as _urlparse
                redir_hostname = _urlparse(location).hostname or ""
                if redir_hostname:
                    _ssrf_check_hostname(redir_hostname)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _safe_remove(path: str) -> None:
    """Delete *path* if it exists; swallow errors (best-effort cleanup)."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        logger.warning("Could not remove partial download file %r: %s", path, exc)
