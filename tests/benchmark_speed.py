import sys
import os
import time
import subprocess
import yaml

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.engine import WhisperEngine
except ImportError:
    print("Error: Could not import src.engine")
    sys.exit(1)

TEST_PHRASE = "The quick brown fox jumps over the lazy dog. Voice activity detection is crucial for ignoring background noise."
AUDIO_FILE = "benchmark_audio.wav"

CONFIGS_TO_TEST = [
    {"name": "Baseline (Medium, Beam 5)", "model": "distil-medium.en", "beam": 5},
    {"name": "Turbo (Medium, Beam 1)", "model": "distil-medium.en", "beam": 1},
    {"name": "Fast (Small, Beam 1)", "model": "distil-small.en", "beam": 1},
    {"name": "Lightning (Tiny, Beam 1)", "model": "tiny.en", "beam": 1},
]

def generate_audio():
    print(f"Generating test audio: '{TEST_PHRASE}'")
    subprocess.run(["say", "-o", AUDIO_FILE, "--data-format=LEI16@16000", TEST_PHRASE], check=True)

def run_benchmark():
    if not os.path.exists(AUDIO_FILE):
        generate_audio()

    results = []
    
    print("\n" + "="*80)
    print(f"{'CONFIGURATION':<30} | {'LOAD TIME':<10} | {'TRANSCRIBE':<10} | {'RTF':<6} | {'TEXT'}")
    print("="*80)

    for conf in CONFIGS_TO_TEST:
        # Create config dict for engine
        engine_config = {
            "whisper": {
                "model": conf["model"],
                "device": "cpu",
                "compute_type": "int8"
            }
        }

        # Measure Load Time
        t0 = time.time()
        engine = WhisperEngine(config=engine_config)
        load_time = time.time() - t0

        # Warmup (optional, but good for JIT/caching)
        engine.transcribe(AUDIO_FILE, beam_size=conf["beam"])

        # Measure Transcription Time
        t1 = time.time()
        result = engine.transcribe(AUDIO_FILE, beam_size=conf["beam"])
        transcribe_time = time.time() - t1
        
        audio_duration = result['duration']
        rtf = transcribe_time / audio_duration if audio_duration > 0 else 0
        
        print(f"{conf['name']:<30} | {load_time:<9.2f}s | {transcribe_time:<9.2f}s | {rtf:<6.2f} | {result['text'][:30]}...")
        
        results.append({
            "config": conf,
            "transcribe_time": transcribe_time,
            "text": result['text']
        })

    print("="*80)
    
    # Clean up
    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)

    # Recommend
    best = min(results, key=lambda x: x['transcribe_time'])
    print(f"\n🏆 WINNER: {best['config']['name']} ({best['transcribe_time']:.2f}s)")
    
if __name__ == "__main__":
    run_benchmark()
