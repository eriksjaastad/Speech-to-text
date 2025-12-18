#!/usr/bin/env python3
"""
Test Corpus Recording Helper

Guides you through recording the test corpus with clear prompts.
Each test is designed to expose specific failure modes.
"""

import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from pathlib import Path
import time

# Test scenarios - deliberately difficult
TEST_SCENARIOS = [
    {
        "id": "01_quick_phrase",
        "duration": 3,
        "prompt": "Test number one",
        "why": "Tests pre-roll buffer captures first word"
    },
    {
        "id": "02_medium_sentence",
        "duration": 10,
        "prompt": "I'm trading MNQ futures on TradeZella today",
        "why": "Baseline jargon test"
    },
    {
        "id": "03_long_dictation",
        "duration": 30,
        "prompt": "(Say a natural paragraph about trading or tech - 20-30 seconds)",
        "why": "Tests sustained recording"
    },
    {
        "id": "04_jargon_heavy",
        "duration": 10,
        "prompt": "Check Runpod, Ollama, and Victron in Cochise County",
        "why": "Multiple jargon terms"
    },
    {
        "id": "05_trailing_important",
        "duration": 8,
        "prompt": "The three requirements are speed, accuracy, and the most important one is reliability",
        "why": "TAIL-CUTOFF TEST - last word critical"
    },
    {
        "id": "06_mid_pause",
        "duration": 10,
        "prompt": "I was thinking... [1s pause] about the MNQ trade",
        "why": "PAUSE TEST - pause doesn't truncate"
    },
    {
        "id": "07_long_pause",
        "duration": 15,
        "prompt": "First point is speed. [3s pause] Second point is accuracy.",
        "why": "PAUSE TEST - long pause, then continue"
    },
    {
        "id": "08_fast_stop",
        "duration": 3,
        "prompt": "Quick test stop [then immediately stop]",
        "why": "Tests if recording captures tail"
    },
    {
        "id": "09_breath_then_final",
        "duration": 12,
        "prompt": "Those are the main points. [breath, 1s pause] Oh and one more thing, reliability matters most.",
        "why": "TAIL-CUTOFF TEST - restart at end"
    },
    {
        "id": "10_two_sentences_end",
        "duration": 10,
        "prompt": "That's the summary. Got it? Good.",
        "why": "TAIL-CUTOFF TEST - multiple sentences at end"
    },
]

SAMPLE_RATE = 16000

def record_audio(duration, sample_rate=16000):
    """Record audio from default microphone."""
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    return audio_data

def main():
    # Create corpus directory
    corpus_dir = Path("test_data/corpus")
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("TEST CORPUS RECORDER")
    print("=" * 70)
    print(f"\nThis will guide you through recording {len(TEST_SCENARIOS)} test clips.")
    print("Each test is designed to expose specific failure modes.\n")
    print("You can skip tests by typing 'skip' when prompted for ground truth.\n")
    
    input("Press Enter to start...")
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print("\n" + "=" * 70)
        print(f"TEST {i}/{len(TEST_SCENARIOS)}: {scenario['id']}")
        print("=" * 70)
        print(f"\n📝 What to say:")
        print(f"   \"{scenario['prompt']}\"")
        print(f"\n🎯 Why: {scenario['why']}")
        print(f"\n⏱  Duration: {scenario['duration']} seconds")
        
        input("\nReady? Press Enter to start countdown...")
        
        # Countdown
        for count in [3, 2, 1]:
            print(f"   {count}...")
            time.sleep(1)
        
        print("   🔴 RECORDING!\n")
        
        # Record
        audio = record_audio(scenario['duration'], SAMPLE_RATE)
        
        print("   ⏹  Done!\n")
        
        # Save audio
        audio_path = corpus_dir / f"{scenario['id']}.wav"
        write(audio_path, SAMPLE_RATE, audio)
        print(f"✅ Saved: {audio_path}")
        
        # Prompt for ground truth
        print("\n📄 Now type the EXACT text you said (ground truth):")
        print("   (Or type 'skip' to skip this test, or 'replay' to listen)")
        
        while True:
            ground_truth = input("   > ").strip()
            
            if ground_truth.lower() == 'skip':
                print("   ⏭  Skipped")
                audio_path.unlink()  # Delete the audio file
                break
            elif ground_truth.lower() == 'replay':
                print("   🔊 Playing back...")
                sd.play(audio, SAMPLE_RATE)
                sd.wait()
                continue
            elif ground_truth:
                # Save ground truth
                txt_path = corpus_dir / f"{scenario['id']}.txt"
                txt_path.write_text(ground_truth)
                print(f"✅ Saved: {txt_path}")
                break
            else:
                print("   ⚠️  Ground truth cannot be empty. Try again or type 'skip'.")
    
    print("\n" + "=" * 70)
    print("CORPUS RECORDING COMPLETE!")
    print("=" * 70)
    
    # Count files
    wav_files = list(corpus_dir.glob("*.wav"))
    txt_files = list(corpus_dir.glob("*.txt"))
    
    print(f"\n✅ {len(wav_files)} audio files")
    print(f"✅ {len(txt_files)} ground truth files")
    
    if len(wav_files) == len(txt_files) == len(TEST_SCENARIOS):
        print("\n🎉 All tests recorded! Ready to run test_runner.py")
    else:
        print(f"\n⚠️  Expected {len(TEST_SCENARIOS)} files of each type.")
        print("   You can re-run this script to record missing tests.")
    
    print(f"\nFiles saved to: {corpus_dir.absolute()}")

if __name__ == "__main__":
    main()

