# VideoVoiceCapturer

CLI tool to capture audio from YouTube videos and train voice cloning models.

## Features

- **Audio Extraction**: Download audio from YouTube videos
- **Voice Training**: Train custom voice models using Coqui XTTS v2
- **Batch Processing**: Process multiple URLs in parallel
- **Format Conversion**: Convert to MP3 or WAV format

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

### Extract Audio

```bash
# Run from project directory
cd ~/ClawProjects/VIdeoVoiceCapturer

# Extract audio to MP3
./vvc extract "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ./output -f mp3
```

### Train Voice Model

```bash
# 1. Extract audio from videos of your voice
./vvc extract "https://youtube.com/..." -o ./audio -f wav

# 2. Prepare dataset for training
./vvc prepare audio1.wav audio2.wav audio3.wav -o ./dataset -n myvoice

# 3. Train the model
./vvc train -d ./dataset/myvoice -o ./models -n myvoice -e 50

# 4. Generate speech with your voice
./vvc infer "Hello world" -m ./models/myvoice.pth -o hello.wav
```

## Commands

### extract - Extract audio from YouTube

```bash
# Single video (MP3)
./vvc extract "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ./music -f mp3

# Single video (WAV)
./vvc extract "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ./music -f wav

# Multiple videos (batch)
./vvc extract "url1" "url2" "url3" -o ./output -f mp3

# Parallel processing (3 at a time)
./vvc extract "url1" "url2" "url3" "url4" "url5" -j 3

# Continue on error (don't stop if one URL fails)
./vvc extract "url1" "url2" "url3" --continue-on-error

# Verbose output
./vvc extract "URL" -v
```

### prepare - Prepare audio for training

```bash
# Prepare audio files for XTTS training
./vvc prepare audio1.wav audio2.wav audio3.wav -o ./dataset -n myvoice

# Options:
#   -o, --output    Output directory (default: ./dataset)
#   -n, --name      Model name (default: myvoice)
#   -v, --verbose   Enable verbose output
```

### train - Train XTTS voice model

```bash
# Train with default settings (50 epochs)
./vvc train -d ./dataset/myvoice -o ./models -n myvoice

# Train with custom settings
./vvc train -d ./dataset/myvoice -e 100 -b 4 -o ./models

# Options:
#   -d, --dataset    Path to prepared dataset (required)
#   -o, --output     Output directory (default: ./models)
#   -n, --name       Model name (default: myvoice)
#   -e, --epochs     Number of epochs (default: 50)
#   -b, --batch-size Batch size (default: 8)
#   -v, --verbose    Enable verbose output
```

### infer - Generate speech

```bash
# Generate speech with trained model
./vvc infer "Hello world" -m ./models/myvoice.pth -o hello.wav

# Options:
#   TEXT              Text to synthesize (required)
#   -m, --model       Path to trained model (required)
#   -o, --output      Output file (default: output.wav)
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

### Audio Extraction
- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://ffmpeg.org/)

### Voice Training
- Python 3.9+
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- PyTorch
- CUDA (optional, for GPU acceleration)

## Project Structure

```
VIdeoVoiceCapturer/
├── vvc                     # Shell wrapper script
├── src/
│   └── videovoicecapturer/
│       ├── __init__.py
│       ├── cli.py          # CLI interface
│       ├── extractor.py    # Audio extraction logic
│       └── trainer.py      # XTTS training logic
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

### XTTS training is slow
- Use GPU acceleration (CUDA)
- Reduce batch size if running out of memory
- Start with fewer epochs for testing

### Python version deprecation warning
The tool works fine but shows a warning about Python 3.9 being deprecated. Consider upgrading to Python 3.10+.

## Voice Training Tips

1. **Audio Quality**: Use high-quality audio sources (ideally 44.1kHz+)
2. **Duration**: 30+ minutes of clean speech recommended
3. **Variety**: Include different sentences, tones, and speaking styles
4. **Transcripts**: Edit the generated `metadata.csv` with accurate transcripts
5. **Epochs**: Start with 50 epochs, increase if quality is poor
