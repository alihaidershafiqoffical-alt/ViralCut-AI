"""
app/services/feasibility.py
---------------------------
Intelligent Shorts feasibility algorithm.
Analyzes duration, redundancy/overlap, content density, and topic diversity
to determine if the user's requested number of Shorts is realistic,
preventing repetitive, low-quality clips.
"""

from __future__ import annotations

import logging
import difflib
import re
from typing import List
from pydantic import BaseModel, Field

from app.services.video_analysis import ShortCandidate

logger = logging.getLogger(__name__)


class FeasibilityReport(BaseModel):
    """The feasibility assessment of a Shorts generation request."""
    is_feasible: bool = Field(
        ...,
        description="Whether the requested number of Shorts can be realistically generated with high quality."
    )
    requested_count: int = Field(
        ...,
        description="The original number of Shorts requested by the user."
    )
    recommended_count: int = Field(
        ...,
        description="The recommended number of distinct, high-quality Shorts."
    )
    reasoning: str = Field(
        ...,
        description="Detailed explanation of content boundaries, overlap limitations, or duration constraints."
    )
    selected_shorts: List[ShortCandidate] = Field(
        ...,
        description="The curated list of non-overlapping, diverse, and high-quality Shorts candidates."
    )


class ShortsFeasibilityService:
    """
    Service responsible for checking constraints and calculating the optimal count of Shorts.
    """

    @staticmethod
    def calculate_overlap_ratio(c1: ShortCandidate, c2: ShortCandidate) -> float:
        """Calculates the ratio of overlap between two candidates relative to the smaller clip."""
        start_max = max(c1.start, c2.start)
        end_min = min(c1.end, c2.end)
        
        if start_max >= end_min:
            return 0.0
            
        intersection = end_min - start_max
        dur1 = c1.end - c1.start
        dur2 = c2.end - c2.start
        min_duration = min(dur1, dur2)
        
        return intersection / min_duration if min_duration > 0 else 0.0

    @staticmethod
    def calculate_text_similarity(s1: str, s2: str) -> float:
        """Returns the SequenceMatcher similarity ratio between two strings (0.0 to 1.0)."""
        if not s1 or not s2:
            return 0.0
        return difflib.SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()

    @staticmethod
    def calculate_semantic_similarity(c1: ShortCandidate, c2: ShortCandidate) -> float:
        """
        Calculates semantic similarity based on token overlap of keywords
        and sequence matching of combined metadata (title + summary).
        """
        text1 = f"{c1.title} {c1.summary} {c1.hook}".lower()
        text2 = f"{c2.title} {c2.summary} {c2.hook}".lower()
        
        words1 = set(re.findall(r"\w+", text1))
        words2 = set(re.findall(r"\w+", text2))
        
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "and", "or", "but", "in", "on", "at", "to", "for", "with", "of", "this", "that", "it"}
        words1 -= stop_words
        words2 -= stop_words
        
        if not words1 or not words2:
            return 0.0
            
        jaccard = len(words1 & words2) / len(words1 | words2)
        sequence_sim = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        return (jaccard * 0.6) + (sequence_sim * 0.4)

    @classmethod
    def is_redundant(
        cls,
        c1: ShortCandidate,
        c2: ShortCandidate,
        overlap_threshold: float = 0.20,
        hook_threshold: float = 0.50,
        title_threshold: float = 0.60,
        semantic_threshold: float = 0.45
    ) -> bool:
        """
        Checks if candidate c1 is too redundant/similar to candidate c2.
        Compares timestamps, hooks, titles (topics), and semantic representations.
        """
        # 1. Timestamp overlap check
        overlap = cls.calculate_overlap_ratio(c1, c2)
        if overlap > overlap_threshold:
            logger.debug("Redundancy rejected (overlap=%.2f): [%.1fs-%.1fs] vs [%.1fs-%.1fs]", overlap, c1.start, c1.end, c2.start, c2.end)
            return True

        # 2. Hook similarity check
        hook_sim = cls.calculate_text_similarity(c1.hook, c2.hook)
        if hook_sim > hook_threshold:
            logger.debug("Redundancy rejected (hook similarity=%.2f): '%s' vs '%s'", hook_sim, c1.hook, c2.hook)
            return True

        # 3. Topic/Title similarity check
        title_sim = cls.calculate_text_similarity(c1.title, c2.title)
        if title_sim > title_threshold:
            logger.debug("Redundancy rejected (title similarity=%.2f): '%s' vs '%s'", title_sim, c1.title, c2.title)
            return True

        # 4. Semantic similarity check (combined words/meaning)
        semantic_sim = cls.calculate_semantic_similarity(c1, c2)
        if semantic_sim > semantic_threshold:
            logger.debug("Redundancy rejected (semantic similarity=%.2f)", semantic_sim)
            return True

        return False

    @classmethod
    def check_feasibility(
        cls,
        video_duration: float,
        requested_count: int,
        target_duration: float,
        candidates: List[ShortCandidate],
        overlap_threshold: float = 0.20
    ) -> FeasibilityReport:
        """
        Evaluates candidate segments against time and overlap constraints.

        Parameters
        ----------
        video_duration : float
            Total duration of original video in seconds.
        requested_count : int
            Number of shorts requested by the user.
        target_duration : float
            Target duration of each short in seconds.
        candidates : List[ShortCandidate]
            All potential clip candidates returned by the model.
        overlap_threshold : float, optional
            Percentage overlap allowed between clips before considering them redundant.

        Returns
        -------
        FeasibilityReport
            The curated report and recommendation details.
        """
        logger.info(
            "Running feasibility check: video_dur=%.2f, requested=%d, target_dur=%.2f, candidates=%d",
            video_duration, requested_count, target_duration, len(candidates)
        )

        # 1. Sort candidates by virality score descending
        sorted_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)
        
        selected: List[ShortCandidate] = []

        # 2. Greedy selection to eliminate overlapping/redundant segments (quality priority)
        for cand in sorted_candidates:
            has_conflict = False
            for sel in selected:
                # Compare all dimensions of similarity (timestamp, hook, topic/title, semantic)
                if cls.is_redundant(cand, sel, overlap_threshold=overlap_threshold):
                    has_conflict = True
                    break
            
            if not has_conflict:
                selected.append(cand)

        # 3. Calculate theoretical limit based on video duration
        # Example: 120s video with 60s target -> max 2 clips.
        theoretical_limit = max(1, int(video_duration // target_duration))

        # Recommended count is constrained by unique content and theoretical duration fit
        max_possible_clips = min(len(selected), theoretical_limit)
        
        if requested_count <= max_possible_clips:
            is_feasible = True
            recommended_count = requested_count
            selected = selected[:recommended_count]
            reasoning = (
                f"Your request for {requested_count} Shorts is feasible. "
                f"We found {recommended_count} highly unique and engaging clips."
            )
        else:
            is_feasible = False
            recommended_count = max_possible_clips
            selected = selected[:recommended_count]
            if len(selected) < theoretical_limit:
                reasoning = (
                    f"We found only {len(selected)} unique hook points with sufficient content. "
                    f"Generating {requested_count} Shorts would cause repetitive segments. "
                    f"We recommend producing {recommended_count} high-quality Shorts instead."
                )
            else:
                reasoning = (
                    f"A video of {video_duration:.1f}s is too short to fit {requested_count} distinct "
                    f"clips of target duration {target_duration}s (max non-overlapping clips possible is {theoretical_limit}). "
                    f"We recommend {recommended_count} Shorts to prioritize quality."
                )

        logger.info(
            "Feasibility result: feasible=%s, recommended=%d (requested=%d)",
            is_feasible, recommended_count, requested_count
        )

        return FeasibilityReport(
            is_feasible=is_feasible,
            requested_count=requested_count,
            recommended_count=recommended_count,
            reasoning=reasoning,
            selected_shorts=selected
        )
