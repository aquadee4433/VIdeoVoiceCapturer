"""Core audio extraction using yt-dlp and ffmpeg."""

import os
import subprocess
from pathlib import Path
from typing import Optional, List
import yt_dlp


class AudioExtractionError(Exception):
    """Custom exception for audio extraction errors."""
    pass


class AudioExtractor:
    """Extract audio from YouTube videos."""
    
    SUPPORTED_FORMATS = ("wav", "mp3")
    
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _check_dependencies(self) -> bool:
        """Check if required system tools are installed."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                check=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _check_ffmpeg(self) -> None:
        """Check if ffmpeg is available, raise error if not."""
        if not self._check_dependencies():
            raise AudioExtractionError(
                "ffmpeg not found. Please install: brew install ffmpeg (macOS) or sudo apt install ffmpeg (Ubuntu)"
            )
    
    def _validate_url(self, url: str) -> None:
        """Validate YouTube URL format."""
        if not url or not isinstance(url, str):
            raise AudioExtractionError("Invalid URL: URL must be a non-empty string")
        
        # Basic YouTube URL patterns
        valid_patterns = [
            "youtube.com/watch",
            "youtu.be/",
            "youtube.com/shorts/",
            "youtube.com/live/",
        ]
        
        if not any(pattern in url for pattern in valid_patterns):
            raise AudioExtractionError(
                f"Invalid YouTube URL: {url}\n"
                "Supported formats: youtube.com/watch?v=..., youtu.be/..., youtube.com/shorts/..."
            )
    
    def extract(self, url: str, format: str = "wav", verbose: bool = False) -> Optional[str]:
        """
        Extract audio from a YouTube video.
        
        Args:
            url: YouTube video URL
            format: Output format ('wav' or 'mp3')
            verbose: Enable verbose output
            
        Returns:
            Path to extracted audio file, or None on failure
            
        Raises:
            AudioExtractionError: If extraction fails
        """
        # Validate inputs
        self._check_ffmpeg()
        self._validate_url(url)
        
        # Sanitize format
        format = format.lower().lstrip(".")
        if format not in self.SUPPORTED_FORMATS:
            raise AudioExtractionError(
                f"Unsupported format: {format}. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Prepare yt-dlp options with better YouTube handling
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(self.output_dir / 'temp_audio.%(ext)s'),
            'quiet': not verbose,
            'no_warnings': not verbose,
            'extractor_retries': 3,
            'fragment_retries': 3,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
        }
        
        # Download audio
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_title = info.get('title', 'audio')
                # Sanitize filename
                safe_title = self._sanitize_filename(video_title)
        except yt_dlp.utils.DownloadError as e:
            raise AudioExtractionError(f"Download failed: {e}")
        except yt_dlp.utils.ExtractorError as e:
            raise AudioExtractionError(f"Extraction failed: {e}")
        except Exception as e:
            raise AudioExtractionError(f"Unexpected error: {e}")
        
        # Find the downloaded file (check all common audio formats)
        temp_file = None
        for ext in ['.mp4', '.webm', '.m4a', '.mp3', '.ogg']:
            candidate = self.output_dir / f"temp_audio{ext}"
            if candidate.exists():
                temp_file = candidate
                break
        
        if temp_file is None:
            raise AudioExtractionError("Downloaded file not found. The video may be unavailable.")
        
        # Convert to target format
        output_file = self.output_dir / f"{safe_title}.{format}"
        
        try:
            self._convert_audio(temp_file, output_file, format, verbose)
        except Exception as e:
            raise AudioExtractionError(f"Audio conversion failed: {e}")
        finally:
            # Cleanup temp file
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass  # Ignore cleanup errors
        
        return str(output_file)
    
    def _sanitize_filename(self, title: str) -> str:
        """Sanitize video title for use as filename."""
        # Remove or replace invalid characters
        safe_chars = []
        for c in title:
            if c.isalnum() or c in " -_":
                safe_chars.append(c)
            elif c in "...":
                safe_chars.append("...")
            else:
                safe_chars.append("_")
        
        safe_title = "".join(safe_chars).strip()
        # Limit length
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        
        return safe_title or "audio"
    
    def _convert_audio(self, input_file: Path, output_file: Path, format: str, verbose: bool):
        """Convert audio to target format using ffmpeg."""
        cmd = ["ffmpeg", "-y", "-i", str(input_file)]
        
        if format == "mp3":
            cmd.extend(["-codec:a", "libmp3lame", "-q:a", "2"])
        else:  # wav
            cmd.extend(["-codec:a", "pcm_s16le", "-ar", "44100", "-ac", "2"])
        
        if not verbose:
            cmd.extend(["-loglevel", "quiet"])
        
        cmd.append(str(output_file))
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown ffmpeg error"
            raise RuntimeError(f"ffmpeg conversion failed: {error_msg}")
        
        if not output_file.exists():
            raise RuntimeError("Output file was not created")