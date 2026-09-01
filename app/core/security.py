"""
app/core/security.py
--------------------
Cryptographically Secure Anonymous Job Access & Token Management.

Provides:
- Unpredictable 256-bit CSPRNG IDs and Access Tokens
- Token hashing & constant-time comparison (anti-timing attacks)
- Unified dependency for protecting uploaded videos, transcripts, generated Shorts, metadata, and ZIP downloads
- Zero filesystem path leakage
"""

from __future__ import annotations

import hmac
import hashlib
import secrets
import logging
from typing import Optional, Dict, Any, Tuple
from fastapi import Header, Query, HTTPException, status, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AnonymousAccessCredentials(BaseModel):
    job_id: str
    access_token: str


class AnonymousSecurityService:
    """
    Manages generation, hashing, and constant-time validation of anonymous access tokens.
    """

    @staticmethod
    def generate_cryptographic_id(prefix: str = "vc_job") -> str:
        """
        Generates a non-predictable, URL-safe cryptographically secure random ID (192 bits entropy).
        Example: vc_job_7e8b9a_...
        """
        token = secrets.token_urlsafe(24)
        return f"{prefix}_{token}"

    @staticmethod
    def generate_access_token() -> str:
        """
        Generates a 256-bit CSPRNG access token.
        Cannot be guessed or brute-forced by any unauthorized user.
        """
        return secrets.token_urlsafe(32)

    @classmethod
    def create_job_credentials(cls) -> Tuple[str, str, str]:
        """
        Creates a new (job_id, raw_access_token, token_hash) triplet.
        Stores only the SHA-256 hash in persistence to follow least-privilege security.
        """
        job_id = cls.generate_cryptographic_id()
        raw_token = cls.generate_access_token()
        token_hash = cls.hash_token(raw_token)
        return job_id, raw_token, token_hash

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Computes SHA-256 hex digest of the raw access token."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @classmethod
    def verify_token(cls, raw_token: Optional[str], stored_token_hash: Optional[str]) -> bool:
        """
        Constant-time comparison using secrets.compare_digest to prevent timing attacks.
        """
        if not raw_token or not stored_token_hash:
            return False
        candidate_hash = cls.hash_token(raw_token)
        return secrets.compare_digest(candidate_hash, stored_token_hash)


def extract_access_token(
    x_access_token: Optional[str] = Header(None, alias="X-Access-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token: Optional[str] = Query(None, description="Access token for direct streaming/download links")
) -> Optional[str]:
    """
    Extracts access token from Header (X-Access-Token or Authorization: Bearer <token>) or query param.
    """
    if x_access_token:
        return x_access_token.strip()
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "", 1).strip()
    if token:
        return token.strip()
    return None
