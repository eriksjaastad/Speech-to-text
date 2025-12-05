from faster_whisper import WhisperModel
import time
import yaml

def load_settings(path="config/settings.yaml"):
    """Load settings with safe defaults."""
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load {path}: {e}")
        print("Using default settings")
        return {
            "whisper": {
                "model": "large-v3",
                "device": "cpu",
                "compute_type": "int8"
            }
        }

def load_vocab(path="config/vocab.yaml"):
    """Load custom vocabulary terms with safe defaults."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("custom_terms", [])
    except Exception as e:
        print(f"Warning: Could not load {path}: {e}")
        return []  # Empty list is safe default

class WhisperEngine:
    def __init__(self, config=None, model=None):
        """Initialize Whisper model from config or use provided model."""
        if model is not None:
            # Use provided model (for testing/performance)
            self.model = model
            print("Using provided model instance")
        else:
            # Load model from config
            if config is None:
                config = load_settings()

            whisper_config = config.get("whisper", {})
            model_size = whisper_config.get("model", "large-v3")
            device = whisper_config.get("device", "cpu")
            compute_type = whisper_config.get("compute_type", "int8")

            print(f"Loading {model_size} model (device={device}, compute={compute_type})...")
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
            print("Model loaded!")

    def transcribe(self, audio_path, language="en", custom_vocab=None):
        """Transcribe audio file with optional vocab injection."""
        start_time = time.time()

        # Build initial_prompt if vocab provided
        # NOTE: initial_prompt was causing truncated transcriptions!
        # Disabled for now - vocab will be handled via post-processing regex instead
        initial_prompt = None
        # if custom_vocab:
        #     initial_prompt = "Key terms: " + ", ".join(custom_vocab) + "."

        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            # initial_prompt disabled - was breaking transcription
            # initial_prompt=initial_prompt,
            beam_size=5,
            temperature=0.0,
            condition_on_previous_text=False,
            # VAD temporarily disabled for debugging
            # vad_filter=True,
            # vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Collect all segments
        text = " ".join([seg.text for seg in segments])

        elapsed = time.time() - start_time

        return {
            "text": text.strip(),
            "language": info.language,
            "duration": info.duration,
            "inference_time": elapsed
        }

if __name__ == "__main__":
    engine = WhisperEngine()  # Uses config/settings.yaml
    result = engine.transcribe("test.wav")

    print("\n" + "="*60)
    print("TRANSCRIPTION RESULT")
    print("="*60)
    print(f"Text: {result['text']}")
    print(f"Audio duration: {result['duration']:.2f}s")
    print(f"Inference time: {result['inference_time']:.2f}s")
    print(f"Latency acceptable: {'✓ YES' if result['inference_time'] < 3.0 else '✗ NO - Consider smaller model'}")
    print("="*60)
