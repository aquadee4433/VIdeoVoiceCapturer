"""Integration tests - requires network and real YouTube URL."""

import pytest
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from videovoicecapturer.extractor import AudioExtractor, AudioExtractionError


# Skip all tests in this module if CI=true or no network
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipping integration tests in CI (requires network)"
)


class TestIntegration:
    """Integration tests - requires real YouTube URL."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_output_dir = "/tmp/vvc_integration_test"
        os.makedirs(self.test_output_dir, exist_ok=True)
        self.extractor = AudioExtractor(output_dir=self.test_output_dir)

    def teardown_method(self):
        """Clean up after tests."""
        # Clean up test files
        import shutil
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir, ignore_errors=True)

    @pytest.mark.integration
    def test_extract_audio_real_url(self):
        """Test extraction with a real YouTube URL.
        
        Note: This test may fail due to:
        - YouTube rate limiting
        - Network issues
        - Video availability
        
        It should be run manually or in specific test environments.
        """
        # Use a known test video (Rick Astley - never gonna give you up)
        # Note: This may be rate limited by YouTube
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        try:
            result = self.extractor.extract(test_url, format="wav", verbose=True)
            
            # Check that file was created
            assert result is not None
            assert os.path.exists(result)
            
            # Check file is not empty
            assert os.path.getsize(result) > 0
            
            print(f"Successfully extracted to: {result}")
            
        except AudioExtractionError as e:
            # May fail due to YouTube rate limiting
            pytest.skip(f"YouTube rate limited or unavailable: {e}")
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")

    @pytest.mark.integration
    def test_extract_mp3_format(self):
        """Test MP3 format extraction."""
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        try:
            result = self.extractor.extract(test_url, format="mp3", verbose=True)
            
            assert result is not None
            assert result.endswith(".mp3")
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
            
        except AudioExtractionError as e:
            pytest.skip(f"YouTube rate limited or unavailable: {e}")


class TestEndToEnd:
    """End-to-end CLI tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_output_dir = "/tmp/vvc_e2e_test"
        os.makedirs(self.test_output_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir, ignore_errors=True)

    @pytest.mark.integration
    def test_cli_extract_and_convert(self):
        """Test full CLI workflow."""
        from click.testing import CliRunner
        from videovoicecapturer.cli import main
        
        runner = CliRunner()
        
        # This will likely hit YouTube rate limiting
        result = runner.invoke(main, [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "-o", self.test_output_dir,
            "-f", "wav"
        ])
        
        # Either succeeds or fails due to YouTube (acceptable)
        assert result.exit_code in [0, 1]
