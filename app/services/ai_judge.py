"""
app/services/ai_judge.py
------------------------
Service for "Pass 2" AI Judgment.
Evaluates candidates discovered in Pass 1 specifically for Hook Strength,
Context Completeness, and overall potential.
"""

from __future__ import annotations

import logging
from typing import List
from pydantic import BaseModel, Field

from app.services.video_analysis import ShortCandidate
from app.services.gemini import GeminiService

logger = logging.getLogger(__name__)


class JudgedScores(BaseModel):
    """The scores assigned to a specific candidate by the AI Judge."""
    candidate_index: int = Field(..., description="The index of the candidate being scored.")
    category: str = Field(..., description="Must be one of: Controversial, Educational, Funny, Surprising, Emotional, Insight, Story, Business, Quote, Question/Answer")
    hook_strength: int = Field(..., description="Hook strength (0-10). Check for curiosity, surprising statement, question, bold claim, emotional trigger.")
    curiosity: int = Field(..., description="Curiosity generation (0-10).")
    emotional_impact: int = Field(..., description="Emotional impact (0-10).")
    information_value: int = Field(..., description="Information value (0-10).")
    context_completeness: int = Field(..., description="Standalone context / Context Completeness (0-10). Does it make sense if you haven't seen the rest of the video?")
    story_completion: int = Field(..., description="Story completion (0-10).")
    shareability: int = Field(..., description="Shareability (0-10).")
    retention_potential: int = Field(..., description="Retention potential (0-10).")
    context_dependency: int = Field(..., description="Context dependency (0-10) [High is bad, means it needs too much context].")
    repetition: int = Field(..., description="Repetition (0-10) [High is bad].")
    weak_opening: int = Field(..., description="Weak opening (0-10) [High is bad].")


class AIJudgeResult(BaseModel):
    """The structured output schema representing the AI Judge's evaluation of all candidates."""
    judgments: List[JudgedScores] = Field(..., description="List of evaluated scores for the candidates.")


SYSTEM_PROMPT = """You are an expert AI video judge. Your sole responsibility is to evaluate a batch of short-form video clip candidates.
For each candidate, you will strictly evaluate its Hook and Context Completeness.

CRITICAL INSTRUCTIONS FOR HOOK:
The first 1-3 seconds are the most important. Evaluate the "hook" text carefully.
Ask yourself:
- Does it generate curiosity?
- Is it a surprising statement?
- Is it a question?
- Is it a bold claim?
- Is there an emotional trigger?
- Does it give the viewer a reason to keep watching?
Example of a weak hook: "Today we're going to talk about productivity."
Example of a strong hook: "You're probably wasting two hours every day without realizing it."
Prioritize strong hooks heavily in your scoring.

CRITICAL INSTRUCTIONS FOR CONTEXT COMPLETENESS (context_completeness):
If a person has NEVER seen the rest of the video, will this clip make complete sense on its own?
If the clip starts with "And that's why he..." and the viewer doesn't know who "he" is or what he did, this is a FAIL. Context dependency must be scored HIGH (which is bad) and context_completeness scored LOW.
If the clip is entirely self-contained, score context_completeness HIGH and context_dependency LOW.

CRITICAL INSTRUCTIONS FOR CATEGORIZATION (category):
You must assign EXACTLY ONE of the following categories to each clip based on its core appeal:
1. Controversial
2. Educational
3. Funny
4. Surprising
5. Emotional
6. Insight
7. Story
8. Business
9. Quote
10. Question/Answer

Score all variables from 0 to 10.
"""

USER_PROMPT_TEMPLATE = """Evaluate the following list of Short Candidates.

{candidates_list}

Return the evaluated scores for each candidate matching their index.
"""


class AIJudgeService:
    """
    Service responsible for invoking the Gemini API to judge and score candidates
    discovered in Pass 1.
    """

    @classmethod
    async def evaluate_candidates(
        cls,
        candidates: List[ShortCandidate]
    ) -> List[ShortCandidate]:
        """
        Runs the Gemini Judge pipeline on a list of candidates to refine their scores.
        """
        if not candidates:
            return []

        logger.info(f"AI Judge evaluating {len(candidates)} candidates.")

        # Format candidates for the prompt
        formatted_cands: List[str] = []
        for idx, cand in enumerate(candidates):
            formatted_cands.append(
                f"--- Candidate {idx} ---\n"
                f"Title: {cand.title}\n"
                f"Hook (First sentence): {cand.hook}\n"
                f"Summary: {cand.summary}\n"
            )
            
        candidates_str = "\n".join(formatted_cands)
        user_prompt = USER_PROMPT_TEMPLATE.format(candidates_list=candidates_str)

        # Call Gemini Service with structured schema
        try:
            raw_result: AIJudgeResult = await GeminiService.generate_content(
                prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT,
                response_schema=AIJudgeResult
            )

            # Map the results back to the candidates
            judgments_map = {j.candidate_index: j for j in raw_result.judgments}

            for idx, cand in enumerate(candidates):
                judgment = judgments_map.get(idx)
                if judgment:
                    cand.category = judgment.category
                    cand.hook_strength = judgment.hook_strength
                    cand.curiosity = judgment.curiosity
                    cand.emotional_impact = judgment.emotional_impact
                    cand.information_value = judgment.information_value
                    cand.context_completeness = judgment.context_completeness
                    cand.story_completion = judgment.story_completion
                    cand.shareability = judgment.shareability
                    cand.retention_potential = judgment.retention_potential
                    cand.context_dependency = judgment.context_dependency
                    cand.repetition = judgment.repetition
                    cand.weak_opening = judgment.weak_opening
                else:
                    logger.warning(f"AI Judge missed candidate index {idx}.")

            logger.info("AI Judge evaluation complete.")
        except Exception as exc:
            logger.warning("AI Judge pass skipped (%s). Using existing candidate scores.", exc)

        return candidates
