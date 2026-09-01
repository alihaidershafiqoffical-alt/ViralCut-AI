"""
app/services/ranking.py
-----------------------
Shorts ranking and scoring algorithm based on user's exact formula:
Final Score = Hook Strength + Curiosity + Emotional Impact + Information Value + Standalone Context + Story Completion + Shareability + Retention Potential - Context Dependency - Repetition - Weak Opening
"""

from __future__ import annotations

import logging
from typing import List

from app.services.video_analysis import ShortCandidate

logger = logging.getLogger(__name__)


class ShortsRankingService:
    """
    Computes a scoring algorithm to rank Shorts candidates dynamically.
    """

    @classmethod
    def rank_candidates(
        cls,
        candidates: List[ShortCandidate]
    ) -> List[ShortCandidate]:
        """
        Scores all candidates using the explicit requested formula and returns a sorted list
        of final ShortCandidate objects, ranked highest to lowest score.
        """
        for cand in candidates:
            # Positive factors (each 0-10, max +80)
            positive_score = (
                cand.hook_strength +
                cand.curiosity +
                cand.emotional_impact +
                cand.information_value +
                cand.context_completeness +
                cand.story_completion +
                cand.shareability +
                cand.retention_potential
            )
            
            # Negative factors (each 0-10, max -30)
            negative_score = (
                cand.context_dependency +
                cand.repetition +
                cand.weak_opening
            )
            
            # Raw score theoretical range: -30 to 80
            # To normalize to 0-100%, we shift by 30 (range 0 to 110)
            # Then divide by 110 and multiply by 100.
            raw_score = positive_score - negative_score
            shifted = raw_score + 30
            normalized = (shifted / 110.0) * 100.0
            
            final_score = int(round(normalized))
            # Ensure score fits within 0-100
            cand.score = max(0, min(100, final_score))
            
        # Sort descending by score
        ranked_list = sorted(candidates, key=lambda x: x.score, reverse=True)
        return ranked_list
