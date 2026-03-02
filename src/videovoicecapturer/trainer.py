"""XTTS v2 Voice Model Training for VideoVoiceCapturer."""

import os
import subprocess
from pathlib import Path
from typing import Optional, List
import shutil


class XTTSTrainingError(Exception):
    """Custom exception for XTTS training errors."""
    pass


class XTTSTrainer:
    """Train voice cloning models using Coqui XTTS v2."""
    
    def __init__(
        self,
        dataset_path: str,
        output_dir: str = "./models",
        model_name: str = "myvoice"
    ):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.model_name = model_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _check_dependencies(self) -> bool:
        """Check if XTTS is installed."""
        try:
            result = subprocess.run(
                ["python3", "-c", "from TTS.api import TTS; print('ok')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _install_xtts(self) -> None:
        """Install XTTS v2 dependencies."""
        print("Installing XTTS v2 (this may take a while)...")
        subprocess.run(
            ["pip3", "install", "tts", "scipy", "numpy"],
            check=True
        )
    
    def prepare_dataset(self, audio_files: List[str]) -> Path:
        """
        Prepare audio files for training.
        
        Args:
            audio_files: List of audio file paths
            
        Returns:
            Path to prepared dataset directory
        """
        import numpy as np
        from scipy.io import wavfile
        
        dataset_dir = self.output_dir / "dataset" / self.model_name
        wav_dir = dataset_dir / "wavs"
        wav_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Preparing dataset from {len(audio_files)} files...")
        
        for i, audio_file in enumerate(audio_files):
            audio_path = Path(audio_file)
            if not audio_path.exists():
                print(f"Warning: File not found: {audio_file}")
                continue
            
            # Load and normalize audio
            try:
                sample_rate, audio = wavfile.read(audio_path)
                
                # Convert to float32 and normalize
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32)
                    if audio.max() > 1:
                        audio = audio / 32768.0
                
                # Resample to 22050 Hz if needed
                if sample_rate != 22050:
                    audio = self._resample_audio(audio, sample_rate, 22050)
                    sample_rate = 22050
                
                # Remove silence
                audio = self._remove_silence(audio)
                
                # Save processed audio
                output_path = wav_dir / f"audio_{i:04d}.wav"
                wavfile.write(output_path, 22050, (audio * 32768).astype(np.int16))
                
                print(f"  ✓ Processed: {audio_path.name}")
                
            except Exception as e:
                print(f"  ✗ Error processing {audio_path.name}: {e}")
        
        # Create metadata file
        self._create_metadata(dataset_dir, wav_dir)
        
        print(f"Dataset prepared at: {dataset_dir}")
        return dataset_dir
    
    def _resample_audio(self, audio, orig_sr: int, target_sr: int):
        """Resample audio to target sample rate."""
        try:
            import librosa
            return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
        except ImportError:
            # Fallback: simple decimation/interpolation
            import numpy as np
            if target_sr < orig_sr:
                ratio = target_sr / orig_sr
                return audio[::int(1/ratio)]
            else:
                # Simple zero-padding interpolation
                ratio = target_sr / orig_sr
                new_length = int(len(audio) * ratio)
                indices = np.linspace(0, len(audio) - 1, new_length)
                return np.interp(indices, np.arange(len(audio)), audio)
    
    def _remove_silence(self, audio):
        """Remove silent portions from audio."""
        import numpy as np
        
        threshold = 0.01
        # Find non-silent segments
        mask = np.abs(audio) > threshold
        if not mask.any():
            return audio
        
        # Find contiguous non-silent regions
        indices = np.where(mask)[0]
        if len(indices) == 0:
            return audio
        
        start = indices[0]
        end = indices[-1]
        
        return audio[start:end+1]
    
    def _create_metadata(self, dataset_dir: Path, wav_dir: Path) -> None:
        """Create metadata file for XTTS training."""
        import csv
        
        metadata_path = dataset_dir / "metadata.csv"
        
        with open(metadata_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='|')
            writer.writerow(['audio', 'text', 'duration'])
            
            for wav_file in sorted(wav_dir.glob("*.wav")):
                # Use filename as text (placeholder - user should edit with actual transcripts)
                text = wav_file.stem.replace('_', ' ')
                writer.writerow([f"wavs/{wav_file.name}", text, ""])
        
        print(f"Metadata created: {metadata_path}")
    
    def train(
        self,
        dataset_path: Optional[str] = None,
        epochs: int = 50,
        batch_size: int = 8,
        grad_accum: int = 4,
        verbose: bool = False
    ) -> Path:
        """
        Train XTTS v2 voice model.
        
        Args:
            dataset_path: Path to prepared dataset (uses self.dataset_path if None)
            epochs: Number of training epochs
            batch_size: Batch size
            grad_accum: Gradient accumulation steps
            verbose: Enable verbose output
            
        Returns:
            Path to trained model
        """
        dataset = Path(dataset_path) if dataset_path else self.dataset_path
        
        if not dataset.exists():
            raise XTTSTrainingError(f"Dataset not found: {dataset}")
        
        print(f"Training XTTS v2 model: {self.model_name}")
        print(f"Dataset: {dataset}")
        print(f"Epochs: {epochs}, Batch size: {batch_size}")
        
        # Check if XTTS is available
        if not self._check_dependencies():
            self._install_xtts()
        
        # Training command using Coqui's training script
        # XTTS v2 uses the train_tts.py from the TTS repository
        train_cmd = [
            "python3", "-m", "TTS.train",
            "--model", "xtts",
            "--dataset_path", str(dataset),
            "--output_path", str(self.output_dir / "training"),
            "--epochs", str(epochs),
            "--batch_size", str(batch_size),
            "--grad_accum_steps", str(grad_accum),
        ]
        
        if not verbose:
            train_cmd.append("--progress_bar")
        
        print(f"Running: {' '.join(train_cmd)}")
        
        try:
            result = subprocess.run(
                train_cmd,
                check=True,
                capture_output=not verbose,
                text=True,
                timeout=None  # Training takes a while
            )
            
            if result.returncode != 0:
                raise XTTSTrainingError(f"Training failed: {result.stderr}")
            
            print("✓ Training completed!")
            
        except subprocess.CalledProcessError as e:
            raise XTTSTrainingError(f"Training command failed: {e.stderr}")
        
        # Find and return the trained model
        model_path = self.output_dir / "training" / "best_model.pth"
        
        if not model_path.exists():
            # Try alternate locations
            for pattern in ["*.pth", "*.pt", "**/model.pth"]:
                matches = list((self.output_dir / "training").glob(pattern))
                if matches:
                    model_path = matches[0]
                    break
        
        if not model_path.exists():
            raise XTTSTrainingError("Trained model not found!")
        
        # Copy to final location
        final_model_path = self.output_dir / f"{self.model_name}.pth"
        shutil.copy(model_path, final_model_path)
        
        print(f"✓ Model saved: {final_model_path}")
        return final_model_path
    
    def infer(
        self,
        text: str,
        model_path: Optional[str] = None,
        output_path: str = "output.wav"
    ) -> str:
        """
        Generate speech using trained XTTS model.
        
        Args:
            text: Text to synthesize
            model_path: Path to trained model (uses default if None)
            output_path: Output file path
            
        Returns:
            Path to generated audio file
        """
        from TTS.api import TTS
        
        model_file = model_path or str(self.output_dir / f"{self.model_name}.pth")
        
        if not Path(model_file).exists():
            raise XTTSTrainingError(f"Model not found: {model_file}")
        
        print(f"Generating speech: '{text}'")
        
        try:
            tts = TTS(model_path=model_file)
            tts.tts(
                text=text,
                file_path=output_path
            )
            
            print(f"✓ Generated: {output_path}")
            return output_path
            
        except Exception as e:
            raise XTTSTrainingError(f"Inference failed: {e}")
