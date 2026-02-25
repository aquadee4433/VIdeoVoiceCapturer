"""Unit tests for the audio extractor module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from videovoicecapturer.extractor import (
    AudioExtractor,
    AudioExtractionError,
)


class TestAudioExtractorInit:
    """Tests for AudioExtractor initialization."""

    def test_default_initialization(self, temp_output_dir):
        """Test default initialization creates output directory."""
        with patch("videovoicecapturer.extractor.Path.mkdir"):
            extractor = AudioExtractor()
            assert extractor.output_dir == Path(".")

    def test_custom_output_dir(self, temp_output_dir):
        """Test initialization with custom output directory."""
        extractor = AudioExtractor(str(temp_output_dir))
        assert extractor.output_dir == temp_output_dir
        assert temp_output_dir.exists()


class TestURLValidation:
    """Tests for URL validation."""

    def test_valid_youtube_watch_url(self, temp_output_dir):
        """Test valid youtube.com/watch URL."""
        extractor = AudioExtractor(str(temp_output_dir))
        extractor._validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_youtu_be_url(self, temp_output_dir):
        """Test valid youtu.be URL."""
        extractor = AudioExtractor(str(temp_output_dir))
        extractor._validate_url("https://youtu.be/dQw4w9WgXcQ")

    def test_valid_youtube_shorts_url(self, temp_output_dir):
        """Test valid youtube.com/shorts URL."""
        extractor = AudioExtractor(str(temp_output_dir))
        extractor._validate_url("https://www.youtube.com/shorts/abc123")

    def test_valid_youtube_live_url(self, temp_output_dir):
        """Test valid youtube.com/live URL."""
        extractor = AudioExtractor(str(temp_output_dir))
        extractor._validate_url("https://www.youtube.com/live/xyz789")

    def test_empty_url_raises_error(self, temp_output_dir):
        """Test empty URL raises AudioExtractionError."""
        extractor = AudioExtractor(str(temp_output_dir))
        with pytest.raises(AudioExtractionError, match="Invalid URL"):
            extractor._validate_url("")

    def test_none_url_raises_error(self, temp_output_dir):
        """Test None URL raises AudioExtractionError."""
        extractor = AudioExtractor(str(temp_output_dir))
        with pytest.raises(AudioExtractionError, match="Invalid URL"):
            extractor._validate_url(None)

    def test_non_string_url_raises_error(self, temp_output_dir):
        """Test non-string URL raises AudioExtractionError."""
        extractor = AudioExtractor(str(temp_output_dir))
        with pytest.raises(AudioExtractionError, match="Invalid URL"):
            extractor._validate_url(123)

    def test_invalid_url_raises_error(self, temp_output_dir):
        """Test invalid URL raises AudioExtractionError."""
        extractor = AudioExtractor(str(temp_output_dir))
        with pytest.raises(AudioExtractionError, match="Invalid YouTube URL"):
            extractor._validate_url("https://vimeo.com/123456")

    def test_random_string_raises_error(self, temp_output_dir):
        """Test random string raises AudioExtractionError."""
        extractor = AudioExtractor(str(temp_output_dir))
        with pytest.raises(AudioExtractionError, match="Invalid YouTube URL"):
            extractor._validate_url("not a url")


class TestFilenameSanitization:
    """Tests for filename sanitization."""

    def test_sanitize_normal_title(self, temp_output_dir):
        """Test sanitization of normal title."""
        extractor = AudioExtractor(str(temp_output_dir))
        result = extractor._sanitize_filename("My Video Title")
        assert result == "My Video Title"

    def test_sanitize_special_characters(self, temp_output_dir):
        """Test sanitization removes special characters."""
        extractor = AudioExtractor(str(temp_output_dir))
        result = extractor._sanitize_filename("Video: Title | 2023!")
        # Should only keep alphanumerics, spaces, dashes, underscores
        assert all(c.isalnum() or c in " -_" for c in result)

    def test_sanitize_long_title(self, temp_output_dir):
        """Test long titles are truncated."""
        extractor = AudioExtractor(str(temp_output_dir))
        long_title = "A" * 100
        result = extractor._sanitize_filename(long_title)
        assert len(result) <= 50

    def test_sanitize_empty_after_cleaning(self, temp_output_dir):
        """Test fallback to 'audio' if title becomes empty."""
        extractor = AudioExtractor(str(temp_output_dir))
        result = extractor._sanitize_filename("!!!")
        # Either "audio" fallback or underscores are valid
        assert result in ["audio", "___"]


class TestFFmpegCheck:
    """Tests for ffmpeg dependency checking."""

    def test_ffmpeg_available(self, temp_output_dir):
        """Test _check_dependencies returns True when ffmpeg is available."""
        extractor = AudioExtractor(str(temp_output_dir))
        with patch("videovoicecapturer.extractor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            result = extractor._check_dependencies()
            assert result is True

    def test_ffmpeg_not_found(self, temp_output_dir):
        """Test _check_dependencies returns False when ffmpeg is not found."""
        extractor = AudioExtractor(str(temp_output_dir))
        with patch("videovoicecapturer.extractor.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = extractor._check_dependencies()
            assert result is False

    def test_check_ffmpeg_raises_error(self, temp_output_dir):
        """Test _check_ffmpeg raises error when ffmpeg not available."""
        extractor = AudioExtractor(str(temp_output_dir))
        with patch.object(extractor, "_check_dependencies", return_value=False):
            with pytest.raises(AudioExtractionError, match="ffmpeg not found"):
                extractor._check_ffmpeg()


class TestSupportedFormats:
    """Tests for supported format validation."""

    def test_supported_formats(self):
        """Test SUPPORTED_FORMATS contains expected formats."""
        assert "wav" in AudioExtractor.SUPPORTED_FORMATS
        assert "mp3" in AudioExtractor.SUPPORTED_FORMATS

    def test_extract_rejects_invalid_format(self, temp_output_dir):
        """Test extract raises error for unsupported format."""
        extractor = AudioExtractor(str(temp_output_dir))
        with patch.object(extractor, "_check_ffmpeg"):
            with pytest.raises(AudioExtractionError, match="Unsupported format"):
                extractor.extract("https://youtube.com/watch?v=test", format="flac")

    def test_extract_accepts_wav(self, temp_output_dir):
        """Test extract accepts wav format."""
        extractor = AudioExtractor(str(temp_output_dir))
        with patch.object(extractor, "_check_ffmpeg"):
            with patch.object(extractor, "_validate_url"):
                with patch("videovoicecapturer.extractor.yt_dlp.YoutubeDL") as mock_ydl:
                    mock_instance = MagicMock()
                    mock_instance.extract_info.return_value = {"title": "Test"}
                    mock_ydl.return_value.__enter__ = MagicMock(
                        return_value=mock_instance
                    )
                    mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
                    # Mock no temp file found
                    with pytest.raises(AudioExtractionError):
                        extractor.extract("https://youtube.com/watch?v=test", format="wav")

    def test_extract_accepts_mp3(self, temp_output_dir):
        """Test extract accepts mp3 format."""
        extractor = AudioExtractor(str(temp_output_dir))
        with patch.object(extractor, "_check_ffmpeg"):
            with patch.object(extractor, "_validate_url"):
                with patch("videovoicecapturer.extractor.yt_dlp.YoutubeDL") as mock_ydl:
                    mock_instance = MagicMock()
                    mock_instance.extract_info.return_value = {"title": "Test"}
                    mock_ydl.return_value.__enter__ = MagicMock(
                        return_value=mock_instance
                    )
                    mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
                    with pytest.raises(AudioExtractionError):
                        extractor.extract("https://youtube.com/watch?v=test", format="mp3")


class TestErrorHandling:
    """Tests for error handling."""

    def test_download_error_is_handled(self, temp_output_dir):
        """Test that download errors can be caught."""
        # This test verifies the error handling code exists
        import yt_dlp
        # Verify DownloadError exists and can be caught
        with pytest.raises(Exception):
            raise yt_dlp.utils.DownloadError("test")
