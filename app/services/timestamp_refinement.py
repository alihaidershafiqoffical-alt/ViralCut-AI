"""
app/services/timestamp_refinement.py
------------------------------------
Service for aligning AI-generated timestamp boundaries for Shorts
to exact word-level timings using Faster-Whisper's output.
"""

from __future__ import annotations

import logging
from typing import List

from app.services.video_analysis import ShortCandidate
from app.services.transcription import TranscriptionResult

logger = logging.getLogger(__name__)


class TimestampRefinementService:
    """
    Refines estimated AI start/end timestamps to match exact word boundaries,
    preventing mid-syllable cutoffs.
    """

    @classmethod
    def refine_timestamps(
        cls,
        candidates: List[ShortCandidate],
        transcription_result: TranscriptionResult,
        video_duration: float,
        buffer_seconds: float = 0.1
    ) -> List[ShortCandidate]:
        """
        Aligns the start and end of each candidate to the nearest word boundaries.
        
        Parameters
        ----------
        candidates : List[ShortCandidate]
            The list of Short candidates to refine.
        transcription_result : TranscriptionResult
            The original transcription data containing word-level timestamps.
        video_duration : float
            Total duration of the video.
        buffer_seconds : float
            Small padding added to the start/end to avoid clipping breath or speech.
            
        Returns
        -------
        List[ShortCandidate]
            The list of candidates with refined timestamps.
        """
        words = transcription_result.words
        if not words:
            logger.warning("No word-level timestamps found. Skipping timestamp refinement.")
            return candidates

        logger.info(f"Refining timestamps for {len(candidates)} candidates.")

        for cand in candidates:
            # --- Start Refinement ---
            # Find the word closest to cand.start
            closest_start_word = min(words, key=lambda w: abs(w.start - cand.start))
            
            # Snap and apply buffer
            refined_start = closest_start_word.start - buffer_seconds
            
            # Ensure it doesn't go below 0
            cand.start = max(0.0, round(refined_start, 2))

            # --- End Refinement ---
            # Find the word closest to cand.end
            closest_end_word = min(words, key=lambda w: abs(w.end - cand.end))
            
            # Snap and apply buffer
            refined_end = closest_end_word.end + buffer_seconds
            
            # Ensure it doesn't exceed video duration
            cand.end = min(video_duration, round(refined_end, 2))

            # Safety check: if logic failed and start >= end, revert to original duration approximation
            if cand.start >= cand.end:
                logger.warning(f"Refinement failed for candidate '{cand.title}', reverting to AI estimates.")
                # We won't revert completely, just ensure at least a 3 second gap
                cand.end = min(video_duration, cand.start + 3.0)

        logger.info("Timestamp refinement complete.")
        return candidates
