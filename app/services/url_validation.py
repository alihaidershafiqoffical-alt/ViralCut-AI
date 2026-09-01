"""
url_validation.py
-----------------
Secure URL validation for the ViralCut ingestion pipeline.

Design principles:
  - Zero I/O — all checks are structural or policy-based.
  - Fail-fast: raises UrlValidationError on the first offence.
  - User-facing messages are deliberately vague to avoid leaking
    internal topology.  Technical details go to the logger only.
  - SSRF pre-check covers literal IPs; the post-DNS re-check in
    SecureDownloader covers DNS-resolved addresses.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from enum import Enum
from typing import Optional
from urllib.parse import urlparse, urlunparse

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------

class UrlValidationErrorCode(str, Enum):
    INVALID_SCHEME       = "INVALID_SCHEME"
    MALFORMED_URL        = "MALFORMED_URL"
    USERINFO_PRESENT     = "USERINFO_PRESENT"
    MISSING_HOST         = "MISSING_HOST"
    BLOCKED_INTERNAL_TLD = "BLOCKED_INTERNAL_TLD"
    LITERAL_PRIVATE_IP   = "LITERAL_PRIVATE_IP"
    DOMAIN_NOT_ALLOWED   = "DOMAIN_NOT_ALLOWED"


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class UrlValidationError(ValueError):
    """
    Raised when a URL fails any policy check.

    Attributes
    ----------
    code : UrlValidationErrorCode
        Machine-readable code for programmatic handling.
    message : str
        Safe, user-facing message — never contains internal topology.
    technical_detail : str
        Full diagnostic string for server logs only.  NEVER return this
        to the client.
    """

    def __init__(
        self,
        code: UrlValidationErrorCode,
        message: str,
        technical_detail: str,
    ) -> None:
        self.code = code
        self.message = message
        self.technical_detail = technical_detail
        super().__init__(message)


# ---------------------------------------------------------------------------
# Helper: collect all hostnames from ALLOWED_PROVIDERS
# ---------------------------------------------------------------------------

def _build_allowed_hostnames() -> frozenset[str]:
    """Flatten ALLOWED_PROVIDERS → a single set of lower-cased hostnames."""
    hosts: set[str] = set()
    for provider_hosts in settings.ALLOWED_PROVIDERS.values():
        for h in provider_hosts:
            hosts.add(h.lower())
    return frozenset(hosts)


# ---------------------------------------------------------------------------
# Helper: check whether a string is a literal IP in a blocked network
# ---------------------------------------------------------------------------

def _is_blocked_literal_ip(hostname: str) -> bool:
    """
    Return True if *hostname* is a literal IPv4/IPv6 address that falls
    inside one of the SSRF-blocked networks listed in settings.

    This is a fast, synchronous pre-check.  It does NOT perform DNS
    resolution — that second check happens in SecureDownloader after the
    TCP connection is about to be made.
    """
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        return False  # Not a literal IP at all

    blocked = [
        ipaddress.ip_network(cidr, strict=False)
        for cidr in settings.SSRF_BLOCKED_NETWORKS
    ]
    return any(addr in net for net in blocked)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class UrlValidationService:
    """
    Stateless URL validation service.

    Usage::

        try:
            clean_url = UrlValidationService.validate("https://youtu.be/...")
        except UrlValidationError as exc:
            # exc.message  → return to client
            # exc.technical_detail  → log server-side only
    """

    # Cached at class level after first access
    _allowed_hostnames: Optional[frozenset[str]] = None

    @classmethod
    def _get_allowed_hostnames(cls) -> frozenset[str]:
        if cls._allowed_hostnames is None:
            cls._allowed_hostnames = _build_allowed_hostnames()
        return cls._allowed_hostnames

    @classmethod
    def validate(cls, raw_url: str) -> str:
        """
        Validate *raw_url* against all URL security policies.

        Returns the cleaned URL (fragment stripped) on success.
        Raises ``UrlValidationError`` on the first policy violation.

        Parameters
        ----------
        raw_url:
            The URL string exactly as supplied by the user.
        """
        # ── 0. Reject obviously empty input ────────────────────────────────
        if not raw_url or not raw_url.strip():
            raise UrlValidationError(
                code=UrlValidationErrorCode.MALFORMED_URL,
                message="Please enter a video URL.",
                technical_detail="Empty or whitespace-only URL received.",
            )

        raw_url = raw_url.strip()

        # ── 1. Scheme must be HTTPS ────────────────────────────────────────
        # Parse loosely first; we do strict scheme check manually.
        parsed = urlparse(raw_url)

        if parsed.scheme.lower() != "https":
            raise UrlValidationError(
                code=UrlValidationErrorCode.INVALID_SCHEME,
                message=(
                    "Only secure HTTPS URLs are supported. "
                    "Please check your link and try again."
                ),
                technical_detail=(
                    f"Rejected scheme '{parsed.scheme}' in URL: {raw_url!r}"
                ),
            )

        # ── 2. Re-parse with strict urlparse to catch malformed URLs ───────
        try:
            parsed = urlparse(raw_url)
            if not parsed.netloc:
                raise ValueError("Empty netloc")
        except Exception as exc:
            raise UrlValidationError(
                code=UrlValidationErrorCode.MALFORMED_URL,
                message="The URL you entered doesn't appear to be valid.",
                technical_detail=f"urlparse failed for {raw_url!r}: {exc}",
            ) from exc

        # ── 3. No userinfo (username:password@host) ─────────────────────────
        if parsed.username or parsed.password:
            raise UrlValidationError(
                code=UrlValidationErrorCode.USERINFO_PRESENT,
                message="The URL you entered doesn't appear to be valid.",
                technical_detail=(
                    f"URL contains userinfo component — rejected: {raw_url!r}"
                ),
            )

        # ── 4. Hostname must be present ────────────────────────────────────
        hostname = parsed.hostname  # Normalised lower-case, brackets stripped
        if not hostname:
            raise UrlValidationError(
                code=UrlValidationErrorCode.MISSING_HOST,
                message="The URL you entered doesn't appear to be valid.",
                technical_detail=f"No hostname extracted from URL: {raw_url!r}",
            )

        # ── 5. Reject internal TLD suffixes ────────────────────────────────
        for tld_suffix in settings.BLOCKED_INTERNAL_TLD_SUFFIXES:
            if hostname.endswith(tld_suffix):
                raise UrlValidationError(
                    code=UrlValidationErrorCode.BLOCKED_INTERNAL_TLD,
                    message=(
                        "That URL points to a domain that is not supported."
                    ),
                    technical_detail=(
                        f"Hostname '{hostname}' ends with blocked TLD suffix "
                        f"'{tld_suffix}'."
                    ),
                )

        # ── 6. Reject literal IPs in SSRF-blocked ranges ───────────────────
        if _is_blocked_literal_ip(hostname):
            raise UrlValidationError(
                code=UrlValidationErrorCode.LITERAL_PRIVATE_IP,
                message=(
                    "That URL points to a domain that is not supported."
                ),
                technical_detail=(
                    f"Literal IP address '{hostname}' is in a blocked private/reserved "
                    f"network range."
                ),
            )

        # ── 7. Domain must be in the provider allowlist ────────────────────
        allowed = cls._get_allowed_hostnames()
        if hostname not in allowed:
            raise UrlValidationError(
                code=UrlValidationErrorCode.DOMAIN_NOT_ALLOWED,
                message=(
                    "That video source is not supported. "
                    "Supported sources: YouTube, and direct video links from "
                    "approved storage providers."
                ),
                technical_detail=(
                    f"Hostname '{hostname}' not found in ALLOWED_PROVIDERS allowlist."
                ),
            )

        # ── 8. Strip fragment (never useful, can confuse downstream) ────────
        clean = urlunparse(parsed._replace(fragment=""))

        logger.debug("URL passed all validation checks: %s", clean)
        return clean
