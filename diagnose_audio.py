"""
Diagnostic script to find out why audio recording isn't working
"""
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write, read
import os

print("="*60)
print("AUDIO DIAGNOSTIC TOOL")
print("="*60)

# 1. Check available devices
print("\n1. CHECKING AUDIO DEVICES:")
print("-" * 60)
devices = sd.query_devices()
print(devices)
print("\nDefault input device:")
print(sd.query_devices(kind='input'))

# 2. Check if test_jargon.wav exists and has content
print("\n2. CHECKING test_jargon.wav FILE:")
print("-" * 60)
if os.path.exists("test_jargon.wav"):
    file_size = os.path.getsize("test_jargon.wav")
    print(f"✓ File exists")
    print(f"  Size: {file_size:,} bytes")
    
    if file_size > 1000:  # More than 1KB
        try:
            sr, data = read("test_jargon.wav")
            print(f"  Sample rate: {sr} Hz")
            print(f"  Duration: {len(data)/sr:.2f} seconds")
            print(f"  Data shape: {data.shape}")
            
            # Check if audio has actual content (not just silence)
            max_amplitude = np.max(np.abs(data))
            print(f"  Max amplitude: {max_amplitude}")
            
            if max_amplitude < 0.001:
                print("  ⚠️  WARNING: Audio appears to be silent or very quiet!")
            else:
                print("  ✓ Audio has content")
        except Exception as e:
            print(f"  ✗ Error reading WAV: {e}")
    else:
        print(f"  ⚠️  File is too small ({file_size} bytes) - likely empty")
else:
    print("✗ File does not exist")

# 3. Quick recording test
print("\n3. QUICK RECORDING TEST:")
print("-" * 60)
print("Recording 3 seconds in 2 seconds...")
print("SAY SOMETHING LOUD!")

import time
time.sleep(2)

try:
    print("🔴 RECORDING NOW...")
    audio_data = sd.rec(
        int(3 * 16000),
        samplerate=16000,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    print("⏹  Recording stopped")
    
    # Check the recording
    max_amplitude = np.max(np.abs(audio_data))
    print(f"\nRecording stats:")
    print(f"  Shape: {audio_data.shape}")
    print(f"  Max amplitude: {max_amplitude}")
    
    if max_amplitude < 0.001:
        print("  ✗ PROBLEM: Recording is silent!")
        print("\n  Possible causes:")
        print("    - Microphone permission not granted")
        print("    - Wrong input device selected")
        print("    - Microphone muted or very quiet")
    else:
        print("  ✓ Recording captured audio!")
        write("diagnostic_test.wav", 16000, audio_data)
        print("  Saved to diagnostic_test.wav - try playing it:")
        print("    afplay diagnostic_test.wav")
        
except Exception as e:
    print(f"✗ Recording failed: {e}")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)

