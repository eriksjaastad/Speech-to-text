from src.engine import WhisperEngine, load_vocab
from src.audio_capture import record_audio, save_audio

# Load vocabulary
vocab = load_vocab()
print(f"Loaded {len(vocab)} custom terms")
print("Terms:", ", ".join(vocab))

# Initialize engine
engine = WhisperEngine()

# Record audio
print("\n" + "="*60)
print("RECORDING JARGON TEST")
print("="*60)
print("Say some jargon terms like:")
print("  - 'I'm trading MNQ on TradeZella'")
print("  - 'Spin up a Runpod instance with Ollama'")
print("  - 'Check the Victron battery in Cochise County'")
print("\nRecording in 3 seconds...")

import time
time.sleep(3)

# Record 10 seconds for a full sentence
audio, sr = record_audio(duration=10)
save_audio(audio, sr, "test_jargon.wav")

# Transcribe with vocabulary injection
print("\n" + "="*60)
print("TRANSCRIBING WITH VOCABULARY INJECTION")
print("="*60)

result = engine.transcribe("test_jargon.wav", custom_vocab=vocab)

print(f"\nTranscription: {result['text']}")
print(f"Inference time: {result['inference_time']:.2f}s")

print("\n" + "="*60)
print("SUCCESS! Check if your jargon terms were recognized correctly.")
print("="*60)
