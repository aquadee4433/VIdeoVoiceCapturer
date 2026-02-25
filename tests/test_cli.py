"""CLI tests for VideoVoiceCapturer."""

import pytest
import sys
from pathlib import Path
from click.testing import CliRunner

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from videovoicecapturer.cli import main


class TestCLI:
    """Tests for CLI interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Extract audio" in result.output

    def test_cli_missing_url(self):
        """Test CLI fails without URL."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code != 0

    def test_cli_invalid_format(self):
        """Test CLI fails with invalid format."""
        runner = CliRunner()
        result = runner.invoke(main, ["https://youtube.com/watch?v=abc", "-f", "invalid"])
        assert result.exit_code != 0
