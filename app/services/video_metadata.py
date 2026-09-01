import subprocess
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class VideoMetadata(BaseModel):
    duration_seconds: float = Field(0.0, description="Duration in seconds")
    width: int = Field(0, description="Video width in pixels")
    height: int = Field(0, description="Video height in pixels")
    fps: float = Field(0.0, description="Frames per second")
    video_codec: str = Field("unknown", description="Video codec (e.g., h264, vp9)")
    audio_codec: Optional[str] = Field(None, description="Audio codec (e.g., aac), None if missing")
    has_audio: bool = Field(False, description="True if an audio stream is present")
    file_size_bytes: int = Field(0, description="Size of the file in bytes")
    container_format: str = Field("unknown", description="Container format (e.g., mp4, matroska)")
    bitrate: int = Field(0, description="Overall bitrate in bps")

class FFprobeError(Exception):
    """Custom exception for FFprobe failures."""
    pass

class VideoMetadataService:
    @staticmethod
    def extract_metadata(file_path: str) -> VideoMetadata:
        """
        Extract detailed metadata from a video file using FFprobe.
        Robust against malformed input, missing audio, and invalid files.
        Never crashes the worker; returns an exception or a safe default.
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]
            
            # Use a timeout to prevent hanging on malformed files
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                raise FFprobeError(f"FFprobe exited with code {result.returncode}")
                
            data = json.loads(result.stdout)
            
            format_info = data.get("format", {})
            streams = data.get("streams", [])
            
            if not streams:
                raise FFprobeError("No streams found in file.")
                
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
            
            if not video_stream:
                raise FFprobeError("No video stream found. File may be an audio file or corrupt.")

            # Calculate FPS safely
            fps = 0.0
            r_frame_rate = video_stream.get("r_frame_rate", "0/1")
            try:
                num, den = map(int, r_frame_rate.split('/'))
                if den != 0:
                    fps = num / den
            except Exception:
                fps = 0.0

            return VideoMetadata(
                duration_seconds=float(format_info.get("duration", video_stream.get("duration", 0.0))),
                width=int(video_stream.get("width", 0)),
                height=int(video_stream.get("height", 0)),
                fps=fps,
                video_codec=video_stream.get("codec_name", "unknown"),
                audio_codec=audio_stream.get("codec_name") if audio_stream else None,
                has_audio=bool(audio_stream),
                file_size_bytes=int(format_info.get("size", 0)),
                container_format=format_info.get("format_name", "unknown"),
                bitrate=int(format_info.get("bit_rate", video_stream.get("bit_rate", 0)))
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"FFprobe timed out for {file_path}")
            raise FFprobeError("FFprobe execution timed out.")
        except FileNotFoundError:
            logger.error("FFprobe executable not found on system PATH.")
            raise FFprobeError("FFprobe is not installed or not in PATH.")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse FFprobe JSON for {file_path}")
            raise FFprobeError("Invalid JSON output from FFprobe (file may be corrupt).")
        except Exception as e:
            logger.error(f"Unexpected error extracting metadata for {file_path}: {str(e)}")
            raise FFprobeError(f"Unexpected metadata extraction error: {str(e)}")
