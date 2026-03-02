"""VideoVoiceCapturer - Extract audio from YouTube videos and train voice models."""

from .extractor import AudioExtractor, AudioExtractionError
from .trainer import XTTSTrainer, XTTSTrainingError

__version__ = "0.2.0"
