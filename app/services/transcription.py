"""
app/services/transcription.py
-----------------------------
Speech-to-Text transcription service using Faster-Whisper.
Provides thread-safe model caching suitable for background workers.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import List, Optional

from pydantic import BaseModel, Field
from faster_whisper import WhisperModel

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed Output Models (Pydantic)
# ---------------------------------------------------------------------------

class WordSegment(BaseModel):
    """Word-level timestamp and confidence mapping."""
    word: str = Field(..., description="The transcribed word (trimmed of leading/trailing spaces).")
    start: float = Field(..., description="Start time of the word in seconds (rounded to 2 decimal places).")
    end: float = Field(..., description="End time of the word in seconds (rounded to 2 decimal places).")
    probability: float = Field(..., description="Model confidence score for this word (0.0 to 1.0, rounded).")
    highlight: bool = Field(default=False, description="Whether this word should receive visual emphasis.")


class TranscriptionSegment(BaseModel):
    """A segment of transcribed audio with timestamps and metadata."""
    id: int = Field(..., description="0-indexed segment ID.")
    start: float = Field(..., description="Start time of the segment in seconds (rounded to 2 decimal places).")
    end: float = Field(..., description="End time of the segment in seconds (rounded to 2 decimal places).")
    text: str = Field(..., description="The text content of this segment.")
    words: List[WordSegment] = Field(default_factory=list, description="Word-level timestamps for this segment.")
    avg_logprob: float = Field(..., description="Average log probability of the segment (higher is better).")
    no_speech_prob: float = Field(..., description="Probability that this segment contains no speech (0.0 to 1.0).")
    compression_ratio: float = Field(..., description="Compression ratio of the segment text.")


class TranscriptionResult(BaseModel):
    """The full return value of the transcription service."""
    text: str = Field(..., description="The complete, concatenated text transcript.")
    segments: List[TranscriptionSegment] = Field(..., description="List of individual timed segments.")
    words: List[WordSegment] = Field(default_factory=list, description="Flat list of all words across all segments.")
    language: str = Field(..., description="Detected language code (e.g., 'en').")
    language_probability: float = Field(..., description="Probability of the detected language detection (0.0 to 1.0).")


# ---------------------------------------------------------------------------
# Model Cache Singleton (Thread-safe)
# ---------------------------------------------------------------------------

class WhisperModelCache:
    """
    Thread-safe lazy-loaded singleton container for the Faster-Whisper model.
    Prevents reloading the model on every task in celery worker processes.
    """
    _instance: Optional[WhisperModel] = None
    _lock = threading.Lock()
    _current_config = None

    @classmethod
    def get_model(
        cls,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None
    ) -> WhisperModel:
        """
        Retrieves the cached WhisperModel. Re-initializes if configuration changes.
        """
        model_size = model_size or settings.WHISPER_MODEL_SIZE
        device = device or settings.WHISPER_DEVICE
        compute_type = compute_type or settings.WHISPER_COMPUTE_TYPE

        config = (model_size, device, compute_type)

        with cls._lock:
            if cls._instance is None or cls._current_config != config:
                logger.info(
                    "Initializing WhisperModel cache with config: size=%s, device=%s, compute_type=%s",
                    model_size, device, compute_type
                )
                try:
                    cls._instance = WhisperModel(
                        model_size,
                        device=device,
                        compute_type=compute_type
                    )
                    cls._current_config = config
                except Exception as exc:
                    logger.error("Failed to load Faster-Whisper model: %s", exc)
                    # Reset cache state on failure
                    cls._instance = None
                    cls._current_config = None
                    raise RuntimeError(f"Failed to load WhisperModel: {exc}") from exc

            return cls._instance


# ---------------------------------------------------------------------------
# Service Class
# ---------------------------------------------------------------------------

class TranscriptionService:
    """
    Service to transcribe speech audio using Faster-Whisper.
    """

    @classmethod
    def transcribe(
        cls,
        audio_path: str,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        word_timestamps: bool = True,
        beam_size: int = 5,
        **whisper_kwargs
    ) -> TranscriptionResult:
        """
        Transcribe an audio file to text.

        Parameters
        ----------
        audio_path : str
            Path to the audio WAV/MP3 file.
        model_size : str, optional
            Faster-Whisper model size override (e.g., 'tiny', 'base', 'small', 'medium', 'large-v3').
        device : str, optional
            Device override ('cpu', 'cuda', 'auto').
        compute_type : str, optional
            Compute type override ('int8', 'float16', 'default').
        word_timestamps : bool, optional
            If True, extracts word-level timestamps and confidences.
        beam_size : int, optional
            Beam size for decoding.
        **whisper_kwargs
            Additional arguments passed directly to model.transcribe().

        Returns
        -------
        TranscriptionResult
            Pydantic model containing transcript, segments, language, and confidence.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Retrieve cached model instance
        model = WhisperModelCache.get_model(
            model_size=model_size,
            device=device,
            compute_type=compute_type
        )

        beam_size = 1 if beam_size is None else beam_size
        vad_filter = whisper_kwargs.pop("vad_filter", True)
        condition_on_previous_text = whisper_kwargs.pop("condition_on_previous_text", False)

        try:
            segments_generator, info = model.transcribe(
                audio_path,
                beam_size=beam_size,
                word_timestamps=word_timestamps,
                vad_filter=vad_filter,
                condition_on_previous_text=condition_on_previous_text,
                **whisper_kwargs
            )

            segments: List[TranscriptionSegment] = []
            all_words: List[WordSegment] = []
            full_text_parts: List[str] = []

            # segments_generator is a lazy generator; transcription runs as we iterate
            for idx, seg in enumerate(segments_generator):
                words: List[WordSegment] = []
                if word_timestamps and seg.words:
                    words = [
                        WordSegment(
                            word=w.word.strip(),
                            start=round(w.start, 2),
                            end=round(w.end, 2),
                            probability=round(w.probability, 2)
                        )
                        for w in seg.words
                    ]

                all_words.extend(words)

                segment_model = TranscriptionSegment(
                    id=idx,
                    start=round(seg.start, 2),
                    end=round(seg.end, 2),
                    text=seg.text,
                    words=words,
                    avg_logprob=seg.avg_logprob,
                    no_speech_prob=seg.no_speech_prob,
                    compression_ratio=seg.compression_ratio
                )
                segments.append(segment_model)
                full_text_parts.append(seg.text)

            full_text = "".join(full_text_parts).strip()

            logger.info(
                "Transcription complete. Language: %s (%.2f probability), segments: %d",
                info.language,
                info.language_probability,
                len(segments)
            )

            return TranscriptionResult(
                text=full_text,
                segments=segments,
                words=all_words,
                language=info.language,
                language_probability=info.language_probability
            )

        except Exception as exc:
            logger.error("Error during transcription execution: %s", exc)
            raise RuntimeError(f"Transcription failed: {exc}") from exc
