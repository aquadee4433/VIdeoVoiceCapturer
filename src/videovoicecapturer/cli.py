"""CLI interface for VideoVoiceCapturer."""

import sys
import click
from pathlib import Path

from .extractor import AudioExtractor


@click.command()
@click.argument("url")
@click.option(
    "-o", "--output", "output_dir",
    default=".",
    help="Output directory for audio files"
)
@click.option(
    "-f", "--format",
    type=click.Choice(["wav", "mp3"], case_sensitive=False),
    default="wav",
    help="Output audio format"
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
def main(url: str, output_dir: str, format: str, verbose: bool):
    """Extract audio from YouTube videos.
    
    URL: YouTube video URL
    
    Example:
    
        videovoicecapturer "https://youtube.com/watch?v=..." -o ./output -f mp3
    """
    try:
        if verbose:
            click.echo(f"Extracting from: {url}")
            click.echo(f"Output format: {format}")
            click.echo(f"Output directory: {output_dir}")
        
        extractor = AudioExtractor(output_dir)
        output_file = extractor.extract(url, format=format, verbose=verbose)
        
        click.echo(f"✓ Saved: {output_file}")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()