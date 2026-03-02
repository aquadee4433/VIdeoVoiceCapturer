"""CLI interface for VideoVoiceCapturer."""

import sys
import concurrent.futures
from pathlib import Path

import click

from .extractor import AudioExtractor, AudioExtractionError
from .trainer import XTTSTrainer, XTTSTrainingError


@click.group()
def cli():
    """VideoVoiceCapturer - Extract audio and train voice models."""
    pass


@cli.command("extract")
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
def extract(urls: tuple, output_dir: str, format: str, verbose: bool, max_workers: int, continue_on_error: bool):
    """Extract audio from YouTube videos.
    
    URL: One or more YouTube video URLs
    
    Examples:
    
        # Single video
        vvc extract "https://youtube.com/watch?v=..." -o ./output -f mp3
        
        # Multiple videos (batch)
        vvc extract "url1" "url2" "url3" -o ./output -f mp3
        
        # Parallel processing (3 at a time)
        vvc extract "url1" "url2" "url3" "url4" "url5" -j 3
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


@cli.command("prepare")
@click.argument("audio_files", nargs=-1, required=True)
@click.option(
    "-o", "--output", "output_dir",
    default="./dataset",
    help="Output directory for prepared dataset"
)
@click.option(
    "-n", "--name", "model_name",
    default="myvoice",
    help="Name for the voice model"
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
def prepare(audio_files: tuple, output_dir: str, model_name: str, verbose: bool):
    """Prepare audio files for XTTS voice training.
    
    AUDIO_FILES: One or more audio files (wav/mp3)
    
    Examples:
    
        # Prepare audio files
        vvc prepare audio1.wav audio2.wav audio3.wav -o ./dataset -n myvoice
    """
    audio_files = list(audio_files)
    
    click.echo(f"Preparing {len(audio_files)} audio files for training...")
    
    try:
        trainer = XTTSTrainer(
            dataset_path=output_dir,
            output_dir=output_dir,
            model_name=model_name
        )
        
        dataset_path = trainer.prepare_dataset(audio_files)
        
        click.echo(f"\n✓ Dataset prepared: {dataset_path}")
        click.echo("\nNote: Edit metadata.csv with actual transcripts for better results!")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command("train")
@click.option(
    "-d", "--dataset", "dataset_path",
    required=True,
    help="Path to prepared dataset directory"
)
@click.option(
    "-o", "--output", "output_dir",
    default="./models",
    help="Output directory for trained model"
)
@click.option(
    "-n", "--name", "model_name",
    default="myvoice",
    help="Name for the voice model"
)
@click.option(
    "-e", "--epochs",
    default=50,
    type=int,
    help="Number of training epochs (default: 50)"
)
@click.option(
    "-b", "--batch-size",
    default=8,
    type=int,
    help="Batch size (default: 8)"
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
def train(dataset_path: str, output_dir: str, model_name: str, epochs: int, batch_size: int, verbose: bool):
    """Train XTTS v2 voice model from prepared dataset.
    
    Examples:
    
        # Train with default settings
        vvc train -d ./dataset/myvoice -o ./models -n myvoice
        
        # Train for more epochs
        vvc train -d ./dataset/myvoice -e 100 -b 4
    """
    click.echo(f"Training XTTS v2 voice model: {model_name}")
    click.echo(f"Dataset: {dataset_path}")
    click.echo(f"Epochs: {epochs}, Batch size: {batch_size}")
    
    try:
        trainer = XTTSTrainer(
            dataset_path=dataset_path,
            output_dir=output_dir,
            model_name=model_name
        )
        
        model_path = trainer.train(
            dataset_path=dataset_path,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose
        )
        
        click.echo(f"\n✓ Training complete!")
        click.echo(f"✓ Model saved: {model_path}")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command("infer")
@click.argument("text", required=True)
@click.option(
    "-m", "--model", "model_path",
    required=True,
    help="Path to trained XTTS model"
)
@click.option(
    "-o", "--output", "output_path",
    default="output.wav",
    help="Output audio file path"
)
def infer(text: str, model_path: str, output_path: str):
    """Generate speech using trained XTTS voice model.
    
    TEXT: Text to synthesize
    
    Examples:
    
        # Generate speech
        vvc infer "Hello world" -m ./models/myvoice.pth -o hello.wav
    """
    click.echo(f"Generating speech: '{text}'")
    click.echo(f"Model: {model_path}")
    
    try:
        trainer = XTTSTrainer(
            dataset_path=".",
            output_dir=Path(model_path).parent,
            model_name=Path(model_path).stem
        )
        
        output = trainer.infer(
            text=text,
            model_path=model_path,
            output_path=output_path
        )
        
        click.echo(f"\n✓ Generated: {output}")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
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
    cli()
