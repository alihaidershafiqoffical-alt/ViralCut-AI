r"""
app/services/caption_rendering.py
---------------------------------
FFmpeg-compatible and client-side animated caption rendering service.
Converts structured CaptionGroups and CaptionStyles into fully-styled, frame-accurate
Advanced Sub Station Alpha (.ass) subtitle files with karaoke-style highlighting (\kf)
and active-word scaling pops.
"""

from __future__ import annotations

import os
import logging
from typing import List
from pydantic import BaseModel, Field

from app.services.transcription import WordSegment
from app.services.captions import CaptionGroup
from app.services.caption_styling import CaptionStyle

logger = logging.getLogger(__name__)


class CaptionRenderingService:
    """
    Translates caption groupings and styling definitions into visual rendering formats.
    """

    @staticmethod
    def hex_to_ass_color(hex_str: str, alpha: float = 0.0) -> str:
        """
        Converts CSS HEX color strings to ASS format: &HAABBGGRR.
        Opaque alpha is &H00, fully transparent is &HFF.
        """
        clean = hex_str.strip().lstrip("#")
        
        # Handle shorthand hex like #FFF
        if len(clean) == 3:
            clean = "".join(c * 2 for c in clean)
            
        if len(clean) == 8:
            # RGBA
            r, g, b, a = clean[0:2], clean[2:4], clean[4:6], clean[6:8]
            # Invert alpha: ASS 00 is fully opaque, FF is fully transparent
            ass_a = f"{255 - int(a, 16):02X}"
            return f"&H{ass_a}{b}{g}{r}"
            
        if len(clean) == 6:
            # RGB
            r, g, b = clean[0:2], clean[2:4], clean[4:6]
            ass_a = f"{int(alpha * 255):02X}"
            return f"&H{ass_a}{b}{g}{r}"

        # Fallback to white opaque
        return f"&H00FFFFFF"

    @classmethod
    def format_ass_time(cls, seconds: float) -> str:
        """Formats seconds into ASS timestamp format: H:MM:SS.cs (centiseconds)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int(round((seconds % 1) * 100))
        
        if centiseconds >= 100:
            secs += 1
            centiseconds -= 100
        if secs >= 60:
            minutes += 1
            secs -= 60
        if minutes >= 60:
            hours += 1
            minutes -= 60
            
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    @classmethod
    def generate_ass_subtitle(
        cls,
        caption_groups: List[CaptionGroup],
        style: CaptionStyle,
        video_width: int = 1080,
        video_height: int = 1920
    ) -> str:
        """
        Generates the raw ASS script content representing the styled timed subtitles.
        """
        # Determine ASS colors
        primary_color = cls.hex_to_ass_color(style.font_color, alpha=0.0)
        
        # Highlight/Secondary color maps to karaoke active highlight
        sec_color = cls.hex_to_ass_color(style.highlight_color or "#FFFF00")
        
        outline_color = cls.hex_to_ass_color(style.stroke_color or "#000000")
        back_color = cls.hex_to_ass_color(style.background_color or "rgba(0,0,0,0.5)", alpha=0.5)

        bold_val = -1 if style.font_weight in {"bold", "900"} else 0
        outline_val = style.stroke_width if style.stroke_width is not None else 1.5
        shadow_val = style.shadow_blur if style.shadow_blur is not None else 1.0

        # Calculate vertical margin based on position_y_pct (lower-third default)
        margin_v = int(round(video_height * (1.0 - style.position_y_pct / 100.0)))

        # 1. Script Info & Styles Headers
        lines = [
            "[Script Info]",
            "Title: Styled Timed Captions",
            "ScriptType: v4.00+",
            "Collisions: Normal",
            f"PlayResX: {video_width}",
            f"PlayResY: {video_height}",
            "Timer: 100.0000",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{style.font_family},{style.font_size},{primary_color},{sec_color},{outline_color},{back_color},{bold_val},0,0,0,100,100,0,0,1,{outline_val},{shadow_val},2,15,15,{margin_v},1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        # 2. Events Dialogues (Karaoke timing mapping)
        for group in caption_groups:
            start_str = cls.format_ass_time(group.start)
            end_str = cls.format_ass_time(group.end)
            
            # Format text line
            dialogue_text = ""
            prev_end = group.start

            for word in group.words:
                # Calculate duration of word in centiseconds (100cs = 1s)
                dur_cs = max(1, int(round((word.end - word.start) * 100)))
                
                # Check for silent gap before this word
                gap_cs = int(round((word.start - prev_end) * 100))
                if gap_cs > 0:
                    dialogue_text += f"{{\\kf{gap_cs}}}"
                
                # Karaoke dynamic tag: {\kf<duration>}<word>
                # Active scale pops can be simulated with font-size changes or standard karaoke highlighting
                # For Karaoke style: we color transition words dynamically.
                dialogue_text += f"{{\\kf{dur_cs}}}{word.word} "
                prev_end = word.end

            lines.append(
                f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{dialogue_text.strip()}"
            )

        return "\n".join(lines)

    @classmethod
    def save_ass_file(
        cls,
        caption_groups: List[CaptionGroup],
        style: CaptionStyle,
        output_path: str
    ) -> str:
        """Generates and writes an ASS file to the output path on disk."""
        content = cls.generate_ass_subtitle(caption_groups, style)
        
        # Ensure parent directory exists
        parent = os.path.dirname(output_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info("Successfully rendered and saved ASS subtitles file: %s", output_path)
        return output_path

    @classmethod
    def generate_html_overlay_data(
        cls,
        caption_groups: List[CaptionGroup],
        style: CaptionStyle
    ) -> List[dict]:
        """
        Generates client-side friendly CSS/HTML overlay styling blocks for caption rendering in browser players.
        Each word contains structured animation transition metadata and timings.
        """
        overlay_groups = []
        
        # Base container styles
        base_container_styles = {
            "font-family": style.font_family,
            "font-size": f"{style.font_size}px",
            "font-weight": style.font_weight,
            "color": style.font_color,
            "top": f"{style.position_y_pct}%",
            "text-align": "center",
            "position": "absolute",
            "width": "100%"
        }
        
        # Apply optional box capsule styles
        if style.background_color:
            base_container_styles["background-color"] = style.background_color
        if style.background_padding:
            base_container_styles["padding"] = style.background_padding
        if style.background_radius:
            base_container_styles["border-radius"] = style.background_radius

        # Text stroke / dropshadows
        text_shadows = []
        if style.stroke_color and style.stroke_width:
            w = style.stroke_width
            c = style.stroke_color
            text_shadows.append(f"-{w}px -{w}px 0 {c}")
            text_shadows.append(f"{w}px -{w}px 0 {c}")
            text_shadows.append(f"-{w}px {w}px 0 {c}")
            text_shadows.append(f"{w}px {w}px 0 {c}")
            
        if style.shadow_color:
            sx = style.shadow_offset_x or 2.0
            sy = style.shadow_offset_y or 2.0
            sb = style.shadow_blur or 3.0
            sc = style.shadow_color
            text_shadows.append(f"{sx}px {sy}px {sb}px {sc}")
            
        if text_shadows:
            base_container_styles["text-shadow"] = ", ".join(text_shadows)

        for group in caption_groups:
            words_data = []
            for w in group.words:
                word_style = {
                    "transition": "all 0.15s ease-in-out",
                    "display": "inline-block"
                }
                
                # Active highlight override rules
                active_style = {}
                if style.highlight_color:
                    active_style["color"] = style.highlight_color
                if style.highlight_scale and style.highlight_scale > 1.0:
                    active_style["transform"] = f"scale({style.highlight_scale})"
                    
                words_data.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "probability": w.probability,
                    "normal_style": word_style,
                    "active_style": active_style
                })

            overlay_groups.append({
                "text": group.text,
                "start": group.start,
                "end": group.end,
                "container_style": base_container_styles,
                "animation_type": style.animation_type,
                "words": words_data
            })
            
        return overlay_groups
