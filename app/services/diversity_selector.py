"""
app/services/diversity_selector.py
----------------------------------
Final AI selection pass to ensure maximum diversity in categories and
strict semantic deduplication of concepts across the final candidates.
"""

from __future__ import annotations

import logging
from typing import List
from pydantic import BaseModel, Field

from app.services.video_analysis import ShortCandidate
from app.services.gemini import GeminiService

logger = logging.getLogger(__name__)


class SelectedShortIndexes(BaseModel):
    """The indexes of the candidates selected by the AI Diversity Selector."""
    selected_indexes: List[int] = Field(..., description="The list of indexes for the chosen candidates.")


SYSTEM_PROMPT = """You are an expert AI Editor and Content Strategist. Your final job is to select the best short-form videos from a list of highly-ranked candidates.

CRITICAL INSTRUCTIONS:
1. SEMANTIC DEDUPLICATION: You must aggressively reject duplicates. If two candidates teach the EXACT same concept, tell the same story, or share the same meaning (even if their words or timestamps are different), you must ONLY select the better one. Do not include conceptual duplicates.
2. CATEGORY DIVERSITY: Ensure the final selection has a healthy mix of categories. Do not select 5 "Educational" clips if there are high-quality "Funny", "Story", or "Controversial" clips available. Maximize variety.
3. SELECT EXACT COUNT: You must select exactly the requested number of clips (if possible, without violating the deduplication rule).
4. Do not select a candidate if its summary implies it requires heavy context from outside the clip.

You will be provided with a list of ranked candidates (0 is the highest ranked mathematically).
Return ONLY the indexes of the selected candidates in your structured output.
"""

USER_PROMPT_TEMPLATE = """Please select exactly {target_count} candidates from the list below.

### RANKED CANDIDATES:
{candidates_list}

Return the selected_indexes.
"""


class DiversitySelectorService:
    """
    Service responsible for final AI-driven selection to enforce diversity
    and conceptual deduplication.
    """

    @classmethod
    async def select_diverse_shorts(
        cls,
        candidates: List[ShortCandidate],
        requested_count: int,
        video_duration: float
    ) -> List[ShortCandidate]:
        """
        Executes the final Gemini selection pass.

        Parameters
        ----------
        candidates : List[ShortCandidate]
            The list of mathematically ranked candidates (highest first).
        requested_count : int
            The number of shorts requested by the user.
        video_duration : float
            Total video duration (used to cap theoretical maximum).

        Returns
        -------
        List[ShortCandidate]
            The final deduplicated and diverse selected shorts.
        """
        if not candidates:
            return []
            
        # Theoretical limit: A 5-minute video shouldn't produce 20 shorts.
        # Max ~1 short per 1 minute of video to ensure quality.
        theoretical_max = max(1, int(video_duration / 60))
        target_count = min(requested_count, theoretical_max)
        
        # If we have fewer candidates than the target, adjust the target
        target_count = min(target_count, len(candidates))

        logger.info(
            "Diversity Selector targeting %d shorts (Requested: %d, Theoretical Max: %d) from %d top candidates.",
            target_count, requested_count, theoretical_max, len(candidates)
        )

        # We only need to send the top N candidates to Gemini to save tokens.
        # Sending roughly 2.5x the requested count gives it enough pool to choose from.
        pool_size = min(len(candidates), max(10, target_count * 3))
        candidate_pool = candidates[:pool_size]

        formatted_cands: List[str] = []
        for idx, cand in enumerate(candidate_pool):
            formatted_cands.append(
                f"--- Index {idx} ---\n"
                f"Title: {cand.title}\n"
                f"Category: {cand.category}\n"
                f"Summary: {cand.summary}\n"
                f"Hook: {cand.hook}\n"
                f"Mathematical Score: {cand.score}/100\n"
            )

        candidates_str = "\n".join(formatted_cands)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            target_count=target_count,
            candidates_list=candidates_str
        )

        try:
            raw_result: SelectedShortIndexes = await GeminiService.generate_content(
                prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT,
                response_schema=SelectedShortIndexes
            )

            selected_indexes = raw_result.selected_indexes
            logger.info("Diversity Selector chose indexes: %s", selected_indexes)

            # Map indexes back to candidates
            final_selection: List[ShortCandidate] = []
            for idx in selected_indexes:
                if 0 <= idx < len(candidate_pool):
                    final_selection.append(candidate_pool[idx])

            # Fallback if Gemini returned nothing or too few due to aggressive deduplication
            if not final_selection:
                logger.warning("Diversity Selector returned empty list. Falling back to top mathematical candidates.")
                return candidate_pool[:target_count]

            return final_selection

        except Exception as exc:
            logger.error("Diversity Selector failed: %s. Falling back to top mathematical candidates.", exc)
            return candidate_pool[:target_count]
