"""
app/services/gemini.py
----------------------
Secure and reusable Google Gemini API service abstraction.
Supports structured outputs (Pydantic), retries with exponential backoff,
timeout configuration, rate-limit handling (429), and safe logging.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Type, TypeVar, Union
import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiError(Exception):
    """Base exception class for all Gemini API integration errors."""
    pass


class GeminiConfigurationError(GeminiError):
    """Raised when Gemini API is misconfigured (e.g. missing API key)."""
    pass


class GeminiService:
    """
    Service responsible for interacting with the Google Gemini API securely.
    """

    @staticmethod
    def _clean_schema_for_gemini(schema: Dict[str, Any], defs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Recursively converts a standard JSON Schema (from Pydantic) to Gemini API's expected format.
        - Resolves internal references ($ref) using $defs.
        - Standardizes types to uppercase (e.g. 'object' -> 'OBJECT').
        """
        if defs is None:
            defs = schema.get("$defs", {})

        # Resolve references
        if "$ref" in schema:
            ref_path = schema["$ref"]
            def_name = ref_path.split("/")[-1]
            if def_name in defs:
                return GeminiService._clean_schema_for_gemini(defs[def_name], defs)
            else:
                raise ValueError(f"Reference '{ref_path}' not found in schema definitions.")

        cleaned: Dict[str, Any] = {}
        
        if "type" in schema:
            json_type = schema["type"]
            type_map = {
                "object": "OBJECT",
                "array": "ARRAY",
                "string": "STRING",
                "number": "NUMBER",
                "integer": "INTEGER",
                "boolean": "BOOLEAN"
            }
            cleaned["type"] = type_map.get(json_type, "STRING")
        
        if "description" in schema:
            cleaned["description"] = schema["description"]

        if "properties" in schema:
            cleaned["properties"] = {
                k: GeminiService._clean_schema_for_gemini(v, defs)
                for k, v in schema["properties"].items()
            }

        if "items" in schema:
            cleaned["items"] = GeminiService._clean_schema_for_gemini(schema["items"], defs)

        if "required" in schema:
            cleaned["required"] = schema["required"]

        return cleaned

    @classmethod
    async def generate_content(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        response_schema: Optional[Type[T]] = None,
        model: Optional[str] = None,
        timeout: float = 45.0,
        max_retries: int = 3,
        base_delay: float = 2.0
    ) -> Union[str, T]:
        """
        Generates content from Gemini API with safety controls.

        Parameters
        ----------
        prompt : str
            The prompt text.
        system_instruction : str, optional
            System instructions for the model.
        response_schema : Type[Pydantic BaseModel], optional
            If provided, forces Gemini to output structured JSON conforming to the schema
            and returns the parsed model instance.
        model : str, optional
            Model override (defaults to settings.GEMINI_MODEL).
        timeout : float, optional
            Request timeout in seconds.
        max_retries : int, optional
            Maximum retries for 429 rate limit or 5xx server issues.
        base_delay : float, optional
            Initial delay for exponential backoff.

        Returns
        -------
        Union[str, BaseModel]
            String response or a validated Pydantic model instance.
        """
        # Validate API configuration
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise GeminiConfigurationError(
                "Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable."
            )

        model_name = model or settings.GEMINI_MODEL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        # 1. Build Payload
        contents = [{
            "role": "user",
            "parts": [{"text": prompt}]
        }]

        payload: Dict[str, Any] = {
            "contents": contents
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Handle structured output
        if response_schema:
            pydantic_schema = response_schema.model_json_schema()
            gemini_schema = cls._clean_schema_for_gemini(pydantic_schema)
            payload["generationConfig"] = {
                "responseMimeType": "application/json",
                "responseSchema": gemini_schema
            }

        # 2. HTTP Call Loop with Backoff Retries
        logger.info(
            "Sending request to Gemini API (model=%s, prompt_len=%d, structured=%s)",
            model_name, len(prompt), response_schema is not None
        )
        
        start_time = time.monotonic()

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)

                # Retry on rate limiting
                if response.status_code == 429:
                    if attempt == max_retries:
                        raise GeminiError(f"Gemini API rate limit exceeded (HTTP 429) after {max_retries} retries.")
                    delay = base_delay * (2 ** attempt)
                    logger.warning("Gemini rate limit hit (HTTP 429). Retrying in %.2fs...", delay)
                    await asyncio.sleep(delay)
                    continue

                # Retry on server errors
                if response.status_code >= 500:
                    if attempt == max_retries:
                        raise GeminiError(f"Gemini server error (HTTP {response.status_code}) after {max_retries} retries.")
                    delay = base_delay * (2 ** attempt)
                    logger.warning("Gemini server error (HTTP %d). Retrying in %.2fs...", response.status_code, delay)
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()
                response_json = response.json()
                break

            except (httpx.RequestError, httpx.TimeoutException) as exc:
                if attempt == max_retries:
                    raise GeminiError(f"Gemini HTTP request failed: {exc}") from exc
                delay = base_delay * (2 ** attempt)
                logger.warning("Gemini request failed (%s). Retrying in %.2fs...", type(exc).__name__, delay)
                await asyncio.sleep(delay)

        duration = time.monotonic() - start_time

        # 3. Parse candidates
        candidates = response_json.get("candidates", [])
        if not candidates:
            raise GeminiError("Gemini returned a response with no output candidates.")

        candidate = candidates[0]
        text_response = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
        if not text_response:
            # Check if finished due to safety/other reasons
            finish_reason = candidate.get("finishReason", "UNKNOWN")
            raise GeminiError(f"Gemini returned an empty response. Finish reason: {finish_reason}")

        # Safe logging (Never log prompt or transcript details to avoid leaking private video content)
        usage = response_json.get("usageMetadata", {})
        logger.info(
            "Gemini call complete in %.2fs. Tokens: prompt=%d, candidate=%d, total=%d",
            duration,
            usage.get("promptTokenCount", 0),
            usage.get("candidatesTokenCount", 0),
            usage.get("totalTokenCount", 0)
        )

        # Validate structured output
        if response_schema:
            def clean_json_text(text: str) -> str:
                t = text.strip()
                if t.startswith("```"):
                    first_line_end = t.find("\n")
                    if first_line_end != -1:
                        t = t[first_line_end:]
                    if t.endswith("```"):
                        t = t[:-3]
                return t.strip()

            cleaned_text = clean_json_text(text_response)
            try:
                return response_schema.model_validate_json(cleaned_text)
            except Exception as parse_error:
                logger.warning("Failed to parse Gemini response as JSON: %s. Attempting repair...", parse_error)
                
                # Controlled JSON repair retry logic
                repair_prompt = (
                    f"The previous response was not valid JSON conforming to the requested schema.\n"
                    f"Error details: {parse_error}\n"
                    f"Raw response was:\n{text_response}\n\n"
                    f"Please output ONLY valid JSON matching this schema: {response_schema.model_json_schema()}"
                )

                try:
                    logger.info("Sending repair request to Gemini...")
                    repaired_raw = await cls.generate_content(
                        prompt=repair_prompt,
                        system_instruction="You are a strict JSON formatter. Fix the invalid JSON and return ONLY the valid JSON block matching the requested schema. Do not include markdown code fences or conversational text.",
                        response_schema=None,
                        model=model_name,
                        timeout=timeout,
                        max_retries=1
                    )
                    repaired_cleaned = clean_json_text(repaired_raw)
                    return response_schema.model_validate_json(repaired_cleaned)
                except Exception as repair_error:
                    logger.error("JSON repair process failed: %s", repair_error)
                    raise GeminiError(
                        f"Gemini response could not be validated against schema after JSON repair. Original error: {parse_error}. Repair error: {repair_error}"
                    ) from repair_error

        return text_response
