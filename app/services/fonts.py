"""
app/services/fonts.py
---------------------
Safe Font Registry and Validation system.
Manages SIL Open Font License compatible fonts (Inter, Poppins, Montserrat, Roboto)
and provides an automated download/caching system to obtain font TTF binaries
from Google Fonts on-demand, ensuring FFmpeg does not rely on OS-installed fonts.
"""

from __future__ import annotations

import os
import logging
import httpx
from typing import List, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FontDefinition(BaseModel):
    """Configuration structure representing a legally compliant web and video font."""
    name: str = Field(..., description="The font name (e.g. Inter, Poppins, Montserrat, Roboto).")
    license_type: str = Field(..., description="License type ensuring commercial usability (e.g. SIL OFL 1.1).")
    google_fonts_url: str = Field(..., description="Public Google Fonts direct download URL for the TTF file.")
    local_filename: str = Field(..., description="Filename to store the TTF binary locally (e.g. Montserrat-Bold.ttf).")
    fallback_font: str = Field(default="Roboto", description="Fallback font name to use if this font is unavailable.")


# ---------------------------------------------------------------------------
# Legally Safe Font Definitions (SIL Open Font License)
# ---------------------------------------------------------------------------

INTER_FONT = FontDefinition(
    name="Inter",
    license_type="SIL Open Font License 1.1",
    google_fonts_url="https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Bold.ttf",
    local_filename="Inter-Bold.ttf",
    fallback_font="Roboto"
)

POPPINS_FONT = FontDefinition(
    name="Poppins",
    license_type="SIL Open Font License 1.1",
    google_fonts_url="https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    local_filename="Poppins-Bold.ttf",
    fallback_font="Roboto"
)

MONTSERRAT_FONT = FontDefinition(
    name="Montserrat",
    license_type="SIL Open Font License 1.1",
    google_fonts_url="https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf",
    local_filename="Montserrat-Bold.ttf",
    fallback_font="Roboto"
)

ROBOTO_FONT = FontDefinition(
    name="Roboto",
    license_type="Apache License 2.0",
    google_fonts_url="https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Bold.ttf",
    local_filename="Roboto-Bold.ttf",
    fallback_font="Inter"
)

FONT_REGISTRY: Dict[str, FontDefinition] = {
    "inter": INTER_FONT,
    "poppins": POPPINS_FONT,
    "montserrat": MONTSERRAT_FONT,
    "roboto": ROBOTO_FONT
}

DEFAULT_FALLBACK = ROBOTO_FONT


class FontRegistryService:
    """
    Manages loading, validating, and local storage download checks for caption fonts.
    """

    @classmethod
    def get_font_dir(cls) -> str:
        """Returns the absolute path to the local directory where font binaries are cached."""
        # Places fonts inside backend/app/resources/fonts/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_dir = os.path.join(base_dir, "resources", "fonts")
        os.makedirs(font_dir, exist_ok=True)
        return font_dir

    @classmethod
    def validate_font(cls, name: str) -> FontDefinition:
        """
        Validates if the requested font is registered.
        Falls back to default fallback if invalid, logging a warning.
        """
        key = name.lower().strip()
        if key in FONT_REGISTRY:
            return FONT_REGISTRY[key]
        
        logger.warning(
            "Requested font '%s' is not registered or licensed. Falling back to default: '%s'.",
            name, DEFAULT_FALLBACK.name
        )
        return DEFAULT_FALLBACK

    @classmethod
    def get_font_file_path(cls, name: str) -> str:
        """
        Retrieves the absolute local file path for a font's TTF file.
        Checks if it exists locally, and returns the path.
        """
        font_def = cls.validate_font(name)
        font_dir = cls.get_font_dir()
        return os.path.join(font_dir, font_def.local_filename)

    @classmethod
    async def ensure_font_downloaded(cls, name: str) -> str:
        """
        Ensures the font's TTF file is downloaded locally.
        If not found in the resources/fonts folder, downloads it dynamically from Google Fonts.
        Returns the absolute local path to the TTF file.
        """
        font_def = cls.validate_font(name)
        file_path = cls.get_font_file_path(font_def.name)

        if os.path.exists(file_path):
            logger.debug("Font '%s' is already cached locally at %s", font_def.name, file_path)
            return file_path

        logger.info("Font '%s' not found locally. Initiating download from: %s", font_def.name, font_def.google_fonts_url)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(font_def.google_fonts_url, follow_redirects=True)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    logger.info("Successfully downloaded and cached font '%s' to: %s", font_def.name, file_path)
                    return file_path
                else:
                    raise Exception(f"HTTP download returned status code: {response.status_code}")
        except Exception as exc:
            logger.error("Failed to download font '%s' dynamically: %s. Using fallback path.", font_def.name, exc)
            # If download fails, check if fallback is downloaded or return local path
            if font_def.name.lower() != DEFAULT_FALLBACK.name.lower():
                return await cls.ensure_font_downloaded(DEFAULT_FALLBACK.name)
            
            # Return current path anyway, assuming caller will handle FileNotFoundError or FFmpeg will report it
            return file_path
