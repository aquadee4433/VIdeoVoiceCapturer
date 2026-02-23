"""Core audio extraction using yt-dlp and ffmpeg."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import yt_dlp


class AudioExtractor:
    """Extract audio from YouTube videos."""
    
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _check_dependencies(self) -> bool:
        """Check if required system tools are installed."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def extract(self, url: str, format: str = "wav", verbose: bool = False) -> Optional[str]:
        """
        Extract audio from a YouTube video.
        
        Args:
            url: YouTube video URL
            format: Output format ('wav' or 'mp3')
            verbose: Enable verbose output
            
        Returns:
            Path to extracted audio file, or None on failure
        """
        if not self._check_dependencies():
            raise RuntimeError("ffmpeg not found. Please install: brew install ffmpeg")
        
        # Sanitize format
        format = format.lower().lstrip(".")
        if format not in ("wav", "mp3"):
            raise ValueError("Format must be 'wav' or 'mp3'")
        
        # Prepare yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.output_dir / 'temp_audio.%(ext)s'),
            'quiet': not verbose,
            'no_warnings': not verbose,
        }
        
        # Extract audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'audio')
            # Sanitize filename
            safe_title = "".join(c for c in video_title if c.isalnum() or c in " -_").strip()[:50]
        
        # Find the downloaded file
        temp_file = self.output_dir / "temp_audio.webm"
        if not temp_file.exists():
            temp_file = self.output_dir / "temp_audio.m4a"
        if not temp_file.exists():
            raise FileNotFoundError("Failed to download audio")
        
        # Convert to target format
        output_file = self.output_dir / f"{safe_title}.{format}"
        
        self._convert_audio(temp_file, output_file, format, verbose)
        
        # Cleanup temp file
        temp_file.unlink()
        
        return str(output_file)
    
    def _convert_audio(self, input_file: Path, output_file: Path, format: str, verbose: bool):
        """Convert audio to target format using ffmpeg."""
        cmd = ["ffmpeg", "-y", "-i", str(input_file)]
        
        if format == "mp3":
            cmd.extend(["-codec:a", "libmp3lame", "-q:a", "2"])
        else:  # wav
            cmd.extend(["-codec:a", "pcm_s16le"])
        
        if not verbose:
            cmd.extend(["-loglevel", "quiet"])
        
        cmd.append(str(output_file))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")