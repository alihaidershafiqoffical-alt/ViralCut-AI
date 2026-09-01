"""
app/services/caption_styling.py
-------------------------------
Caption styling configuration service.
Defines Pydantic structures and a style registry for caption presets:
Classic, Bold, Minimal, Modern, Highlight, and Karaoke.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CaptionStyle(BaseModel):
    """Configuration structure defining caption appearance, positioning, and animation behavior."""
    name: str = Field(..., description="Unique identifier name of the style preset.")
    font_family: str = Field(..., description="Font family name (e.g. Inter, Outfit, Montserrat, Impact).")
    font_size: float = Field(..., description="Base font size in pixels or relative scale.")
    font_weight: str = Field(..., description="Font weight: normal, bold, 900.")
    font_color: str = Field(..., description="Primary text color in HEX or RGBA (e.g. #FFFFFF).")
    position_y_pct: float = Field(default=80.0, description="Vertical alignment position percentage from top (0.0 to 100.0).")
    
    # Background Box Styling
    background_color: Optional[str] = Field(default=None, description="Optional capsule box background color (HEX or RGBA).")
    background_padding: Optional[str] = Field(default=None, description="CSS padding format (e.g. '6px 12px').")
    background_radius: Optional[str] = Field(default=None, description="CSS border radius format (e.g. '8px').")
    
    # Text stroke / outline (highly compatible with video overlays)
    stroke_color: Optional[str] = Field(default=None, description="HEX/RGBA color of text outline.")
    stroke_width: Optional[float] = Field(default=None, description="Text outline width in pixels.")
    
    # Shadows
    shadow_color: Optional[str] = Field(default=None, description="HEX/RGBA color of text drop shadow.")
    shadow_offset_x: Optional[float] = Field(default=None, description="Horizontal shadow offset in pixels.")
    shadow_offset_y: Optional[float] = Field(default=None, description="Vertical shadow offset in pixels.")
    shadow_blur: Optional[float] = Field(default=None, description="Drop shadow blur radius in pixels.")
    
    # Active/Word-level Highlight behaviour
    highlight_color: Optional[str] = Field(default=None, description="Vibrant color for active spoken words (HEX/RGBA).")
    highlight_scale: Optional[float] = Field(default=1.0, description="Active word scaling multiplier (e.g. 1.15 for pop).")
    
    # Text entry / transition animation
    animation_type: str = Field(default="none", description="Transition style: none, pop, fade, slide, bounce.")


# ---------------------------------------------------------------------------
# Presets Styles Registry
# ---------------------------------------------------------------------------

CLASSIC_STYLE = CaptionStyle(
    name="Classic",
    font_family="Arial",
    font_size=40.0,
    font_weight="bold",
    font_color="#FFFFFF",
    position_y_pct=80.0,
    stroke_color="#000000",
    stroke_width=2.5,
    shadow_color="rgba(0, 0, 0, 0.5)",
    shadow_offset_x=2.0,
    shadow_offset_y=2.0,
    shadow_blur=3.0,
    animation_type="none"
)

BOLD_STYLE = CaptionStyle(
    name="Bold",
    font_family="Montserrat",
    font_size=48.0,
    font_weight="900",
    font_color="#FFFFFF",
    position_y_pct=75.0,
    stroke_color="#000000",
    stroke_width=3.5,
    highlight_color="#FFFF00",  # Vivid yellow highlight
    highlight_scale=1.1,
    animation_type="pop"         # Pop transition active
)

MINIMAL_STYLE = CaptionStyle(
    name="Minimal",
    font_family="Inter",
    font_size=32.0,
    font_weight="normal",
    font_color="#EEEEEE",
    position_y_pct=85.0,
    animation_type="fade"
)

MODERN_STYLE = CaptionStyle(
    name="Modern",
    font_family="Outfit",
    font_size=38.0,
    font_weight="bold",
    font_color="#FFFFFF",
    position_y_pct=78.0,
    background_color="rgba(0, 0, 0, 0.7)",  # Rounded capsule box
    background_padding="8px 16px",
    background_radius="12px",
    animation_type="slide"
)

HIGHLIGHT_STYLE = CaptionStyle(
    name="Highlight",
    font_family="Montserrat",
    font_size=44.0,
    font_weight="bold",
    font_color="#FFFFFF",
    position_y_pct=75.0,
    stroke_color="#111111",
    stroke_width=2.0,
    highlight_color="#FF4500",  # Vivid orange highlight color
    animation_type="bounce"
)

KARAOKE_STYLE = CaptionStyle(
    name="Karaoke",
    font_family="Outfit",
    font_size=42.0,
    font_weight="bold",
    font_color="#AAAAAA",       # Inactive words are dimmed grey
    position_y_pct=75.0,
    stroke_color="#000000",
    stroke_width=1.5,
    highlight_color="#00FF00",  # Active spoken word is neon green
    highlight_scale=1.15,       # Scales active word to emphasize speech rhythm
    animation_type="pop"
)

STYLE_REGISTRY: Dict[str, CaptionStyle] = {
    "classic": CLASSIC_STYLE,
    "bold": BOLD_STYLE,
    "minimal": MINIMAL_STYLE,
    "modern": MODERN_STYLE,
    "highlight": HIGHLIGHT_STYLE,
    "karaoke": KARAOKE_STYLE
}


class CaptionStylingService:
    """
    Registry management service for caption style configurations.
    """

    @classmethod
    def get_style(cls, name: str) -> CaptionStyle:
        """Retrieves a specific CaptionStyle configuration by its name case-insensitively."""
        key = name.lower().strip()
        if key not in STYLE_REGISTRY:
            raise KeyError(f"Caption style '{name}' is not found in registry. Available: {list(STYLE_REGISTRY.keys())}")
        return STYLE_REGISTRY[key]

    @classmethod
    def list_styles(cls) -> List[CaptionStyle]:
        """Lists all registered style presets."""
        return list(STYLE_REGISTRY.values())
