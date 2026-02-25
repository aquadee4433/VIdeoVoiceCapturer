"""Pytest configuration and fixtures for VIdeoVoiceCapturer tests."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_youtube_urls():
    """Sample valid YouTube URLs for testing."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/abc123",
        "https://www.youtube.com/live/xyz789",
    ]


@pytest.fixture
def invalid_urls():
    """Sample invalid URLs for testing."""
    return [
        "",
        None,
        123,
        "https://vimeo.com/123456",
        "https://example.com/video",
        "not a url",
    ]
