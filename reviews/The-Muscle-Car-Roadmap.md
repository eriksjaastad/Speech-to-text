# The Muscle Car Roadmap

**Author:** Claude Code (Opus 4)
**Date:** December 5, 2025
**Philosophy:** "I don't want it just to work. I want it to rip the tires apart."

---

## Executive Summary

This isn't a roadmap for "good enough." This is the supercharged, flame-throwing, tire-shredding version of Erik STT. We're keeping Python as the brain (UI, vocab, regex, focus restoration) and bolting on a WhisperKit Swift binary as the blower (CoreML, Neural Engine, 0.45s latency).

But first, we fix the bugs. You don't put a supercharger on an engine that doesn't run clean.

---

## Current State: The Engine Needs Work

Before we bolt on the blower, let's be honest about what's broken:

| Component | Status | Issue |
|-----------|--------|-------|
| `injection.py` | ❌ | No `restore_app` parameter - focus restoration unwired |
| `main.py` | ❌ | No `target_app` capture in `start_recording()` |
| `engine.py` | ❌ | No `vad_filter=True` - silence not filtered |
| `main.py` | ⚠️ | Uses list with `pop(0)` instead of deque (O(n) vs O(1)) |
| `bubble.py` | ✅ | `setCollectionBehavior_` and `acceptsFirstResponder` working |
| `menubar_app.py` | ✅ | Hides bubble before injection |

---

## The Build: Four Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   🔧 STAGE 1: Make It Run Clean                                            │
│   Fix the bugs. No supercharger on a broken engine.                        │
│                                                                             │
│   ⚡ STAGE 2: Build the Blower (WhisperKit Swift Binary)                   │
│   A standalone Swift CLI that does one thing: transcribe FAST.              │
│                                                                             │
│   🔗 STAGE 3: Bridge It                                                     │
│   Python calls Swift. Keep all your customization. Get the speed.          │
│                                                                             │
│   🔥 STAGE 4: Flames Out the Back                                          │
│   Polish, sound feedback, error handling, rip the tires apart.             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Make It Run Clean (1-2 Days)

### 1.1 Wire Up Focus Restoration

**File: `src/injection.py`**

Add helper functions:
```python
def get_active_app():
    """Get the name of the currently frontmost application."""
    try:
        res = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to name of first application process whose frontmost is true'],
            capture_output=True, text=True, check=True
        )
        return res.stdout.strip()
    except Exception:
        return None

def activate_app(app_name):
    """Activate (focus) a specific application by name."""
    if not app_name:
        return
    script = f'tell application "{app_name}" to activate'
    subprocess.run(["osascript", "-e", script], check=True)
    time.sleep(0.2)  # Allow focus to settle (0.25s for Electron apps)
```

Update `inject_text` signature:
```python
def inject_text(text, force_applescript=False, restore_app=None):
    """
    Inject text at cursor using primary clipboard method, fallback to AppleScript.

    Args:
        text: The text to inject
        force_applescript: If True, skip clipboard and use AppleScript directly
        restore_app: Optional name of app to refocus before injection
    """
    # Restore focus if requested
    if restore_app:
        activate_app(restore_app)

    # ... rest of function unchanged
```

**File: `src/main.py`**

Capture target app in `start_recording()`:
```python
def start_recording(self):
    if self.is_recording:
        return

    # Capture target app IMMEDIATELY
    from src.injection import get_active_app
    self.target_app = get_active_app()
    print(f"🎯 Target App: {self.target_app}")

    # Start with pre-roll buffer
    self.audio_data = list(self.pre_roll_buffer)
    pre_roll_ms = len(self.pre_roll_buffer) * 1024 / self.sample_rate * 1000
    print(f"🎤 Recording... (with {pre_roll_ms:.0f}ms pre-roll)")

    self.is_recording = True
```

**File: `src/menubar_app.py`**

Pass `restore_app` to injection:
```python
# Line ~155, change:
success = inject_text(processed_text)
# To:
success = inject_text(processed_text, restore_app=self.stt.target_app)
```

### 1.2 Enable VAD Filter

**File: `src/engine.py`**

```python
segments, info = self.model.transcribe(
    audio_path,
    language=language,
    initial_prompt=initial_prompt,
    beam_size=5,
    temperature=0.0,
    condition_on_previous_text=False,
    vad_filter=True,  # ADD THIS
    vad_parameters=dict(
        min_silence_duration_ms=500,
        speech_pad_ms=200
    )
)
```

### 1.3 Switch to Deque

**File: `src/main.py`**

```python
from collections import deque

# In __init__:
self.pre_roll_buffer = deque(maxlen=self.pre_roll_max_chunks)

# In audio_callback (simplified - no manual pop needed):
def audio_callback(self, indata, frames, time_info, status):
    chunk = indata.copy()

    if self.is_recording:
        self.audio_data.append(chunk)
    else:
        self.pre_roll_buffer.append(chunk)  # Auto-evicts old items
```

### 1.4 Success Criteria for Stage 1

- [ ] Console shows `🎯 Target App: <app name>` when recording starts
- [ ] Console shows `🔄 Restoring focus to: <app name>` before injection
- [ ] "One two three" test: First word always captured (5/5 tests)
- [ ] VS Code/Cursor test: Text appears in correct window (5/5 tests)
- [ ] Notes.app test: Text appears correctly (5/5 tests)

---

## Stage 2: Build the Blower (WhisperKit Swift Binary)

This is the supercharger. A standalone Swift CLI that does one thing: transcribe audio files as fast as physically possible using Apple's Neural Engine.

### 2.1 Project Structure

```
whisperkit-cli/
├── Package.swift
├── Sources/
│   └── whisperkit-cli/
│       └── main.swift
└── README.md
```

### 2.2 Package.swift

```swift
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "whisperkit-cli",
    platforms: [
        .macOS(.v14)  // Requires macOS 14+ for WhisperKit
    ],
    dependencies: [
        .package(url: "https://github.com/argmaxinc/WhisperKit.git", from: "0.9.0")
    ],
    targets: [
        .executableTarget(
            name: "whisperkit-cli",
            dependencies: ["WhisperKit"]
        )
    ]
)
```

### 2.3 main.swift - The Core

```swift
import Foundation
import WhisperKit

@main
struct WhisperKitCLI {
    static func main() async {
        // Parse arguments
        let args = CommandLine.arguments
        guard args.count >= 2 else {
            printError("Usage: whisperkit-cli <audio-file> [--model <model-name>] [--json]")
            exit(1)
        }

        let audioPath = args[1]
        let modelName = parseArg(args, flag: "--model") ?? "large-v3-turbo"
        let outputJSON = args.contains("--json")

        // Verify file exists
        guard FileManager.default.fileExists(atPath: audioPath) else {
            printError("File not found: \(audioPath)")
            exit(1)
        }

        do {
            // Initialize WhisperKit
            let startInit = Date()
            let whisper = try await WhisperKit(
                model: modelName,
                computeOptions: .init(
                    melCompute: .cpuAndNeuralEngine,
                    audioEncoderCompute: .cpuAndNeuralEngine,
                    textDecoderCompute: .cpuAndNeuralEngine
                )
            )
            let initTime = Date().timeIntervalSince(startInit)

            // Transcribe
            let startTranscribe = Date()
            let result = try await whisper.transcribe(audioPath: audioPath)
            let transcribeTime = Date().timeIntervalSince(startTranscribe)

            // Output
            if outputJSON {
                let output: [String: Any] = [
                    "text": result.text,
                    "init_time_ms": Int(initTime * 1000),
                    "transcribe_time_ms": Int(transcribeTime * 1000),
                    "model": modelName,
                    "segments": result.segments.map { segment in
                        [
                            "text": segment.text,
                            "start": segment.start,
                            "end": segment.end
                        ]
                    }
                ]
                if let jsonData = try? JSONSerialization.data(withJSONObject: output),
                   let jsonString = String(data: jsonData, encoding: .utf8) {
                    print(jsonString)
                }
            } else {
                // Plain text output
                print(result.text)
            }

        } catch {
            printError("Transcription failed: \(error)")
            exit(1)
        }
    }

    static func parseArg(_ args: [String], flag: String) -> String? {
        guard let index = args.firstIndex(of: flag),
              index + 1 < args.count else { return nil }
        return args[index + 1]
    }

    static func printError(_ message: String) {
        FileHandle.standardError.write("\(message)\n".data(using: .utf8)!)
    }
}
```

### 2.4 Build & Install

```bash
# Build release binary
cd whisperkit-cli
swift build -c release

# Copy to accessible location
cp .build/release/whisperkit-cli ~/bin/whisperkit-cli

# Or install system-wide
sudo cp .build/release/whisperkit-cli /usr/local/bin/
```

### 2.5 Performance Expectations

| Model | M1 | M2 | M3 | M4 Pro (Erik's) |
|-------|----|----|----|-----------------|
| large-v3-turbo | ~0.8s | ~0.6s | ~0.5s | **~0.4s** |
| distil-large-v3 | ~0.5s | ~0.4s | ~0.35s | **~0.3s** |

Target: **<0.5s transcription time** for 5-10 second audio clips.

### 2.6 Success Criteria for Stage 2

- [ ] `whisperkit-cli test.wav` returns transcription in <0.5s
- [ ] `whisperkit-cli test.wav --json` returns valid JSON
- [ ] Works with 16kHz WAV files (our format)
- [ ] Model loads in <2s on first run, <0.1s on subsequent (cached)

---

## Stage 3: Bridge It (2-3 Days)

### 3.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PYTHON (The Brain)                                  │
│                                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Menubar UI   │  │ Vocab Inject  │  │ Regex Rules  │  │ Focus Restore │  │
│  │ (rumps)      │  │ (12 terms)    │  │ (8 rules)    │  │ (injection)   │  │
│  └──────┬───────┘  └───────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                  │                 │                   │          │
│         └──────────────────┴────────┬────────┴───────────────────┘          │
│                                     │                                       │
│                          ┌──────────▼──────────┐                            │
│                          │  WhisperKit Bridge  │                            │
│                          │  (subprocess call)  │                            │
│                          └──────────┬──────────┘                            │
│                                     │                                       │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │
                                      │ subprocess.run()
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SWIFT BINARY (The Supercharger)                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          whisperkit-cli                               │  │
│  │                                                                       │  │
│  │   • WhisperKit framework                                              │  │
│  │   • CoreML + Neural Engine                                            │  │
│  │   • Large V3 Turbo model                                              │  │
│  │   • 0.4s transcription (72x real-time)                                │  │
│  │   • JSON output with timing metadata                                  │  │
│  │                                                                       │  │
│  │   🔥 FLAMES. OUT. THE. BACK. 🔥                                       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Python Bridge Implementation

**New file: `src/engine_whisperkit.py`**

```python
"""
WhisperKit Bridge - Calls the Swift binary for transcription.
Falls back to faster-whisper if Swift binary not available.
"""

import subprocess
import json
import shutil
from pathlib import Path

class WhisperKitEngine:
    """Engine that uses WhisperKit Swift binary for transcription."""

    def __init__(self, binary_path=None, model="large-v3-turbo"):
        self.model = model

        # Find the binary
        if binary_path:
            self.binary_path = Path(binary_path)
        else:
            # Search common locations
            for path in [
                Path.home() / "bin" / "whisperkit-cli",
                Path("/usr/local/bin/whisperkit-cli"),
                Path(__file__).parent.parent / "bin" / "whisperkit-cli"
            ]:
                if path.exists():
                    self.binary_path = path
                    break
            else:
                raise FileNotFoundError(
                    "whisperkit-cli not found. Build it with: "
                    "cd whisperkit-cli && swift build -c release"
                )

        print(f"🚀 WhisperKit Engine initialized ({self.binary_path})")
        print(f"   Model: {self.model}")

    def transcribe(self, audio_path, language="en", custom_vocab=None):
        """
        Transcribe audio using WhisperKit.

        Note: custom_vocab is not directly supported by WhisperKit,
        but we keep the parameter for API compatibility. The Python
        layer handles vocab injection via post-processing.
        """
        import time
        start_time = time.time()

        # Call the Swift binary
        result = subprocess.run(
            [
                str(self.binary_path),
                audio_path,
                "--model", self.model,
                "--json"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"WhisperKit failed: {result.stderr}")

        # Parse JSON output
        output = json.loads(result.stdout)

        elapsed = time.time() - start_time

        return {
            "text": output["text"].strip(),
            "language": language,
            "duration": output.get("transcribe_time_ms", 0) / 1000,
            "inference_time": elapsed,
            "engine": "whisperkit",
            "model": self.model
        }


def create_engine(config):
    """
    Factory function to create the best available engine.
    Falls back to faster-whisper if WhisperKit not available.
    """
    engine_type = config.get("whisper", {}).get("engine", "auto")

    if engine_type == "whisperkit" or engine_type == "auto":
        try:
            return WhisperKitEngine(
                model=config.get("whisper", {}).get("model", "large-v3-turbo")
            )
        except FileNotFoundError as e:
            if engine_type == "whisperkit":
                raise  # User explicitly requested WhisperKit
            print(f"⚠️ WhisperKit not available, falling back to faster-whisper")

    # Fallback to faster-whisper
    from src.engine import WhisperEngine
    return WhisperEngine(config=config)
```

### 3.3 Config Update

**File: `config/settings.yaml`**

```yaml
whisper:
  # Engine: "whisperkit" (fast), "faster-whisper" (compatible), or "auto"
  engine: "whisperkit"

  # Model for WhisperKit (ignored if using faster-whisper)
  model: "large-v3-turbo"

  # Fallback settings for faster-whisper
  fallback_model: "distil-medium.en"
  device: "cpu"
  compute_type: "int8"

modes:
  default: "raw"

timing:
  focus_settle_ms: 200
  clipboard_settle_ms: 200
```

### 3.4 Integration with Main App

**File: `src/main.py` (modification)**

```python
# Change the import at the top:
# from src.engine import WhisperEngine, load_settings, load_vocab
from src.engine_whisperkit import create_engine
from src.engine import load_settings, load_vocab

# In __init__, change:
# self.engine = WhisperEngine(config=self.settings)
self.engine = create_engine(self.settings)
```

### 3.5 Success Criteria for Stage 3

- [ ] `python -m src.main` uses WhisperKit by default
- [ ] Falls back to faster-whisper if binary not found
- [ ] Total latency <1s (transcription + injection)
- [ ] Custom vocab still works via post-processing
- [ ] All existing tests pass

---

## Stage 4: Flames Out the Back (Ongoing)

### 4.1 Sound Feedback (Optional)

```python
# src/audio_feedback.py
import subprocess

def play_sound(name):
    """Play system sound."""
    sounds = {
        "start": "/System/Library/Sounds/Tink.aiff",     # Subtle
        "stop": "/System/Library/Sounds/Pop.aiff",       # Subtle
        "success": "/System/Library/Sounds/Glass.aiff",  # Success
        "error": "/System/Library/Sounds/Basso.aiff"     # Error
    }
    path = sounds.get(name)
    if path:
        subprocess.run(["afplay", "-v", "0.5", path])  # 50% volume
```

### 4.2 Retry Logic

```python
def inject_text_with_retry(text, restore_app=None, max_retries=2):
    for attempt in range(max_retries + 1):
        if restore_app:
            activate_app(restore_app)
            time.sleep(0.1 * (attempt + 1))  # Increasing backoff

        if inject_text_clipboard(text):
            return True

        if attempt < max_retries:
            print(f"⚠️ Retry {attempt + 1}/{max_retries}...")

    return inject_text_applescript(text)  # Final fallback
```

### 4.3 Structured Logging

```python
import json
from datetime import datetime

def log_transcription(result, target_app, success):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "text": result["text"],
        "inference_time_ms": int(result["inference_time"] * 1000),
        "engine": result.get("engine", "faster-whisper"),
        "target_app": target_app,
        "injection_success": success
    }

    with open("logs/transcriptions.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

---

## Timeline Summary

| Stage | Duration | Deliverable |
|-------|----------|-------------|
| **Stage 1** | 1-2 days | Bugs fixed, focus restoration wired |
| **Stage 2** | 3-5 days | WhisperKit Swift binary built and tested |
| **Stage 3** | 2-3 days | Python-Swift bridge integrated |
| **Stage 4** | Ongoing | Polish, sound, logging, flames |

**Total to "Ripping Tires":** ~2 weeks

---

## Performance Targets

| Metric | Current | After Stage 1 | After Stage 3 | Target |
|--------|---------|---------------|---------------|--------|
| Transcription | 3.5s | 3.5s | **0.4s** | <0.5s |
| Total Latency | 4.0s | 3.8s | **0.8s** | <1.0s |
| First Word | ⚠️ 80% | ✅ 99% | ✅ 99% | 99% |
| Focus Accuracy | ⚠️ 70% | ✅ 95% | ✅ 99% | 99% |

---

## What You Keep (Python)

- ✅ 12-term custom vocabulary injection
- ✅ 8 regex replacement rules
- ✅ Mode A (raw) / Mode B (formatted)
- ✅ Menubar UI with status bubble
- ✅ Focus restoration logic
- ✅ YAML configuration
- ✅ All your customization

## What You Gain (Swift)

- 🔥 0.4s transcription (was 3.5s)
- 🔥 Apple Neural Engine utilization
- 🔥 CoreML optimization
- 🔥 Large V3 Turbo model
- 🔥 72x real-time processing
- 🔥 Flames. Out. The. Back.

---

*"This isn't about making it work. It's about making it SCREAM."*

— Claude Code (Opus 4), December 2025
