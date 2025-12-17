import os
import sys
import time
import subprocess
import difflib
import wave
import contextlib

# Add src to path so we can import engine
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.engine import WhisperEngine
except ImportError:
    print("Error: Could not import src.engine. Make sure you are running this from the project root or tests directory.")
    sys.exit(1)

TEST_CASES = [
    {
        "text": "Hello world.",
        "description": "Short greeting",
        "difficulty": "Easy"
    },
    {
        "text": "The quick brown fox jumps over the lazy dog.",
        "description": "Standard pangram",
        "difficulty": "Medium"
    },
    {
        "text": "Voice activity detection is crucial for ignoring background noise.",
        "description": "Technical sentence",
        "difficulty": "Hard"
    },
    {
        "text": "This is a test of the emergency broadcast system.",
        "description": "Medium length sentence",
        "difficulty": "Medium"
    }
]

TEMP_FILENAME = "temp_test_audio.wav"

def generate_audio(text, filename):
    """Generates audio file using Mac's 'say' command."""
    # -o specifies output file, --data-format=LEF32@16000 specifies format compatible with many models
    # But Whisper usually handles standard wavs. Let's stick to default uncompressed or specific if needed.
    # 'say' creates AIFF by default on some older macs if .wav extension isn't respected or if arguments are weird.
    # modern 'say' with .wav usually works.
    try:
        subprocess.run(["say", "-o", filename, "--data-format=LEI16@16000", text], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating audio: {e}")
        return False

def similarity(s1, s2):
    """Calculates similarity ratio between two strings."""
    s1 = s1.lower().strip().replace(".", "").replace(",", "")
    s2 = s2.lower().strip().replace(".", "").replace(",", "")
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def run_suite():
    print(f"{'='*60}")
    print(f"STARTING VAD & TRANSCRIPTION DIAGNOSTIC SUITE")
    print(f"{'='*60}\n")

    print("Initializing Engine (this might take a few seconds)...")
    try:
        engine = WhisperEngine()
    except Exception as e:
        print(f"CRITICAL: Engine failed to initialize. {e}")
        return

    print("\nStarting Tests...\n")
    
    results = []

    for idx, case in enumerate(TEST_CASES):
        print(f"Test {idx+1}/{len(TEST_CASES)}: {case['description']} ({case['difficulty']})")
        print(f"  Prompt: \"{case['text']}\"")
        
        # 1. Generate Audio
        gen_start = time.time()
        if not generate_audio(case['text'], TEMP_FILENAME):
            print("  [FAIL] Audio generation failed.")
            continue
        
        # 2. Transcribe
        try:
            # We use the engine's transcribe method
            # Note: engine.transcribe returns a dict with 'text', 'duration', etc.
            result = engine.transcribe(TEMP_FILENAME)
            transcription = result['text']
            inference_time = result['inference_time']
            audio_duration = result['duration']
            
        except Exception as e:
            print(f"  [FAIL] Transcription crashed: {e}")
            results.append({"status": "CRASH", "case": case})
            continue

        # 3. Compare
        score = similarity(case['text'], transcription)
        passed = score > 0.8  # 80% similarity threshold

        status = "PASS" if passed else "WARN"
        if score < 0.5: status = "FAIL"
        
        print(f"  Result: \"{transcription}\"")
        print(f"  [{status}] Match: {score*100:.1f}% | Latency: {inference_time:.2f}s | Audio: {audio_duration:.2f}s")
        print("-" * 40)
        
        results.append({
            "status": status,
            "case": case,
            "score": score,
            "time": inference_time,
            "duration": audio_duration
        })

    # Cleanup
    if os.path.exists(TEMP_FILENAME):
        os.remove(TEMP_FILENAME)

    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC REPORT")
    print("="*60)
    
    passed_count = sum(1 for r in results if r['status'] == 'PASS')
    total = len(TEST_CASES)
    
    print(f"Passed: {passed_count}/{total}")
    
    avg_latency = sum(r['time'] for r in results) / total if results else 0
    print(f"Average Latency: {avg_latency:.2f}s")
    
    if passed_count == total:
        print("\nSUMMARY: SYSTEM GREEN. Ready for use.")
    else:
        print("\nSUMMARY: ISSUES DETECTED. See above for details.")
    print("="*60)

if __name__ == "__main__":
    run_suite()
