"""
providers/base.py
-----------------
Abstract base class and shared data types for the ViralCut video-provider
abstraction layer.

Adding a new provider
---------------------
1. Subclass ``VideoProvider``.
2. Set ``provider_id``, ``display_name``, and ``allowed_domains``.
3. Implement ``can_handle(url)`` and ``resolve(url)``.
4. Register with ``ProviderRegistry`` via ``registry.register(MyProvider())``.
5. Add the provider's hostnames to ``ALLOWED_PROVIDERS`` in config.py.

The abstraction deliberately keeps *resolution* (getting a direct-download
URL) separate from *downloading* (fetching the bytes).  This allows the
security layer in ``SecureDownloader`` to run its SSRF and size checks
against every URL, regardless of which provider produced it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Shared exception
# ---------------------------------------------------------------------------

class IngestionError(Exception):
    """
    Raised when a provider cannot resolve a URL for any reason that should
    surface as a user-visible error (e.g. private video, geo-block,
    unavailable content).

    Attributes
    ----------
    user_message : str
        Safe text to return in the HTTP response body.
    technical_detail : str
        Full diagnostic string.  Log server-side only; never send to client.
    http_status : int
        Suggested HTTP status code for the router to use.
        502 = upstream provider error.
        400 = bad request (e.g. unsupported URL format for this provider).
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


class UnsupportedProviderError(IngestionError):
    """Raised when no registered provider can handle the URL."""

    def __init__(self, url: str) -> None:
        super().__init__(
            user_message=(
                "That video source is not supported. "
                "Please use a YouTube link or a direct video URL from an "
                "approved storage provider."
            ),
            technical_detail=f"No provider matched URL: {url!r}",
            http_status=400,
        )


# ---------------------------------------------------------------------------
# ResolvedMedia — the value returned by VideoProvider.resolve()
# ---------------------------------------------------------------------------

@dataclass
class ResolvedMedia:
    """
    The result of provider resolution.  Contains everything the downloader
    needs to fetch and verify the media.

    Attributes
    ----------
    download_url : str
        A direct HTTPS URL to the raw video bytes.  Must always start with
        ``https://`` — the downloader will re-validate this.
    suggested_extension : str
        Best-guess file extension including the dot, e.g. ``".mp4"``.
    provider_id : str
        Identifier of the provider that produced this result.
    content_type_hint : str | None
        ``Content-Type`` the provider believes the response will carry.
        Used as a pre-check hint only; the actual header from the download
        response is what the downloader enforces.
    original_url : str
        The original user-supplied URL, kept for audit/logging purposes.
    """

    download_url: str
    suggested_extension: str
    provider_id: str
    content_type_hint: Optional[str] = field(default=None)
    original_url: str = field(default="")


# ---------------------------------------------------------------------------
# VideoProvider — abstract base
# ---------------------------------------------------------------------------

class VideoProvider(ABC):
    """
    Abstract base class for all video providers.

    Each subclass represents one upstream source (YouTube, direct URL, etc.)
    and is responsible for:
      - declaring which hostnames it handles (``allowed_domains``),
      - deciding at runtime whether it can handle a given URL (``can_handle``),
      - resolving the URL to a direct, downloadable HTTPS link (``resolve``).

    Providers MUST NOT:
      - Download the video themselves — that is the downloader's job.
      - Pass credentials, cookies, or auth headers to the downloader.
      - Bypass access restrictions (geo-blocks, login walls, paywalls).
        If the upstream rejects access, raise ``IngestionError`` with
        ``http_status=502``.
    """

    #: Unique, stable string ID — matches the key in ``ALLOWED_PROVIDERS``.
    provider_id: str

    #: Human-readable name shown in logs and error messages.
    display_name: str

    #: Set of lower-cased hostnames this provider handles.  Must be a subset
    #: of the hostnames registered in ``ALLOWED_PROVIDERS[provider_id]``.
    allowed_domains: set[str]

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Return True if this provider knows how to resolve *url*.

        This must be cheap and synchronous — it is called on every
        registered provider for each ingest request.
        """
        ...

    @abstractmethod
    async def resolve(self, url: str) -> ResolvedMedia:
        """
        Resolve *url* to a ``ResolvedMedia`` object.

        This may perform network I/O (e.g. call YouTube's oEmbed endpoint
        or yt-dlp's info extractor).  Any upstream error that prevents
        resolution should raise ``IngestionError``.

        Parameters
        ----------
        url:
            A validated HTTPS URL that passed ``can_handle`` for this provider.

        Returns
        -------
        ResolvedMedia
            A direct download URL and associated metadata.

        Raises
        ------
        IngestionError
            When the content cannot be accessed (private, deleted, geo-blocked).
        """
        ...
