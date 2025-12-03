import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import sys
import os

def record_audio(duration=5, sample_rate=16000):
    """
    Records audio from the default microphone.

    Args:
        duration (int): Recording duration in seconds (default: 5)
        sample_rate (int): Sample rate in Hz (default: 16000)

    Returns:
        tuple: (audio_data, sample_rate) where audio_data is a numpy array
    """
    print(f"Recording {duration} seconds of audio at {sample_rate} Hz...")

    # Record audio
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )

    # Wait for recording to complete
    sd.wait()

    print("Recording completed.")
    return audio_data, sample_rate

def save_audio(audio_data, sample_rate, filename="test.wav"):
    """
    Saves audio data to a WAV file.

    Args:
        audio_data (numpy.ndarray): Audio data array
        sample_rate (int): Sample rate in Hz
        filename (str): Output filename (default: "test.wav")
    """
    # Ensure the audio data is in the correct format
    if audio_data.ndim > 1:
        audio_data = audio_data.flatten()

    # Normalize to int16 range for WAV file
    audio_int16 = (audio_data * 32767).astype(np.int16)

    # Save to WAV file
    wav.write(filename, sample_rate, audio_int16)
    print(f"Audio saved to {filename}")

if __name__ == "__main__":
    # Record 5 seconds and save to test.wav
    audio_data, sample_rate = record_audio(5, 16000)
    save_audio(audio_data, sample_rate, "test.wav")
