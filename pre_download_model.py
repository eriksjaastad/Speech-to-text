# pre_download_model.py
from faster_whisper import WhisperModel

print("Downloading large-v3 model... this may take 3-5 minutes.")
print("This only happens once - the model is cached locally.")

model = WhisperModel("large-v3", device="cpu", compute_type="int8")

print("✓ Model downloaded and cached!")
print("You can now proceed to audio testing.")
