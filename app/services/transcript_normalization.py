"""
app/services/transcript_normalization.py
----------------------------------------
Service to clean and normalize Whisper speech-to-text transcriptions.
Removes duplicate words (stutters), filler words, excessive whitespace,
and transcription artifacts/hallucinations while preserving timestamps
and segment boundaries. Keeps the original raw transcription for debugging.
"""

from __future__ import annotations

import logging
import re
from typing import List, Set
from pydantic import BaseModel, Field

from app.services.transcription import TranscriptionResult, TranscriptionSegment, WordSegment

logger = logging.getLogger(__name__)

# Common filler words to remove
DEFAULT_FILLER_WORDS: Set[str] = {
    "uh", "um", "ah", "er", "hmm", "eh", "oh", "like"
}

# Common emphasis words that should NOT be treated as duplicate stutter artifacts
EMPHASIS_WORDS: Set[str] = {
    "very", "many", "great", "long", "far", "never", "so", "more", "less", "really",
    "no", "yes", "please", "go", "stop", "run"
}

# Patterns of common Whisper hallucination / artifact strings
HALLUCINATION_PATTERNS = [
    r"^\[music\]$",
    r"^\[music\s+playing\]$",
    r"^\(music\)$",
    r"^\(singing\)$",
    r"^\[applause\]$",
    r"^\[laughter\]$",
    r"^thank\s+you\s+for\s+watching$",
    r"^please\s+subscribe$",
    r"^subscribed\s+by$"
]


class NormalizedTranscriptionResult(BaseModel):
    """The normalized transcription result containing both raw and clean versions."""
    original: TranscriptionResult = Field(..., description="The raw, unmodified original transcription for debugging.")
    normalized: TranscriptionResult = Field(..., description="The cleaned, normalized transcription ready for consumption.")


class TranscriptNormalizationService:
    """
    Service responsible for cleaning speech-to-text transcription artifacts, stutters,
    filler words, invalid timestamps, and whitespace.
    """

    @staticmethod
    def _clean_word_for_comparison(word: str) -> str:
        """Helper to lower-case and strip punctuation from a word for equality checks."""
        # Strip common punctuation
        cleaned = re.sub(r"[^\w\s]", "", word.lower())
        return cleaned.strip()

    @classmethod
    def normalize(
        cls,
        result: TranscriptionResult,
        remove_fillers: bool = True,
        filler_words: Set[str] = DEFAULT_FILLER_WORDS,
        remove_hallucinations: bool = True
    ) -> NormalizedTranscriptionResult:
        """
        Cleans and normalizes a TranscriptionResult.

        Parameters
        ----------
        result : TranscriptionResult
            The raw transcription result to clean.
        remove_fillers : bool, optional
            Whether to strip filler words ("uh", "um", etc.).
        filler_words : Set[str], optional
            Set of filler words to strip.
        remove_hallucinations : bool, optional
            Whether to clean common Whisper silent-hallucination artifacts.

        Returns
        -------
        NormalizedTranscriptionResult
            Pydantic model containing both the original and normalized transcript.
        """
        logger.info("Starting transcript normalization...")

        # Deep-copy segments to avoid modifying the original in-place
        cleaned_segments: List[TranscriptionSegment] = []
        
        for seg in result.segments:
            cleaned_words: List[WordSegment] = []
            
            # 1. Clean individual word strings, timestamps, and filter filler words/artifacts
            for w in seg.words:
                cleaned_text = w.word.strip()
                if not cleaned_text:
                    continue

                # Strip/clean timestamps
                start = max(0.0, round(w.start, 2))
                end = max(start + 0.05, round(w.end, 2))

                # Check if word is filler
                word_lower = cls._clean_word_for_comparison(cleaned_text)
                if remove_fillers and word_lower in filler_words:
                    # Skip filler word
                    continue

                # Check if word matches hallucination/music tags
                if remove_hallucinations:
                    is_hallucination = False
                    for pattern in HALLUCINATION_PATTERNS:
                        if re.search(pattern, word_lower) or re.search(pattern, cleaned_text.lower()):
                            is_hallucination = True
                            break
                    if is_hallucination:
                        continue

                cleaned_words.append(
                    WordSegment(
                        word=cleaned_text,
                        start=start,
                        end=end,
                        probability=w.probability
                    )
                )

            # 2. Clean stutters / duplicate words (consecutive repetitions)
            i = 0
            while i < len(cleaned_words) - 1:
                w_curr = cleaned_words[i]
                w_next = cleaned_words[i + 1]
                
                curr_clean = cls._clean_word_for_comparison(w_curr.word)
                next_clean = cls._clean_word_for_comparison(w_next.word)

                # If they are duplicates and not emphasis words, merge them
                if curr_clean == next_clean and curr_clean not in EMPHASIS_WORDS:
                    # Extend end of current word to end of next word
                    w_curr.end = max(w_curr.end, w_next.end)
                    # Remove the next word
                    cleaned_words.pop(i + 1)
                else:
                    i += 1

            # 3. Clean invalid or overlapping timestamps in the sequence
            for idx in range(1, len(cleaned_words)):
                prev_w = cleaned_words[idx - 1]
                curr_w = cleaned_words[idx]

                # Resolve overlaps
                if curr_w.start < prev_w.end:
                    # Shrink previous end to current start
                    prev_w.end = curr_w.start
                    # Ensure previous word still has positive duration
                    if prev_w.start >= prev_w.end:
                        prev_w.start = max(0.0, round(prev_w.end - 0.1, 2))

            # 4. If all words in segment were removed, omit the segment
            if not cleaned_words:
                continue

            # Update segment timestamps based on remaining words
            seg_start = cleaned_words[0].start
            seg_end = cleaned_words[-1].end

            # Clean the segment text by joining clean words
            seg_text = " ".join(w.word for w in cleaned_words)

            cleaned_segments.append(
                TranscriptionSegment(
                    id=len(cleaned_segments),  # re-index
                    start=seg_start,
                    end=seg_end,
                    text=seg_text,
                    words=cleaned_words,
                    avg_logprob=seg.avg_logprob,
                    no_speech_prob=seg.no_speech_prob,
                    compression_ratio=seg.compression_ratio
                )
            )

        # 5. Assemble final normalized TranscriptionResult
        normalized_full_text = " ".join(seg.text for seg in cleaned_segments)
        
        # Flat list of all remaining clean words
        flat_words: List[WordSegment] = []
        for seg in cleaned_segments:
            flat_words.extend(seg.words)

        normalized_result = TranscriptionResult(
            text=normalized_full_text,
            segments=cleaned_segments,
            words=flat_words,
            language=result.language,
            language_probability=result.language_probability
        )

        logger.info(
            "Normalization complete. Removed %d segments and %d words.",
            len(result.segments) - len(cleaned_segments),
            len(result.words) - len(flat_words)
        )

        return NormalizedTranscriptionResult(
            original=result,
            normalized=normalized_result
        )
