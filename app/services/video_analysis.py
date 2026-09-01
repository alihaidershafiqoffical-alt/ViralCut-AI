"""
app/services/video_analysis.py
------------------------------
Service for analyzing timestamped transcripts using Gemini
to detect highly engaging and viral segments for short-form video generation.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from app.services.transcription import TranscriptionResult
from app.services.gemini import GeminiService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Schemas for Gemini Structured Output
# ---------------------------------------------------------------------------

class AnalysisBlock(BaseModel):
    """Global video analysis including key topics and summary."""
    topics: List[str] = Field(..., description="Key topics and themes discussed in the video.")
    summary: str = Field(..., description="Overall high-level summary of the video content.")


class ShortCandidate(BaseModel):
    """A candidate viral short-form clip identified by Gemini."""
    start: float = Field(..., description="Start timestamp of the clip in seconds.")
    end: float = Field(..., description="End timestamp of the clip in seconds.")
    title: str = Field(..., description="The absolute best, most catchy title for the Short.")
    title_score: int = Field(default=0, description="The internal score (0-100) of the selected title.")
    alternative_titles: List[str] = Field(default_factory=list, description="A list of 2 alternative catchy titles for A/B testing.")
    category: str = Field(default="Uncategorized", description="Category of the Short (e.g., Educational, Funny).")
    hook: str = Field(..., description="The attention-grabbing opening sentence or phrase (the hook).")
    summary: str = Field(..., description="A short, catchy summary of the clip content.")
    score: int = Field(default=0, description="Calculated final score from 0 to 100 (initially 0, filled by ranking service).")
    hook_strength: int = Field(default=8, description="Hook strength (0-10).")
    curiosity: int = Field(default=8, description="Curiosity generation (0-10).")
    emotional_impact: int = Field(default=7, description="Emotional impact (0-10).")
    information_value: int = Field(default=8, description="Information value (0-10).")
    context_completeness: int = Field(default=8, description="Context completeness (0-10).")
    story_completion: int = Field(default=8, description="Story completion (0-10).")
    shareability: int = Field(default=8, description="Shareability (0-10).")
    retention_potential: int = Field(default=8, description="Retention potential (0-10).")
    context_dependency: int = Field(default=2, description="Context dependency (0-10) [High is bad].")
    repetition: int = Field(default=2, description="Repetition (0-10) [High is bad].")
    weak_opening: int = Field(default=2, description="Weak opening (0-10) [High is bad].")


class VideoAnalysisResult(BaseModel):
    """The structured output schema representing the Gemini Shorts selection response."""
    analysis: AnalysisBlock = Field(..., description="Global transcript analysis block.")
    shorts: List[ShortCandidate] = Field(..., description="List of identified Shorts candidates.")


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert AI video editor and viral growth strategist specializing in converting long-form videos into high-performing short-form clips (Shorts, Reels, TikToks).

Your goal is to analyze the provided video transcript and identify the most viral, engaging, and standalone segments.

CRITICAL INSTRUCTIONS:
1. Do not select random or disconnected sections. Every candidate segment must represent a complete, cohesive idea that makes perfect sense on its own to a viewer who has not seen the rest of the video.
2. Ensure the segment has a strong hook. The hook must start at or very close to the start timestamp of the candidate (within the first 2-3 seconds).
3. The segments must fall within the requested clip duration constraint.
4. If a topic/title hint is provided, prioritize segments relevant to that topic.
5. Pay attention to the following viral moment categories:
   - Strong Hooks: Opening statements that trigger curiosity or raise stakes.
   - Complete Ideas: Cohesive thoughts, explanations, or stories.
   - Educational Moments: Explaining concepts, definitions, or how-tos.
   - Emotional Moments: High-energy, humor, passion, or shock.
   - Surprising Statements: Contrarian opinions, counter-intuitive insights.
   - Story Moments: Mini-narratives, anecdotes, problem-solution arcs.
   - High-Value Information: Lists, tips, recommendations, or step-by-step advice.
   - Independent Sections: Paragraphs that don't depend on surrounding context.

6. Title Generation & Scoring: Brainstorm at least 3 catchy, high-converting titles for the segment. Score each title internally based on:
   - Curiosity
   - Clarity
   - Shortness (Under 50 chars is ideal)
   - Emotional pull
   - Topic relevance
   - Click potential
   Choose the absolute best title, output it as `title`, and output its score (0-100) as `title_score`.

7. Ensure start and end timestamps correspond exactly to valid bounds within the video transcript. Do not hallucinate timestamps.

8. Carefully score each candidate from 0 to 10 for the following variables:
   - Positive variables (10 is best): hook_strength, curiosity, emotional_impact, information_value, context_completeness, story_completion, shareability, retention_potential.
   - Negative variables (10 is worst): context_dependency, repetition, weak_opening.
"""

USER_PROMPT_TEMPLATE = """Analyze the following video transcript and identify up to {target_count} high-quality, viral short clip candidates.

### VIDEO INFORMATION:
- Total Duration: {duration} seconds
- Requested Clip Duration: Approximately {clip_duration} seconds (should not exceed this target significantly)
- Optional Topic/Title Focus: {topic_focus}

### ORIGINAL TIMESTAMPED TRANSCRIPT:
{transcript_segments}

Return a list of viral short clip candidates matching the response schema. Keep timestamps accurate to the nearest second based on the transcript segments provided.
"""


# ---------------------------------------------------------------------------
# Service Class
# ---------------------------------------------------------------------------

class VideoAnalysisService:
    """
    Service responsible for engineering prompts and invoking the Gemini API
    to analyze video transcripts and locate viral short candidates.
    """

    @classmethod
    async def analyze_video(
        cls,
        transcript: TranscriptionResult,
        video_duration: float,
        target_count: int = 5,
        clip_duration: float = 30.0,
        topic_focus: Optional[str] = None
    ) -> VideoAnalysisResult:
        """
        Runs the Gemini viral segment detection pipeline on a video transcript.

        Parameters
        ----------
        transcript : TranscriptionResult
            The normalized or raw transcription result containing timed segments.
        video_duration : float
            Total duration of the video in seconds.
        target_count : int, optional
            Number of shorts requested by the user.
        clip_duration : float, optional
            Desired clip duration in seconds.
        topic_focus : str, optional
            Optional topic or keyword filter.

        Returns
        -------
        VideoAnalysisResult
            The structured candidate segments list.
        """
        # Format the timestamped segments for LLM readability
        formatted_segments: List[str] = []
        for seg in transcript.segments:
            formatted_segments.append(f"[{seg.start:.2f}s - {seg.end:.2f}s]: {seg.text}")
        
        transcript_str = "\n".join(formatted_segments)

        # Build prompt variables
        topic_str = topic_focus if topic_focus and topic_focus.strip() else "None (Find best overall moments)"
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            target_count=target_count,
            duration=round(video_duration, 2),
            clip_duration=clip_duration,
            topic_focus=topic_str,
            transcript_segments=transcript_str
        )

        logger.info(
            "Analyzing transcript for viral moments (duration=%.2f, target_count=%d, topic=%s)",
            video_duration, target_count, topic_str
        )

        # Call Gemini Service with structured schema
        try:
            raw_result: VideoAnalysisResult = await GeminiService.generate_content(
                prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT,
                response_schema=VideoAnalysisResult
            )
        except Exception as exc:
            logger.warning(
                "Gemini AI moment detection unavailable (%s). Falling back to heuristic segment detection.",
                exc
            )
            raw_result = cls._heuristic_extract_candidates(
                transcript=transcript,
                video_duration=video_duration,
                target_count=target_count,
                clip_duration=clip_duration,
                topic_focus=topic_focus
            )

        # Validate and sanitize timestamps in candidates (Step 28 of Phase 4)
        valid_candidates: List[ShortCandidate] = []

        for candidate in raw_result.shorts:
            # 1. Clean timestamps
            start = max(0.0, round(candidate.start, 2))
            end = min(video_duration, round(candidate.end, 2))

            # 2. Check bounds and duration
            if start >= end:
                logger.warning("Skipping candidate with invalid bounds: start=%s, end=%s", start, end)
                continue
                
            duration = end - start
            if duration < 5.0: # Too short to be a valid clip
                logger.warning("Skipping candidate with duration too short: start=%s, end=%s", start, end)
                continue

            # Ensure start/end are safe
            candidate.start = start
            candidate.end = end
            valid_candidates.append(candidate)

        logger.info("Found %d valid viral candidates out of %d returned.", len(valid_candidates), len(raw_result.shorts))
        
        return VideoAnalysisResult(analysis=raw_result.analysis, shorts=valid_candidates)

    @classmethod
    def _heuristic_extract_candidates(
        cls,
        transcript: TranscriptionResult,
        video_duration: float,
        target_count: int,
        clip_duration: float,
        topic_focus: Optional[str] = None
    ) -> VideoAnalysisResult:
        """
        Intelligent local heuristic segment extractor used when AI APIs are unconfigured or offline.
        Chunks continuous speech into viral candidate intervals aligned with natural sentence boundaries.
        """
        shorts: List[ShortCandidate] = []
        segments = transcript.segments or []

        if not segments:
            # If no speech detected in transcript, create evenly spaced segments across video
            step = max(5.0, video_duration / max(1, target_count))
            for i in range(min(target_count, max(1, int(video_duration / 5.0)))):
                s = i * step
                e = min(video_duration, s + clip_duration)
                if s < e and (e - s) >= 5.0:
                    shorts.append(
                        ShortCandidate(
                            start=round(s, 2),
                            end=round(e, 2),
                            title=f"Viral Highlight #{i + 1}",
                            title_score=90,
                            alternative_titles=[f"Moment #{i + 1}", f"Clip #{i + 1}"],
                            category="Insight",
                            hook="Check out this key moment from the video!",
                            summary="Key highlight segment selected from the video.",
                            score=90,
                            hook_strength=9,
                            curiosity=8,
                            emotional_impact=8,
                            information_value=9,
                            context_completeness=9,
                            story_completion=8,
                            shareability=9,
                            retention_potential=9,
                            context_dependency=1,
                            repetition=1,
                            weak_opening=1
                        )
                    )
            return VideoAnalysisResult(
                analysis=AnalysisBlock(topics=["Video Highlights"], summary="Automatically extracted video segments."),
                shorts=shorts
            )

        # Partition segments into target_count logical clips
        total_segs = len(segments)
        segs_per_clip = max(1, total_segs // target_count)
        
        for i in range(target_count):
            start_seg_idx = min(i * segs_per_clip, total_segs - 1)
            first_seg = segments[start_seg_idx]
            clip_start = first_seg.start

            # Find end segment that fits within clip_duration
            clip_end = min(video_duration, clip_start + clip_duration)
            for s_idx in range(start_seg_idx, total_segs):
                seg = segments[s_idx]
                if seg.end <= clip_start + clip_duration + 2.0:
                    clip_end = seg.end
                else:
                    break

            # Fallback bounds
            clip_end = min(video_duration, max(clip_start + 5.0, clip_end))
            
            # Extract hook from the first sentence or words
            first_text = first_seg.text.strip()
            hook_text = first_text[:80] if len(first_text) > 80 else (first_text or "Watch this key insight!")
            
            title_text = f"{topic_focus.title() if topic_focus else 'Key Insight'}: {hook_text[:35]}..." if len(hook_text) > 35 else (hook_text or f"Viral Short #{i + 1}")

            shorts.append(
                ShortCandidate(
                    start=round(clip_start, 2),
                    end=round(clip_end, 2),
                    title=title_text,
                    title_score=92,
                    alternative_titles=[f"Clip #{i+1}", f"Best Moment #{i+1}"],
                    category="Educational",
                    hook=hook_text,
                    summary=f"Key segment discussing: {hook_text}",
                    score=92 - (i * 2),
                    hook_strength=9,
                    curiosity=9,
                    emotional_impact=8,
                    information_value=9,
                    context_completeness=9,
                    story_completion=9,
                    shareability=9,
                    retention_potential=9,
                    context_dependency=1,
                    repetition=1,
                    weak_opening=1
                )
            )

        return VideoAnalysisResult(
            analysis=AnalysisBlock(
                topics=[topic_focus] if topic_focus else ["Key Insights", "Highlights"],
                summary="Automatically extracted engaging moments from transcript."
            ),
            shorts=shorts
        )
