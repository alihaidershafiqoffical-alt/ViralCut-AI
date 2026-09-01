"""
app/services/captions.py
------------------------
Speech caption generator using Whisper word-level timestamps.
Groups words into timed visual caption phrases (1-6 words) based on word count constraints,
terminal punctuation boundaries, maximum display durations, and inter-word silence gaps.
"""

from __future__ import annotations

import logging
from typing import List
from pydantic import BaseModel, Field

from app.services.transcription import WordSegment

logger = logging.getLogger(__name__)


class CaptionGroup(BaseModel):
    """A single timed caption phrase containing grouped words."""
    text: str = Field(..., description="The combined text of the words in this caption group.")
    start: float = Field(..., description="Start timestamp of the first word in the group.")
    end: float = Field(..., description="End timestamp of the last word in the group.")
    words: List[WordSegment] = Field(..., description="Individual word-level metadata segments for this group.")


class CaptionGeneratorService:
    """
    Groups words dynamically into brief visual caption segments for video overlay.
    """

    @staticmethod
    def generate_captions(
        words: List[WordSegment],
        max_words: int = 6,
        max_duration: float = 2.5,
        max_gap: float = 1.0
    ) -> List[CaptionGroup]:
        """
        Groups flat word timestamps into timed caption segments suitable for Shorts overlays.

        Parameters
        ----------
        words : List[WordSegment]
            Flat list of transcribed words with timestamps.
        max_words : int, optional
            Maximum words permitted in a single caption group. Defaults to 6.
        max_duration : int, optional
            Maximum duration in seconds for a single caption group. Defaults to 2.5.
        max_gap : float, optional
            Silence threshold in seconds between words that triggers a segment break. Defaults to 1.0.

        Returns
        -------
        List[CaptionGroup]
            A list of timed caption groups.
        """
        if not words:
            return []

        # Ensure correct temporal ordering
        sorted_words = sorted(words, key=lambda w: w.start)

        caption_groups: List[CaptionGroup] = []
        current_words: List[WordSegment] = []

        def finalize_group() -> None:
            if current_words:
                text = " ".join(w.word for w in current_words)
                caption_groups.append(
                    CaptionGroup(
                        text=text,
                        start=current_words[0].start,
                        end=current_words[-1].end,
                        words=list(current_words)
                    )
                )
                current_words.clear()

        for word in sorted_words:
            # First word in group: append and proceed
            if not current_words:
                current_words.append(word)
                continue

            prev_word = current_words[-1]

            # 1. Word count constraint check (1-6 words)
            limit_reached = len(current_words) >= max_words

            # 2. Silence/gap threshold check (natural pause in speech)
            gap_occurred = (word.start - prev_word.end) > max_gap

            # 3. Maximum display duration check
            duration_exceeded = (word.end - current_words[0].start) > max_duration

            # 4. Punctuation break check (comma, period, question, exclamation, colon, semicolon)
            # We strip trailing quotes to examine terminal characters
            clean_prev = prev_word.word.strip().rstrip('"\'')
            has_punctuation_break = False
            if clean_prev:
                last_char = clean_prev[-1]
                if last_char in {".", "?", "!", ",", ";", ":"}:
                    has_punctuation_break = True

            # If any constraint triggers, finalize current group before adding new word
            if limit_reached or gap_occurred or duration_exceeded or has_punctuation_break:
                finalize_group()

            current_words.append(word)

        # Finalize the last group
        finalize_group()

        logger.info("Generated %d caption groups from %d words.", len(caption_groups), len(words))
        return caption_groups
