# VIdeoVoiceCapturer

CLI tool to capture audio from YouTube videos and convert to .wav or .mp3 formats.

## Features

- Download audio from YouTube videos
- Convert to MP3 or WAV format
- Batch processing (multiple URLs)
- Parallel processing for faster downloads
- Error handling with continue-on-error option

## Installation

```bash
# Install dependencies
pip3 install -e .

# Install ffmpeg (macOS)
brew install ffmpeg

# Install ffmpeg (Ubuntu/Debian)
sudo apt install ffmpeg
```

## Quick Start

```bash
# Run from project directory
cd ~/ClawProjects/VIdeoVoiceCapturer

# Extract audio to MP3
./vvc "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ./output -f mp3
```

## Usage

```bash
# Single video (MP3)
./vvc "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ./music -f mp3

# Single video (WAV)
./vvc "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ./music -f wav

# Multiple videos (batch)
./vvc "url1" "url2" "url3" -o ./output -f mp3

# Parallel processing (3 at a time)
./vvc "url1" "url2" "url3" "url4" "url5" -j 3

# Continue on error (don't stop if one URL fails)
./vvc "url1" "url2" "url3" --continue-on-error

# Verbose output
./vvc "URL" -v
```

## Options

| Option | Description |
|--------|-------------|
| `URLS` | One or more YouTube video URLs |
| `-o, --output` | Output directory (default: current directory) |
| `-f, --format` | Output format: `mp3` or `wav` (default: wav) |
| `-v, --verbose` | Enable verbose output |
| `-j, --jobs` | Number of parallel downloads (default: 1) |
| `--continue-on-error` | Continue processing if one URL fails |

## Requirements

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://ffmpeg.org/)

## Project Structure

```
VIdeoVoiceCapturer/
├── vvc                     # Shell wrapper script
├── src/
│   └── videovoicecapturer/
│       ├── __init__.py
│       ├── cli.py          # CLI interface
│       └── extractor.py    # Core extraction logic
├── pyproject.toml
├── setup.py
└── README.md
```

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`

### YouTube download fails (403 error)
Try using a different client format or wait - YouTube sometimes rate-limits downloads.

### Python version deprecation warning
The tool works fine but shows a warning about Python 3.9 being deprecated. Consider upgrading to Python 3.10+.