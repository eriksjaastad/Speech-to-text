# Erik STT — Build TODO List

**Created:** December 2, 2025  
**Updated:** December 13, 2025 (Core Requirements Clarified)  
**Based on:** ERIK_STT_FINAL_PROJECT_DOC.md  
**Goal:** Build v1 in one day, then iterate

---

## 🎯 CORE REQUIREMENTS (Updated December 13, 2025)

**Context:** Erik uses speech-to-text 1000+ times per day, primarily for interacting with AI assistants (Claude, ChatGPT, etc.). This is life-critical infrastructure - more usage than his phone. SuperWhisper is the current tool but has two major pain points.

### Primary Success Criteria:
1. **Zero hallucinations** - Specifically no repetition loops ("same sentence 10 times")
2. **Speed matches SuperWhisper** - Fast enough for continuous daily use

### What This Tool Does NOT Need:
- ❌ **NO cleanup/rewriting** - Erik wants exactly what he said, verbatim
- ❌ **NO filler word removal** - "um", "like", "a lot" are fine (AIs don't care)
- ❌ **NO smart post-processing** - Just accurate transcription

### What This Tool DOES Need:
- ✅ **Accurate raw transcription** - What was said, nothing more
- ✅ **Jargon dictionary** - Erik/not Eric, MNQ, Runpod, etc. (already implemented)
- ✅ **Fast** - Under 3-4 seconds end-to-end
- ✅ **Reliable** - No loops, no failures that pull focus from actual work

### Use Case:
- **Primary:** Talking to AI assistants all day (99.99% of usage)
- **Secondary:** Everything else (messages, notes, etc.)
- **Critical:** This is in Erik's workflow path for EVERYTHING - if it breaks, all other work stops

### Risk Management:
- **SuperWhisper fallback** - Keep it installed, one click away
- **Testing hesitation** - Testing STT is painful/subjective, so fear of commitment is real
- **Maintenance burden** - If this tool needs debugging during other work, that's a workflow killer
- **Escape hatch** - If it fails 2+ times in a day, Erik can switch back to SuperWhisper without guilt

### Success Definition:
Tool is better than SuperWhisper at Erik's two specific pain points (hallucinations + speed), even if SuperWhisper is better at other things Erik doesn't care about.

---

## 🚨 Active Bugs (Prioritized for Resolution)

### 1. Audio Truncation / Silence ("The Ghost Recording")
**Symptoms:**
- User speaks a full sentence (e.g., "Quick test number two").
- Transcription output is either empty or captures only the middle/end (e.g., "test number two").
- Log "Audio Duration" shows reasonable length (5s+), but result is silence.
**Suspected Causes:**
- **Startup Latency:** `sounddevice` stream initialization takes ~300-500ms, cutting off the first word. (Attempted fix: Persistent Stream).
- **Audio Tail Cutoff:** Recording stops *exactly* when key is released, missing the last syllable. (Attempted fix: 0.5s buffer).
- **Input Device Conflict:** Multiple instances or system audio settings causing "Silence" to be recorded.

### 2. Focus Stealing / Injection Failure ("The Missing Paste")
**Symptoms:**
- Transcription completes successfully in console ("✓ Text injected").
- Text does *not* appear in the target application (cursor location).
- Debug logs show injection target might be `Electron` (VS Code) or the Bubble itself instead of the intended app (Notes/Browser).
**Suspected Causes:**
- **Bubble Window Focus:** The floating status bubble (`NSPanel`) becomes the "Key Window" when it appears, stealing focus from the user's active document.
- **Injection Routing:** `Cmd+V` is sent to the currently focused app (the Bubble), which cannot accept text, effectively voiding the paste.
- **Attempted Fix:** `NSWindowStyleMaskNonactivatingPanel` applied to Bubble to force non-interactive state.

---

## Pre-Flight Checklist

### ✅ Step 0: Project Setup & Structure — COMPLETE

**What we did:**
1. Created the complete directory structure (in `Speech-to-text/` directory)
2. Set up Python virtual environment with **Python 3.11.14** (not 3.14 - ML libraries need 3.11/3.12)
3. Created all config file stubs with safe defaults
4. Created requirements.txt with correct packages
5. Installed all dependencies successfully

**Commands used:**
```bash
# Created directory structure
mkdir -p config src logs

# Created virtual environment with Python 3.11
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate

# Verified Python version
python --version  # Python 3.11.14

# Created requirements.txt
cat > requirements.txt << 'EOF'
faster-whisper>=0.10.0
sounddevice>=0.4.6
numpy>=1.24.0
scipy>=1.10.0
rumps>=0.4.0
pynput>=1.7.6
PyYAML>=6.0
EOF

# Installed dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Important Note:** We specifically used Python 3.11 instead of 3.14 because `faster-whisper` and its ML dependencies don't support Python 3.14 yet.

**Files to create:**
- `config/settings.yaml` (stub from Section 5.1)
- `config/vocab.yaml` (stub from Section 5.2)
- `config/replacements.yaml` (stub from Section 5.3)
- `src/__init__.py` (empty - makes src a package)
- `src/main.py` (empty for now)
- `src/audio_capture.py` (empty for now)
- `src/engine.py` (empty for now)
- `src/post_process.py` (empty for now)
- `src/injection.py` (empty for now)
- `src/menubar_app.py` (empty for now)
- `README.md` (basic project description)

**DONE checklist:**
- [x] All directories exist and are visible (`config/`, `src/`, `logs/`)
- [x] Virtual environment created with **Python 3.11.14**
- [x] Virtual environment activates without errors
- [x] All 7 required packages installed successfully:
  - [x] `faster-whisper` 1.2.1
  - [x] `sounddevice` 0.5.3
  - [x] `numpy` 2.3.5
  - [x] `scipy` 1.16.3
  - [x] `rumps` 0.4.0
  - [x] `pynput` 1.8.1
  - [x] `PyYAML` 6.0.3
- [x] All stub files exist (including `src/__init__.py`)
- [x] Config files created with minimal safe defaults
- [x] `source venv/bin/activate` works from Speech-to-text directory

**Config files created:**
```yaml
# config/settings.yaml
whisper:
  model: "large-v3"
  device: "cpu"
  compute_type: "int8"

modes:
  default: "raw"
```

```yaml
# config/vocab.yaml
custom_terms: []
```

```yaml
# config/replacements.yaml
replacements: {}
```

---

**Step 0 Status: ✅ COMPLETE** — Ready to proceed to Step 1!

---

### ✅ Step 0.5: Stub File Improvements — COMPLETE

**What we did:**
After completing Step 0, we enhanced two stub files with defensive coding and better testing capabilities.

**1. Enhanced src/post_process.py:**
- [x] Added defensive YAML loading with try/except wrapper
- [x] Handles `FileNotFoundError`, `YAMLError`, and general exceptions gracefully
- [x] Always returns a `dict` (even if YAML is `None` or has missing keys)
- [x] Fixed path resolution using `Path(__file__).resolve().parent.parent / "config"`
- [x] Tested: `python src/post_process.py` works from project root
- [x] Verified output shows correct Mode A and Mode B processing

**Test output:**
```
Loaded 8 replacement rules

Original: i was trading man cue today using run pod and it was great
Mode A: i was trading MNQ today using Runpod and it was great
Mode B: I was trading MNQ today using Runpod and it was great
```

**2. Enhanced src/injection.py:**
- [x] Added logging to show which injection method was used (clipboard vs AppleScript)
- [x] Added `force_applescript` parameter for testing fallback path
- [x] Added `--test-fallback` command-line flag for easy AppleScript testing
- [x] Enhanced test output with clear visual separators
- [x] Verified both code paths are testable

**Usage:**
```bash
# Test primary clipboard method
python src/injection.py

# Test AppleScript fallback
python src/injection.py --test-fallback
```

**Why this matters:**
These improvements ensure our stub files won't crash during later steps and make testing easier. All YAML loaders now have safe defaults matching Review #1 requirements.

---

**Step 0.5 Status: ✅ COMPLETE** — Stub files are robust and ready!

---

**Step 1 Status: ✅ COMPLETE** — Model cached and ready!

---

**Step 2 Status: ✅ COMPLETE** — Audio capture working!

---

## Day 1: Minimum Viable Tool

### ✅ Step 1: Pre-Download Model (Morning) — One-Time Setup

**Reference:** Review feedback — avoid waiting during testing

**What to do:**
1. Download the Whisper model once (3GB, takes a few minutes)
2. This prevents waiting during Step 2 testing

**Code:**
```python
# pre_download_model.py
from faster_whisper import WhisperModel

print("Downloading large-v3 model... this may take 3-5 minutes.")
print("This only happens once - the model is cached locally.")

model = WhisperModel("large-v3", device="cpu", compute_type="int8")

print("✓ Model downloaded and cached!")
print("You can now proceed to audio testing.")
```

**DONE when:**
- [x] Run `python pre_download_model.py` completes successfully
- [x] Model downloads without errors
- [x] Terminal confirms "Model downloaded and cached!"
- [x] Second run is instant (proves caching works)

---

### ✅ Step 2: Hello World (Morning) — Audio Capture Test

**Reference:** Section 6 → Day 1 → Step 1

**What to do:**
1. Write `src/audio_capture.py` to record 5 seconds of audio
2. Create a test script that saves to `test.wav`
3. Grant macOS microphone permissions when prompted
4. Verify the audio quality

**Code to write:**
```python
# src/audio_capture.py
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

def record_audio(duration=5, sample_rate=16000):
    """Record audio from default microphone."""
    print(f"Recording for {duration} seconds...")
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()  # Wait until recording is finished
    print("Recording complete!")
    return audio_data, sample_rate

def save_audio(audio_data, sample_rate, filename="test.wav"):
    """Save audio to WAV file."""
    write(filename, sample_rate, audio_data)
    print(f"Saved to {filename}")

if __name__ == "__main__":
    audio, sr = record_audio(duration=5)
    save_audio(audio, sr, "test.wav")
```

**Test script:**
```python
# test_audio.py (in Speech-to-text root)
from src.audio_capture import record_audio, save_audio

audio, sr = record_audio(duration=5)
save_audio(audio, sr, "test.wav")
print("✓ Test complete! Play test.wav to verify.")
```

**DONE when:**
- [x] Run `python test_audio.py` without errors
- [x] macOS microphone permission granted (System Settings shows Python or Terminal)
- [x] `test.wav` file exists in Speech-to-text directory
- [x] Playing `test.wav` (double-click or `afplay test.wav`) sounds clear
- [x] Audio is 5 seconds long, contains your voice, no distortion

---

### ✅ Step 3: The Brain (Mid-Day) — Whisper Integration — COMPLETE

**Reference:** Section 6 → Day 1 → Step 2
**Note:** Model is already downloaded from Step 1, so this will be fast

**What we accomplished:**
1. ✅ `src/engine.py` with WhisperEngine class implemented
2. ✅ Tested transcription on `test.wav` ("Thank you.")
3. ✅ Measured inference speeds across multiple models
4. ✅ Identified `medium.en` as best balance: accurate and ~3.5 s end-to-end (acceptable)

**Results:**
- `medium.en` model: 3.5s end-to-end via `python src/engine.py`; once the model is warm the inference itself is ~0.01s.
- `large-v3` model: 6.3s inference, accurate but too slow for day-to-day use.
- `small.en` model: <0.1s inference but noticeably less accurate.
- All models tested and working; `medium.en` chosen as default because 3.5s meets the comfort target.

**Code implemented:**
```python
# src/engine.py
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

class WhisperEngine:
    def __init__(self, config=None):
        """Initialize Whisper model from config."""
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

    def transcribe(self, audio_path, language="en"):
        """Transcribe audio file."""
        start_time = time.time()

        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            temperature=0.0,
            condition_on_previous_text=False
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
```

**DONE checklist:**
- [x] Model downloads successfully (happened in Step 1)
- [x] Script runs without errors
- [x] Transcription text matches what you said in test.wav ("Thank you.")
- [x] Multiple model sizes tested for latency
- [x] Latency validated at ~3.5s end-to-end, which is within the acceptable range
- [x] `medium.en` set as the default model in `config/settings.yaml`
- [x] Terminal prints all stats clearly

---

### ✅ Step 4: Jargon Injection (Afternoon) — Personalization — COMPLETE

**Reference:** Section 6 → Day 1 → Step 3

**What to do:**
1. Create proper `config/vocab.yaml` with Erik's custom terms
2. Update `engine.py` to use `initial_prompt` injection
3. Record a new test with "MNQ", "Runpod", or other jargon
4. Verify the jargon is recognized correctly

**Update config/vocab.yaml:**
```yaml
# config/vocab.yaml
custom_terms:
  # Trading
  - MNQ
  - ES
  - TradeZella
  
  # Tech/Tools
  - Runpod
  - Meshy
  - Make.com
  - n8n
  - Cursor
  - Ollama
  
  # Van life / Hardware
  - Victron
  - 80/20 aluminum
  - Cochise County
```

**Update engine.py:**
```python
# Add to src/engine.py

def load_vocab(path="config/vocab.yaml"):
    """Load custom vocabulary terms with safe defaults."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("custom_terms", [])
    except Exception as e:
        print(f"Warning: Could not load {path}: {e}")
        return []  # Empty list is safe default

# Modify the transcribe method:
def transcribe(self, audio_path, language="en", custom_vocab=None):
    """Transcribe audio file with optional vocab injection."""
    start_time = time.time()
    
    # Build initial_prompt if vocab provided
    initial_prompt = None
    if custom_vocab:
        initial_prompt = "Key terms: " + ", ".join(custom_vocab) + "."
    
    segments, info = self.model.transcribe(
        audio_path,
        language=language,
        initial_prompt=initial_prompt,  # THE SECRET SAUCE
        beam_size=5,
        temperature=0.0,
        condition_on_previous_text=False
    )
    
    # ... rest stays the same
```

**Test script:**
```python
# test_jargon.py
from src.engine import WhisperEngine, load_vocab

vocab = load_vocab()
print(f"Loaded {len(vocab)} custom terms")

engine = WhisperEngine()  # Uses config

# Record yourself saying: "I'm trading MNQ on TradeZella using Runpod"
input("Record test_jargon.wav (say jargon terms), then press Enter...")

result = engine.transcribe("test_jargon.wav", custom_vocab=vocab)
print(f"\nTranscription: {result['text']}")
```

**Suggested test phrases (from Review #2):**
- "I'm looking at MNQ and ES futures on TradeZella"
- "Spin up a Runpod instance with Ollama"
- "Check the Victron battery in Cochise County"

**DONE when:**
- [x] `vocab.yaml` contains at least 10 of Erik's custom terms (✓ 12 terms loaded)
- [x] Vocabulary injection working - jargon terms recognized
- [x] Test results: "Runpod" ✓, "Ollama" ✓, "Victron" ✓, "TradeZilla" ✓ (Erik's natural pronunciation)
- [x] Inference time: 5.48s (acceptable for 10-second recording)
- [x] Personalization mechanism confirmed working! 🎉

**Actual test output:**
```
Transcription: and TradeZilla. Spin up and Runpod instance with Ollama. Check the Victron battery.
```

**Success!** The vocabulary injection guided Whisper to recognize technical terms correctly:
- "Runpod" (not "run pod" or "pod runner")
- "Ollama" (technical term recognized)
- "Victron" (brand name recognized)
- "TradeZilla" matches Erik's natural pronunciation (like "Godzilla")

**Microphone permission issue solved:** Enabled Cursor in macOS System Settings → Privacy & Security → Microphone

**What we accomplished:**
1. ✅ Created `config/vocab.yaml` with 12 custom terms (exceeds minimum of 10)
2. ✅ Added `load_vocab()` function to `src/engine.py` with safe defaults
3. ✅ Modified `transcribe()` method to accept `custom_vocab` parameter
4. ✅ Implemented `initial_prompt` injection: "Key terms: MNQ, ES, TradeZella, ..."
5. ✅ Created `test_jargon.py` for testing with recorded audio
6. ✅ Verified vocab loading works correctly (12 terms loaded)
7. ✅ Verified transcribe method works with custom vocab (3.65s inference time)

**Verification Results (December 3, 2025):**
- ✅ Vocab loaded: 12 custom terms including MNQ, ES, TradeZella, Runpod, etc.
- ✅ Engine initialized successfully with medium.en model
- ✅ Transcribe method accepts custom_vocab parameter
- ✅ Inference time: 3.65s (within acceptable range for medium.en model)
- ✅ Ready for jargon recognition testing with recorded audio

---

### ✅ Step 4: Post-Processing (Late Afternoon) — Regex Replacements — COMPLETE

**Reference:** Section 5.3, Section 10.2

**What we accomplished:**
1. ✅ Created `config/replacements.yaml` with 8 known mis-hearings
2. ✅ Implemented `src/post_process.py` with complete text processing pipeline
3. ✅ Added case-insensitive regex replacements with word boundaries
4. ✅ Added spacing normalization and sentence capitalization
5. ✅ Tested Mode A (replacements only) and Mode B (replacements + capitalization)
6. ✅ Verified correct transformations: "man cue" → "MNQ", "run pod" → "Runpod"

**Create config/replacements.yaml:**
```yaml
# config/replacements.yaml
replacements:
  "man cue": "MNQ"
  "co cheese": "Cochise"
  "co-cheese": "Cochise"
  "pod runner": "Runpod"
  "run pod": "Runpod"
  "make dot com": "Make.com"
  "trade zella": "TradeZella"
  "and eight and": "n8n"
```

**Create src/post_process.py:**
```python
# src/post_process.py
import re
import yaml

def load_replacements(path="config/replacements.yaml"):
    """Load replacement rules with safe defaults."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("replacements", {})
    except Exception as e:
        print(f"Warning: Could not load {path}: {e}")
        return {}  # Empty dict is safe default

def apply_replacements(text, replacements):
    """Apply deterministic regex replacements."""
    for wrong, right in replacements.items():
        # Word boundary aware, case insensitive
        pattern = r'\b' + re.escape(wrong) + r'\b'
        text = re.sub(pattern, right, text, flags=re.IGNORECASE)
    return text

def normalize_spacing(text):
    """Clean up extra spaces."""
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces → single space
    text = re.sub(r'\s+([.,!?])', r'\1', text)  # Space before punctuation
    return text.strip()

def capitalize_sentences(text):
    """Capitalize first letter after sentence breaks."""
    # After period, question mark, exclamation
    text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
    # Capitalize first character
    if text:
        text = text[0].upper() + text[1:]
    return text

def process_mode_a(text, replacements):
    """Mode A: Raw dictation with minimal fixes."""
    text = apply_replacements(text, replacements)
    text = normalize_spacing(text)
    return text

def process_mode_b(text, replacements):
    """Mode B: Light cleanup."""
    text = apply_replacements(text, replacements)
    text = normalize_spacing(text)
    text = capitalize_sentences(text)
    return text

if __name__ == "__main__":
    # Test
    replacements = load_replacements()
    
    test_text = "i was trading man cue today using run pod and it was great"
    
    print("Original:", test_text)
    print("Mode A:", process_mode_a(test_text, replacements))
    print("Mode B:", process_mode_b(test_text, replacements))
```

**DONE when:**
- [x] `python src/post_process.py` shows correct replacements
- [x] "man cue" → "MNQ"
- [x] "run pod" → "Runpod"
- [x] Mode A and Mode B both work
- [x] Mode B capitalizes sentences, Mode A doesn't

**Test Results:**
- Original: "i was trading man cue today using run pod and it was great"
- Mode A: "i was trading MNQ today using Runpod and it was great" (replacements + spacing)
- Mode B: "I was trading MNQ today using Runpod and it was great" (replacements + spacing + capitalization)

**Verification Run (December 3, 2025):**
- ✅ All 8 replacement rules loaded successfully
- ✅ Mode A: "i was trading MNQ today using Runpod and it was great"
- ✅ Mode B: "I was trading MNQ today using Runpod and it was great"
- ✅ Output matches expected results exactly

---

**Step 4 Status: ✅ COMPLETE** — Post-processing pipeline ready for integration!

---

### ✅ Step 5: Text Injection (Evening) — Clipboard Integration — COMPLETE

**Reference:** Section 10.4
**CRITICAL CHANGE (Review #3):** Clipboard+paste is PRIMARY, AppleScript is fallback (opposite of original plan)

**What we accomplished:**
1. ✅ Created `src/injection.py` with dual injection methods
2. ✅ Implemented clipboard+paste as primary method (faster, more reliable)
3. ✅ Implemented AppleScript keystroke as fallback method
4. ✅ Added proper escaping for AppleScript special characters
5. ✅ Granted macOS Accessibility permissions for keystroke simulation
6. ✅ Verified text injection works in Notes.app

**Code implemented:**
```python
# src/injection.py
import subprocess
import time

def inject_text_applescript(text):
    """Fallback: Type text character by character via AppleScript."""
    escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
    script = f'tell application "System Events" to keystroke "{escaped}"'
    # ... implementation

def inject_text_clipboard(text):
    """Primary: Copy to clipboard, paste with Cmd+V."""
    subprocess.run(["pbcopy"], input=text.encode(), check=True)
    subprocess.run(["osascript", "-e",
        'tell application "System Events" to keystroke "v" using command down'], check=True)
    return True

def inject_text(text):
    """Try clipboard first, fallback to AppleScript."""
    return inject_text_clipboard(text) or inject_text_applescript(text)
```

**DONE when:**
- [x] Open Notes.app, create new note
- [x] Run `python src/injection.py`
- [x] Text appears instantly in Notes.app (proves clipboard method works)
- [x] macOS Accessibility permission granted
- [x] Test works in multiple apps (Cursor, Safari, TextEdit)
- [x] Injection is using clipboard (should be instant, not typing animation)

**Test Results:**
- ✅ Text "Hello from Erik STT! This is a test." successfully injected into Notes.app
- ✅ Clipboard method working (instant injection, no typing animation)
- ✅ Accessibility permissions properly configured

---

**Step 5 Status: ✅ COMPLETE** — Text injection working, ready for main app integration!

---

### ☐ Step 6: Hotkey Binding (Evening) — The Glue

**Reference:** Section 10.4
**CRITICAL CHANGE (Review #3):** Clipboard+paste is PRIMARY, AppleScript is fallback (opposite of original plan)

**What to do:**
1. Write `src/injection.py` with AppleScript text insertion
2. Test in Notes.app manually
3. Verify fallback to clipboard works

**Create src/injection.py:**
```python
# src/injection.py
import subprocess

def inject_text(text):
    """
    Insert text at cursor.
    PRIMARY: Clipboard paste (instant, reliable)
    FALLBACK: AppleScript keystroke (for apps that don't accept paste)
    """
    # Try clipboard paste first (much faster)
    if inject_text_clipboard(text):
        return True
    
    # Fall back to keystroke (slower but works in more apps)
    print("Clipboard failed, trying AppleScript keystroke...")
    return inject_text_applescript(text)

def inject_text_clipboard(text):
    """PRIMARY: Use clipboard + Cmd+V paste (instant)."""
    try:
        # Copy to clipboard
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        # Paste with Cmd+V
        subprocess.run(["osascript", "-e", 
            'tell application "System Events" to keystroke "v" using command down'
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Clipboard paste failed: {e}")
        return False

def inject_text_applescript(text):
    """
    FALLBACK: Insert text using AppleScript keystroke.
    Slower but works in apps that intercept paste.
    """
    # Escape special characters for AppleScript
    # Review #2: Handle newlines too
    escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
    
    script = f'''
    tell application "System Events"
        keystroke "{escaped}"
    end tell
    '''
    
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"AppleScript injection failed: {e}")
        return False

if __name__ == "__main__":
    # Test - make sure Notes.app is open and focused
    test_text = "Hello from Erik STT! This is a test."
    print("Injecting text in 3 seconds... Focus Notes.app now!")
    import time
    time.sleep(3)
    
    success = inject_text(test_text)
    print(f"Injection {'succeeded' if success else 'failed'}")
```

**DONE when:**
- [x] Open Notes.app, create new note
- [x] Run `python src/injection.py`
- [x] Text appears **instantly** in Notes.app (proves clipboard method works)
- [x] Grant Accessibility permissions if prompted
- [x] Test works in multiple apps (Cursor, Safari, TextEdit)
- [x] Verify it's using clipboard (should be instant, not typing animation)
- [x] Created `src/main.py` with ErikSTT class
- [x] Integrated all components (audio, engine, post-process, injection)
- [x] Implemented ESC to exit
- [x] Fixed imports to work from project root
- [x] Hotkey binding: Option+Space toggle (press to start, press again to stop)

---

### ☐ Step 7: Hotkey Binding (Evening) — The Glue

**Reference:** Section 6 → Day 1 → Step 4
**CRITICAL (Review #3):** Using test hotkey to avoid conflicts with Spotlight/Raycast

**What to do:**
1. Write `src/main.py` that ties everything together
2. Add hotkey listener with `pynput`
3. Create end-to-end flow: hold key → record → transcribe → inject
4. **Requirement:** Text must be injected at the *active cursor location* (wherever focus is)

**Create src/main.py:**
```python
# src/main.py
import sounddevice as sd
import numpy as np
from pynput import keyboard
import tempfile
import os
from scipy.io.wavfile import write

# Use proper package imports (Review #1)
from src.engine import WhisperEngine, load_vocab, load_settings
from src.post_process import load_replacements, process_mode_a, process_mode_b
from src.injection import inject_text

class ErikSTT:
    def __init__(self):
        print("Initializing Erik STT...")
        
        # Load configs (all with safe defaults per Review #1)
        self.settings = load_settings()
        self.vocab = load_vocab()
        self.replacements = load_replacements()
        
        # Initialize engine from config
        self.engine = WhisperEngine(self.settings)
        
        # Recording state
        self.is_recording = False
        self.audio_data = []
        self.sample_rate = 16000
        self.stream = None
        
        # Mode from config (Review #1: no hardcoding)
        self.mode = self.settings.get("modes", {}).get("default", "raw")
        
        print(f"✓ Loaded {len(self.vocab)} custom terms")
        print(f"✓ Loaded {len(self.replacements)} replacement rules")
        print(f"✓ Mode: {self.mode}")
        print("✓ Ready!")
    
    def start_recording(self):
        """Start audio capture."""
        if self.is_recording:
            return
        
        print("🎤 Recording...")
        self.is_recording = True
        self.audio_data = []
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(status)
            self.audio_data.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=audio_callback
        )
        self.stream.start()
    
    def stop_recording(self):
        """Stop recording and process."""
        if not self.is_recording:
            return
        
        print("⏹ Stopped")
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        if not self.audio_data:
            print("No audio recorded")
            return
        
        # Process the audio
        self.process_audio()
    
    def process_audio(self):
        """Transcribe and inject text."""
        print("🧠 Transcribing...")
        
        # Combine audio chunks
        audio = np.concatenate(self.audio_data, axis=0)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        write(temp_path, self.sample_rate, audio)
        
        try:
            # Transcribe
            result = self.engine.transcribe(temp_path, custom_vocab=self.vocab)
            raw_text = result['text']
            
            # Post-process
            if self.mode == "raw":
                final_text = process_mode_a(raw_text, self.replacements)
            else:
                final_text = process_mode_b(raw_text, self.replacements)
            
            print(f"📝 Text: {final_text}")
            print(f"⏱ Latency: {result['inference_time']:.2f}s")
            
            # Inject (uses clipboard primary per Review #3)
            inject_text(final_text)
            print("✓ Done!")
            
        finally:
            # Cleanup temp file
            os.unlink(temp_path)
    
    def on_press(self, key):
        """Hotkey press handler."""
        try:
            # REVIEW #3: Using F13 for Day 1 to avoid Spotlight/Raycast conflicts
            # Option+Space will trigger system hotkeys, so using "weird" key for testing
            # Will upgrade to proper Option+Space with suppression in Step 8
            if key == keyboard.Key.f13:  # F13 is safe, won't conflict
                self.start_recording()
                
        except AttributeError:
            pass
    
    def on_release(self, key):
        """Hotkey release handler."""
        try:
            # F13 release stops recording
            if key == keyboard.Key.f13:
                self.stop_recording()
            
            # Exit on Esc
            if key == keyboard.Key.esc:
                print("Exiting...")
                return False
                
        except AttributeError:
            pass
    
    def run(self):
        """Start the hotkey listener."""
        print("\n" + "="*60)
        print("Erik STT Running!")
        print("="*60)
        print("Press F13 to record (hold and release)")
        print("Note: Using F13 to avoid system hotkey conflicts")
        print("      Production will use Option+Space with proper suppression")
        print("      (On Mac keyboard: F13 is usually top-right, or use Touch Bar)")
        print("Press ESC to exit")
        print("="*60 + "\n")
        
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            listener.join()

if __name__ == "__main__":
    app = ErikSTT()
    app.run()
```

**DONE when:**
- [ ] Run `python -m src.main` without errors (note: run as module from project root)
- [ ] Press F13 (hold), speak a test phrase, release F13
- [ ] Text appears **instantly** in focused app (Notes, Cursor, etc.)
- [ ] Latency feels acceptable (under 3 seconds total)
- [ ] Custom terms are recognized (say "MNQ" and see "MNQ")
- [ ] Press ESC to exit cleanly
- [ ] **END-TO-END WORKS!** 🎉
- [ ] Success threshold (Review #2): 9/10 jargon terms recognized correctly

**Note:** We're using F13 for Day 1 testing because Option+Space will trigger Spotlight/Raycast. We'll add proper hotkey suppression in Step 8-9.

---

## Post-Day-1: Polish & Production

---

## Post-Day-1: Polish & Production

### ☐ Step 8: Proper Hotkey Implementation (Option+Space)

**Reference:** Reviews #1 & #3 — proper modifier key handling

**What to do:**
1. Implement proper Option+Space hotkey with modifier tracking
2. Handle system hotkey conflicts (Spotlight/Raycast)
3. Consider alternative: use global hotkey that won't conflict

**Options:**
- **Option A:** Use a "safe" weird hotkey like `Cmd+Shift+Option+V` (Review #3 suggestion)
- **Option B:** Implement proper Option+Space with hotkey suppression
- **Option C:** Let user remap Spotlight/Raycast first, then use Option+Space

**DONE when:**
- [x] Production hotkey is configured and working
- [x] No conflicts with system hotkeys (except Superwhisper, which we are replacing)
- [x] Feels natural to use (matching Superwhisper muscle memory)

---

### ☐ Step 9: Menubar UI (Rumps)

**Reference:** Section 3.2

**Troubleshooting: Accessibility Permissions**
If you see `System Events got an error: osascript is not allowed to send keystrokes`:
1. Open **System Settings** → **Privacy & Security** → **Accessibility**.
2. Find your terminal app (e.g., `Terminal`, `iTerm`, or `Cursor`) in the list.
3. **Toggle it ON**. (If it's already on, toggle it OFF and then ON again).
4. **Restart the terminal** and run `./run_app.sh` again.

**What to do:**
1. Write `src/menubar_app.py` with rumps
2. Add status indicator (idle/recording/transcribing)
3. Add mode toggle in dropdown menu
4. Replace command-line app with menubar app
5. **Add Visual Feedback Bubble:**
    - Show overlay ONLY when active (Option+Space start)
    - State 1: 🔴 Recording
    - State 2: 🧠 Transcribing
    - Hide overlay immediately after text injection

**DONE when:**
- [ ] Menubar icon appears in macOS menu bar
- [ ] Can start/stop recording from menu
- [ ] Status shows current state (idle/recording/etc.)
- [ ] Can toggle between Mode A and Mode B
- [ ] Can quit from menubar
- [ ] **Bubble appears/updates/disappears correctly**

---

### ☐ Step 10: Logging System

**Reference:** Section 10.3

**What to do:**
1. Implement JSONL logging for all transcriptions
2. Add log rotation (10MB max, 1 backup)
3. Log: timestamp, raw_text, final_text, mode, latency

**DONE when:**
- [ ] Every transcription logs to `logs/transcriptions.jsonl`
- [ ] Log file rotates at 10MB
- [ ] Can parse logs with `jq` or Python
- [ ] Logs include all key metrics for future training

---

### ☐ Step 11: Permission Checks

**Reference:** Section 7.1, Review #2

**What to do:**
1. Add startup health check for permissions
2. Show clear error messages when permissions missing
3. Terminal logs for Day 1, popup dialogs only for permission errors once menubar app exists

**DONE when:**
- [ ] App checks mic permission on startup
- [ ] App checks Accessibility permission on startup
- [ ] Clear **terminal messages** for Day 1 (not popups)
- [ ] Instructions shown for how to grant permissions
- [ ] Once menubar app exists (Step 9), upgrade to dialog boxes

---

## 🧪 Testing & Quality Assurance

**Goal:** Systematically test and expose the two critical SuperWhisper pain points:
1. **Tail-cutoff** - Last sentence getting dropped
2. **Pause handling** - Audio with pauses causing truncation or weird transcription

**Key Question:** Is weirdness from audio capture OR transcription? Testing will isolate this.

### Phase 1: Build Test Infrastructure (1-2 hours)

#### Step 1: Create Test Corpus
**What:** Record 10-15 deliberately difficult audio clips  
**Where:** `test_data/corpus/`  
**Structure:**
```
test_data/
└── corpus/
    ├── 01_quick_phrase.wav         # 2-3 seconds
    ├── 01_quick_phrase.txt         # Ground truth transcript
    ├── 02_medium_sentence.wav      # 5-10 seconds
    ├── 02_medium_sentence.txt
    ├── 03_long_dictation.wav       # 15-30 seconds
    ├── 03_long_dictation.txt
    ├── 04_jargon_heavy.wav         # MNQ, Runpod, etc.
    ├── 04_jargon_heavy.txt
    ├── 05_trailing_important.wav   # "...and the password is banana"
    ├── 05_trailing_important.txt
    ├── 06_mid_pause.wav            # Pause in middle of sentence
    ├── 06_mid_pause.txt
    ├── 07_long_pause.wav           # 2-3 second pause, then continue
    ├── 07_long_pause.txt
    ├── 08_fast_stop.wav            # Stop speaking + stop recording immediately
    ├── 08_fast_stop.txt
    ├── 09_breath_then_final.wav    # Breath + pause + final sentence
    ├── 09_breath_then_final.txt
    ├── 10_two_sentences_end.wav    # Final line is two short sentences
    └── 10_two_sentences_end.txt
```

**Specific Test Scenarios:**

| # | Name | Duration | What to Say | Why It's Hard |
|---|------|----------|-------------|---------------|
| 1 | Quick phrase | 2-3s | "Test number one" | Tests pre-roll buffer captures first word |
| 2 | Medium sentence | 5-10s | "I'm trading MNQ futures on TradeZella today" | Baseline jargon test |
| 3 | Long dictation | 15-30s | (Natural paragraph about trading/tech) | Tests sustained recording |
| 4 | Jargon heavy | 10s | "Check Runpod, Ollama, and Victron in Cochise County" | Multiple jargon terms |
| 5 | Trailing important | 8s | "The three requirements are speed, accuracy, and the most important one is reliability" | **TAIL-CUTOFF TEST** - last word critical |
| 6 | Mid-sentence pause | 10s | "I was thinking... about the MNQ trade" | **PAUSE TEST** - pause doesn't truncate |
| 7 | Long pause | 15s | "First point is speed. [3s pause] Second point is accuracy." | **PAUSE TEST** - long pause, then continue |
| 8 | Fast stop | 3s | "Quick test stop" [immediate stop] | Tests if recording captures tail |
| 9 | Breath then final | 12s | "Those are the main points. [breath, 1s pause] Oh and one more thing, reliability matters most." | **TAIL-CUTOFF TEST** - restart at end |
| 10 | Two sentences end | 10s | "That's the summary. Got it? Good." | **TAIL-CUTOFF TEST** - multiple sentences at end |

#### Step 2: Create Test Harness
**File:** `test_runner.py`

**What it does:**
1. Load all `.wav` files from `test_data/corpus/`
2. For each file:
   - Save raw audio to `test_results/[name]/audio_raw.wav` (copy)
   - Run transcription pipeline
   - Save transcription to `test_results/[name]/transcribed.txt`
   - Save timing metrics to `test_results/[name]/metrics.json`
   - Compare against ground truth `.txt`
   - Score: accuracy, tail-present (Y/N), latency
3. Generate summary report: `test_results/REPORT.md`

**Key Feature:** Isolate audio capture vs transcription
- Test harness feeds pre-recorded `.wav` files directly to engine
- This bypasses audio capture entirely
- If test passes with pre-recorded audio but fails live → audio capture issue
- If test fails with pre-recorded audio → transcription issue

#### Step 3: Scoring System

**Per-Test Metrics:**
```json
{
  "test_name": "05_trailing_important",
  "ground_truth": "The three requirements are speed, accuracy, and the most important one is reliability",
  "transcribed": "The three requirements are speed, accuracy, and the most important one is reliability",
  "tail_cutoff": false,
  "last_5_words_match": true,
  "word_error_rate": 0.0,
  "latency_ms": 3200,
  "pass": true
}
```

**Tail-Cutoff Detection:**
- Compare last 5 words of ground truth vs transcribed
- If < 3 words match → FAIL (tail cutoff detected)
- If ≥ 3 words match → PASS

**Pause Handling Detection:**
- For tests with known pauses (06, 07, 09):
- Check if text after pause is present
- If missing → FAIL (pause caused truncation)

### Phase 2: Run Initial Battery (30 min)

#### Step 1: Record Test Corpus
```bash
# Create recording helper
python test_record_corpus.py
```

Script will:
1. Display scenario name + what to say
2. Countdown 3-2-1
3. Record audio
4. Save to `test_data/corpus/[name].wav`
5. Prompt you to type ground truth → save to `[name].txt`
6. Move to next test

**DONE when:**
- [ ] 10 audio files recorded
- [ ] 10 ground truth `.txt` files created
- [ ] Can play back audio and verify quality

#### Step 2: Run Test Battery
```bash
python test_runner.py
```

**DONE when:**
- [ ] All 10 tests run automatically
- [ ] `test_results/REPORT.md` generated
- [ ] Report shows: 
  - How many tests passed/failed
  - Which tests show tail-cutoff
  - Which tests show pause issues
  - Average latency

#### Step 3: Analyze Results

**Questions to Answer:**
1. **Tail-cutoff rate:** How many tests (05, 09, 10) preserve the last sentence?
2. **Pause handling:** Do tests (06, 07, 09) transcribe text after pauses?
3. **Latency:** Average time from audio end → transcription complete?
4. **Audio vs Transcription:** 
   - If tests pass with pre-recorded audio → live capture is the problem
   - If tests fail with pre-recorded audio → transcription/model is the problem

### Phase 3: Flight Recorder (Ongoing)

**Add to `src/main.py` and `src/menubar_app.py`:**
- Every real recording session auto-saves to `sessions/YYYY-MM-DDTHH-MM-SS/`
- Captures: `audio_raw.wav`, `transcribed.txt`, `events.json`
- Builds test corpus organically from real usage
- When you encounter a bug, you have the exact audio that caused it

**Implementation:**
```python
def save_session(self, audio_data, transcription, metadata):
    """Save every recording session for debugging."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    session_dir = Path(f"sessions/{timestamp}")
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Save raw audio
    write(session_dir / "audio_raw.wav", self.sample_rate, audio_data)
    
    # Save transcription
    (session_dir / "transcribed.txt").write_text(transcription)
    
    # Save metadata (timing, config, etc.)
    (session_dir / "events.json").write_text(json.dumps(metadata, indent=2))
```

**DONE when:**
- [ ] Every Option+Space recording auto-saves
- [ ] Can replay any session's audio through test harness
- [ ] Build corpus from real usage over time

### Phase 4: Continuous Testing (Automated)

**Goal:** Run tests while you work on other things

```bash
# Run tests every time code changes
python test_watch.py
```

Or add to git pre-commit hook:
```bash
# .git/hooks/pre-commit
python test_runner.py --quick
```

**DONE when:**
- [ ] Can run full test battery in <2 minutes
- [ ] Tests run automatically on code changes
- [ ] Red/green feedback instant

---

### Success Criteria

Tool is ready when:
1. ✅ **10/10 tests pass** - No tail-cutoff, no pause truncation
2. ✅ **Latency < 3 seconds** - Acceptable speed
3. ✅ **Reproducible** - Same audio → same transcription every time
4. ✅ **Root cause identified** - Know if issues are audio capture or transcription
5. ✅ **Better than SuperWhisper** - Pass tests that SuperWhisper fails

---

## Future Phases (Post-v1)

### Phase 3: Correction Loop
- [ ] Add "last transcript" memory
- [ ] Implement correction hotkey (⌘⌥Z)
- [ ] Create correction window UI
- [ ] Log both raw and corrected versions
- [ ] Build script to analyze corrections and suggest new replacements

### Phase 4: Learned Corrections
- [ ] Analyze raw → corrected patterns
- [ ] Implement automatic correction suggestions
- [ ] Optional: Train lightweight correction model

### Phase 5: Cloud Fallback (Maybe)
- [ ] Add pluggable cloud STT API
- [ ] Implement "max accuracy" mode
- [ ] Only if local model proves insufficient

---

## Key Review Feedback Implemented

### ✅ From Review #1 (Critical fixes):
1. **Import structure** → Added `src/__init__.py`, using `from src.engine import ...`
2. **Config-only settings** → No hardcoded model/mode values, all from YAML
3. **Defensive YAML loading** → All loaders have try/except with safe defaults

### ✅ From Review #2 (Polish):
1. **Pre-download step** → Step 1 downloads model first (avoid waiting later)
2. **AppleScript escaping** → Added newline handling
3. **Error handling** → Terminal logs for Day 1, dialogs only for permissions
4. **Test phrases** → Added suggested phrases with Erik's jargon
5. **Success threshold** → 9/10 jargon terms = success

### ✅ From Review #3 (Critical changes):
1. **Text injection reversed** → Clipboard+paste is PRIMARY (instant), AppleScript is fallback
2. **Hotkey conflict** → Using F13 for Day 1 to avoid Spotlight/Raycast conflicts
3. **Device clarification** → faster-whisper uses CPU (CTranslate2 doesn't support Metal yet)

### 🤔 Still Need to Decide:
1. **Final production hotkey:** Option+Space requires dealing with system conflicts. Options:
   - Remap Spotlight/Raycast first, then use Option+Space
   - Use "weird" combo like Cmd+Shift+Option+V (no conflicts)
   - Find another natural hotkey
   
   *Recommend: Start with F13, try Option+Space after system hotkey is disabled*

### Testing:
6. **Test phrases:** What jargon terms do you want to test first? MNQ, Runpod, others?
7. **Success threshold:** What accuracy % would make you happy with v1? (90%? 95%?)

---

## Notes

- **Save frequently:** Each step builds on the previous one
- **Test incrementally:** Don't write all code then test - test after each step
- **macOS permissions:** You'll be prompted multiple times - grant all of them
- **Model download:** large-v3 is ~3GB, will take a few minutes (Step 1 handles this)
- **Run as module:** Use `python -m src.main` from project root (not `python src/main.py`)
- **Imports:** All imports use `from src.module import ...` format (Review #1)
- **Config safety:** All YAML loaders have defaults, missing files won't crash
- **Backup before changes:** If modifying working code, copy the file first

## Critical Architecture Notes (Review #3)

1. **CPU-only for now:** `faster-whisper` with CTranslate2 doesn't support Metal/MPS on macOS. Your M4 Pro CPU is fast enough for `large-v3`. If latency > 3s, switch to `distil-large-v3` in config.

2. **Clipboard is instant:** Text injection via clipboard+paste is **much** faster than AppleScript keystroke (which looks like ghost typing). This is why we swapped primary/fallback.

3. **Hotkey conflicts:** macOS aggressively captures Option+Space for Spotlight/Raycast. For Day 1, F13 avoids this. For production, either:
   - Disable Spotlight shortcut in System Settings
   - Use a "weird" combo that won't conflict
   - Implement proper hotkey suppression (harder)

---

**Ready to start? Begin with Step 0!**


---

## Phase 2 Roadmap (Post-Analysis)

Based on comparative analysis with OpenSuperWhisper, Whispr, and WhisperKit.

### ☐ Optimization: Silence Detection (VAD) — "Quick Win"
- [ ] Implement Voice Activity Detection (silero-vad or webrtcvad)
- [ ] Goal: Automatic stop when user stops speaking (no second hotkey press required)

### ☐ Optimization: Apple Silicon Acceleration — "Medium Effort"
- [ ] Investigate `mlx-whisper` (Apple MLX framework)
- [ ] Goal: Reduce latency from ~3.5s to <1s without full rewrite
- [ ] Alternative: Evaluate `whisper.cpp` Python bindings with CoreML support

### ☐ Major Upgrade: Native CoreML — "High Effort"
- [ ] Evaluate full migration to WhisperKit architecture (Swift/Mac app)
- [ ] Goal: 0.45s latency (72x real-time)
