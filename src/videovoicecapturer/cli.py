"""CLI interface for VideoVoiceCapturer."""

import sys
import concurrent.futures
from pathlib import Path

import click

from .extractor import AudioExtractor, AudioExtractionError


@click.command()
@click.argument("urls", nargs=-1, required=True)
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
@click.option(
    "-j", "--jobs", "max_workers",
    default=1,
    type=int,
    help="Number of parallel downloads (default: 1)"
)
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Continue processing remaining URLs if one fails"
)
def main(urls: tuple, output_dir: str, format: str, verbose: bool, max_workers: int, continue_on_error: bool):
    """Extract audio from YouTube videos.
    
    URL: One or more YouTube video URLs
    
    Examples:
    
        # Single video
        vvc "https://youtube.com/watch?v=..." -o ./output -f mp3
        
        # Multiple videos (batch)
        vvc "url1" "url2" "url3" -o ./output -f mp3
        
        # Parallel processing (3 at a time)
        vvc "url1" "url2" "url3" "url4" "url5" -j 3
    """
    urls = list(urls)
    
    # Validate output directory
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    elif output_path.is_file():
        click.echo(f"✗ Error: Output path '{output_dir}' is a file, not a directory", err=True)
        sys.exit(1)
    
    # Validate format
    format = format.lower().lstrip(".")
    
    # Show initial info for single URL or batch
    if len(urls) == 1:
        if verbose:
            click.echo(f"Extracting from: {urls[0]}")
            click.echo(f"Output format: {format}")
            click.echo(f"Output directory: {output_dir}")
    else:
        click.echo(f"Processing {len(urls)} URLs (parallel: {max_workers})")
    
    # Process URLs
    results = {"success": [], "failed": []}
    
    if max_workers > 1:
        # Parallel processing
        results = _process_parallel(urls, output_dir, format, verbose, max_workers, continue_on_error)
    else:
        # Sequential processing
        results = _process_sequential(urls, output_dir, format, verbose, continue_on_error)
    
    # Summary
    click.echo(f"\n{'='*40}")
    click.echo(f"✓ Success: {len(results['success'])}")
    click.echo(f"✗ Failed: {len(results['failed'])}")
    
    if results["failed"]:
        click.echo("\nFailed URLs:")
        for url, error in results["failed"]:
            click.echo(f"  - {url}")
            click.echo(f"    Error: {error}")
    
    # Exit with error if any failed
    if results["failed"] and not continue_on_error:
        sys.exit(1)


def _process_sequential(urls: list, output_dir: str, format: str, verbose: bool, continue_on_error: bool) -> dict:
    """Process URLs sequentially."""
    results = {"success": [], "failed": []}
    
    for i, url in enumerate(urls, 1):
        if len(urls) > 1:
            click.echo(f"\n[{i}/{len(urls)}] {url}")
        
        try:
            extractor = AudioExtractor(output_dir)
            output_file = extractor.extract(url, format=format, verbose=verbose)
            results["success"].append((url, output_file))
            click.echo(f"✓ Saved: {output_file}")
        except Exception as e:
            error_msg = str(e)
            results["failed"].append((url, error_msg))
            click.echo(f"✗ Error: {error_msg}", err=True)
            
            if not continue_on_error:
                raise
    
    return results


def _process_parallel(urls: list, output_dir: str, format: str, verbose: bool, max_workers: int, continue_on_error: bool) -> dict:
    """Process URLs in parallel."""
    results = {"success": [], "failed": []}
    
    def process_single(url: str) -> tuple:
        """Process a single URL. Returns (success, url, output_file_or_error)."""
        try:
            extractor = AudioExtractor(output_dir)
            output_file = extractor.extract(url, format=format, verbose=verbose)
            return (True, url, output_file)
        except Exception as e:
            return (False, url, str(e))
    
    # Show progress for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single, url): url for url in urls}
        
        completed = 0
        total = len(futures)
        
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            success, url, result = future.result()
            
            if success:
                results["success"].append((url, result))
                click.echo(f"[{completed}/{total}] ✓ {url}")
            else:
                results["failed"].append((url, result))
                click.echo(f"[{completed}/{total}] ✗ {url}: {result}", err=True)
                
                if not continue_on_error:
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break
    
    return results


if __name__ == "__main__":
    main()