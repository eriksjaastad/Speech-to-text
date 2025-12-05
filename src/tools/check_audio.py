import sounddevice as sd
import numpy as np
import time

def check_audio():
    print("="*60)
    print("AUDIO DIAGNOSTICS")
    print("="*60)
    
    # 1. List Devices
    print("\n1. Listing Input Devices:")
    devices = sd.query_devices()
    default_input = sd.default.device[0]
    
    found_valid = False
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            mark = "★" if i == default_input else " "
            print(f"{mark} [{i}] {dev['name']}")
            found_valid = True
            
    if not found_valid:
        print("❌ No input devices found!")
        return

    print(f"\nUsing Default Device: {default_input} ({devices[default_input]['name']})")

    # 2. Test Recording
    print("\n2. Testing Input Levels (Speak now!)...")
    duration = 3  # seconds
    fs = 16000
    
    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        for i in range(duration):
            print(f"   Recording {i+1}/{duration}...", end="\r")
            time.sleep(1)
        sd.wait()
        print("\n   Done.")
        
        # 3. Analyze Amplitude
        max_amp = np.max(np.abs(recording))
        mean_amp = np.mean(np.abs(recording))
        
        print(f"\n3. Results:")
        print(f"   Max Amplitude:  {max_amp:.4f}")
        print(f"   Mean Amplitude: {mean_amp:.4f}")
        
        if max_amp < 0.01:
            print("\n❌ SILENCE DETECTED. The app is hearing nothing.")
            print("   -> Check System Settings > Sound > Input")
            print("   -> Check if the microphone is muted")
        else:
            print("\n✓ Audio detected! The microphone works.")
            
    except Exception as e:
        print(f"\n❌ Recording failed: {e}")

if __name__ == "__main__":
    check_audio()
