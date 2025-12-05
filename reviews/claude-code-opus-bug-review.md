# Bug Review & Recommendations
**Model:** Claude Code (Opus 4)
**Date:** December 5, 2025
**Branch:** `claude/compare-whisper-repos-01457JBnuvPtQNW8bRyrsxa4`

---

## Executive Summary

I compared Erik STT against popular open-source Whisper repos: **OpenSuperWhisper** (492 stars, Swift), **Whispr** (24 stars, Rust/Tauri), **Ottotone** (Python/faster-whisper), and **WhisperKit** (Apple's CoreML framework). This review covers the two active bugs and provides recommendations based on how other projects solve similar issues.

---

## Bug #1: Audio Truncation ("The Ghost Recording")

### Symptoms
- User speaks a full sentence, but transcription captures only middle/end
- First word(s) cut off despite reasonable audio duration in logs

### Current Implementation Analysis

**What you already have (good):**
- Persistent audio stream (`src/main.py:72-79`) - eliminates startup latency
- Pre-roll buffer of 0.5s (`src/main.py:64-68`) - captures audio before hotkey press
- Post-roll buffer of 0.5s (`src/main.py:123`) - captures audio after hotkey release

**Potential issue found:**
The `menubar_app.py` duplicates processing logic (lines 93-177) and may not be correctly using the pre-roll buffer from `ErikSTT`. It calls `self.original_start()` but then handles `stop_recording` differently, potentially bypassing the buffer logic.

### How Other Repos Solve This

| Repo | Approach |
|------|----------|
| **Ottotone** | Silence detection (VAD) auto-stops recording after speech ends |
| **Whispr** | Uses whisper.cpp with configurable silence threshold |
| **faster-whisper** | Built-in Silero VAD that filters silence >2s |
| **whisper_real_time** | Continuous recording + phrase pause detection |

### Recommendations

#### Quick Fix (Low Effort)
Enable faster-whisper's built-in VAD filter in `src/engine.py`:

```python
# In transcribe() method, add vad_filter parameter:
segments, info = self.model.transcribe(
    audio_path,
    language=language,
    initial_prompt=initial_prompt,
    beam_size=5,
    temperature=0.0,
    condition_on_previous_text=False,
    vad_filter=True,  # ADD THIS - filters silence automatically
    vad_parameters=dict(min_silence_duration_ms=500)  # Optional tuning
)
```

#### Medium Fix (Ensure Buffer Consistency)
Audit `menubar_app.py` to ensure it uses the same pre-roll buffer logic as `main.py`. The `run_processing_thread()` method should not duplicate audio processing - it should delegate to `ErikSTT.process_audio()`.

#### Advanced Fix (Full VAD Integration)
Add Silero VAD as a separate pre-processing step for automatic recording stop:

```python
# Conceptual - would require silero-vad package
from silero_vad import load_model, get_speech_timestamps
vad_model = load_model()
# Auto-stop when silence detected for >1.5s after speech
```

---

## Bug #2: Focus Stealing ("The Missing Paste")

### Symptoms
- Transcription completes successfully in console
- Text does NOT appear in target application
- Debug shows injection target is sometimes `Electron` or the Bubble itself

### Current Implementation Analysis

**What you already have (good):**
- `NonActivatingPanel` subclass with `canBecomeKeyWindow() → False` (`src/ui/bubble.py:4-15`)
- `NSWindowStyleMaskNonactivatingPanel` style mask (`src/ui/bubble.py:26`)
- `setIgnoresMouseEvents_(True)` (`src/ui/bubble.py:44`)
- Bubble hidden before injection (`src/menubar_app.py:150`)
- 0.15s delay after hide (`src/menubar_app.py:151`)

**What's missing:**
- No explicit re-activation of the previous frontmost app
- No `becomesKeyOnlyIfNeeded` property set
- Timing may be insufficient for Electron apps (VS Code, Cursor)

### How Other Repos Solve This

| Repo | Approach |
|------|----------|
| **Whispr** | Stores frontmost app before overlay, explicitly re-activates before paste |
| **OpenSuperWhisper** | Uses `becomesKeyOnlyIfNeeded = true` on NSPanel |
| **macOS Best Practice** | CGEvent for keyboard simulation (bypasses AppleScript focus issues) |

### Recommendations

#### Quick Fix #1: Add becomesKeyOnlyIfNeeded
In `src/ui/bubble.py`, after creating the panel:

```python
self.window.setBecomesKeyOnlyIfNeeded_(True)
```

#### Quick Fix #2: Store and Restore Frontmost App
In `src/menubar_app.py`, before showing bubble:

```python
# Store the frontmost app
def get_frontmost_app():
    script = 'tell application "System Events" to name of first process whose frontmost is true'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip()

# Before injection, re-activate it
def activate_app(app_name):
    script = f'tell application "{app_name}" to activate'
    subprocess.run(["osascript", "-e", script])
```

#### Quick Fix #3: Increase Delay for Electron Apps
In `src/menubar_app.py:151` and `src/injection.py:36`:

```python
time.sleep(0.3)  # Increase from 0.15s/0.2s to 0.3s for Electron apps
```

#### Advanced Fix: Use CGEvent Instead of AppleScript
Replace AppleScript keystroke with direct CGEvent (more reliable, doesn't involve System Events focus):

```python
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    kCGHIDEventTap,
    kCGEventKeyDown,
    kCGEventKeyUp,
    CGEventSetFlags,
    kCGEventFlagMaskCommand
)

def paste_with_cgevent():
    # 'v' key code is 9
    event_down = CGEventCreateKeyboardEvent(None, 9, True)
    event_up = CGEventCreateKeyboardEvent(None, 9, False)
    CGEventSetFlags(event_down, kCGEventFlagMaskCommand)
    CGEventSetFlags(event_up, kCGEventFlagMaskCommand)
    CGEventPost(kCGHIDEventTap, event_down)
    CGEventPost(kCGHIDEventTap, event_up)
```

---

## Phase 2 Roadmap Verification

Your `BUILD_TODO.md` already includes these recommendations:

| Recommendation | In TODO? | Priority |
|---------------|----------|----------|
| VAD/Silence Detection | ✅ Yes | Quick Win |
| mlx-whisper (Apple Silicon) | ✅ Yes | Medium Effort |
| WhisperKit/CoreML Migration | ✅ Yes | High Effort |

**Suggested Addition:**
- "Store/restore frontmost app for injection" - should be added as a Quick Win for Bug #2

---

## Competitive Comparison Summary

| Feature | Erik STT | OpenSuperWhisper | Whispr | Ottotone | WhisperKit |
|---------|----------|------------------|--------|----------|------------|
| Stars | N/A | 492 | 24 | 0 | 5k+ |
| Language | Python | Swift | Rust | Python | Swift |
| Engine | faster-whisper | whisper.cpp | whisper.cpp | faster-whisper | CoreML |
| Latency | ~3.5s | Unknown | Unknown | Unknown | **0.45s** |
| Custom Vocab | ✅ 12 terms | ❌ | ✅ | ❌ | ❌ |
| Post-Processing | ✅ 8 rules | ❌ | ❌ | ❌ | ❌ |
| Pre-roll Buffer | ✅ 0.5s | ❌ | ❌ | ❌ | ❌ |
| VAD | ❌ | ❌ | ✅ | ✅ | ✅ |
| Apple Silicon | ❌ CPU only | ✅ Required | ✅ Required | ❌ CPU only | ✅ Native |

### Strengths (Keep These)
1. **Custom vocabulary injection** - Most repos don't have this
2. **Regex replacement pipeline** - Unique personalization feature
3. **Pre-roll buffer** - Actually better than most competitors
4. **YAML configuration** - More user-friendly than JSON/code

### Gaps to Address
1. **VAD for auto-stop** - Enable faster-whisper's built-in VAD
2. **Focus restoration** - Store/restore frontmost app
3. **Apple Silicon acceleration** - Investigate mlx-whisper for <1s latency

---

## Baseline Assessment (For End-of-Day Comparison)

| Category | Current | Target | Notes |
|----------|---------|--------|-------|
| Architecture | 🟢 Solid | 🟢 | Clean modular design |
| Customization | 🟢 Best-in-class | 🟢 | Vocab + replacements unique |
| Performance | 🟡 Middle (3.5s) | 🟢 (<1s) | Needs mlx-whisper |
| UX Polish | 🟡 Has bugs | 🟢 | Fix focus stealing |
| Reliability | 🟡 Intermittent | 🟢 | Fix truncation + paste |
| Portability | 🟢 Better | 🟢 | Works on Intel |

---

## Recommended Priority Order

1. **Enable VAD filter** (5 min) - One line change in `engine.py`
2. **Add becomesKeyOnlyIfNeeded** (5 min) - One line in `bubble.py`
3. **Store/restore frontmost app** (30 min) - New helper functions
4. **Increase injection delay** (5 min) - Tune timing constants
5. **Audit menubar_app.py buffer handling** (1 hr) - Ensure consistency with main.py

---

*End of Review*
