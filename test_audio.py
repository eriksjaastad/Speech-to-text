#!/usr/bin/env python3
"""
Simple test script for audio capture functionality.
Records 5 seconds of audio and saves it to test.wav.
"""

from src.audio_capture import record_audio, save_audio

def main():
    print("Testing audio capture...")

    # Record 5 seconds of audio
    audio_data, sample_rate = record_audio(5, 16000)

    # Save to test.wav
    save_audio(audio_data, sample_rate, "test.wav")

    print("✅ Test completed successfully!")
    print("📁 Audio saved to test.wav")
    print("🔊 To play back: afplay test.wav")

if __name__ == "__main__":
    main()
