# Best-In-Class Roadmap

**Author:** Claude Code (Opus 4)
**Date:** December 5, 2025
**Goal:** Take Erik STT from B+ to A+ across every category

---

## Current State vs. Best-In-Class

| Category | Current | Target | Gap |
|----------|---------|--------|-----|
| Architecture | 🟢 B+ | 🟢 A | Minor cleanup |
| Customization | 🟢 A | 🟢 A+ | Already leading |
| Performance | 🟡 C | 🟢 A | Major work needed |
| UX Polish | 🟡 B | 🟢 A | Wire up focus restoration |
| Reliability | 🟡 B- | 🟢 A | VAD + timing fixes |
| Portability | 🟢 B+ | 🟢 A | Minor improvements |

---

## Category 1: Architecture

### Current State: B+
- Clean modular design
- Good separation of concerns
- YAML-based configuration

### What Best-In-Class Looks Like
- **WhisperKit:** Clean Swift architecture with protocol-based design
- **OpenSuperWhisper:** Native SwiftUI with proper MVVM

### Recommendations

#### 1.1 Use Dependency Injection for Testing
```python
# Current: Hard-coded dependencies
class ErikSTT:
    def __init__(self):
        self.engine = WhisperEngine(config=self.settings)

# Best-in-class: Injectable dependencies
class ErikSTT:
    def __init__(self, engine=None, injector=None):
        self.engine = engine or WhisperEngine(config=self.settings)
        self.injector = injector or TextInjector()
```

**Why:** Enables unit testing without actual Whisper model, faster development iteration.

#### 1.2 Extract Configuration into a Config Class
```python
# Create: src/config.py
@dataclass
class STTConfig:
    model: str = "distil-medium.en"
    device: str = "cpu"
    compute_type: str = "int8"
    pre_roll_seconds: float = 0.5
    post_roll_seconds: float = 0.5
    vad_enabled: bool = True
    vad_silence_ms: int = 500

    @classmethod
    def from_yaml(cls, path: str) -> 'STTConfig':
        ...
```

**Why:** Type-safe configuration, IDE autocomplete, validation at load time.

#### 1.3 Add Proper Logging
```python
import logging

logger = logging.getLogger("erik_stt")
logger.setLevel(logging.DEBUG)

# Replace print statements:
logger.info("🎤 Recording... (with %dms pre-roll)", pre_roll_ms)
logger.debug("Audio chunk received: %d frames", len(chunk))
```

**Why:** Configurable log levels, file output, easier debugging.

---

## Category 2: Customization

### Current State: A (Already Leading!)
- 12 custom vocabulary terms
- 8 regex replacement rules
- Two processing modes (raw/formatted)

### What Best-In-Class Looks Like
You're already ahead of OpenSuperWhisper, Whispr, and Ottotone here. None of them have vocab injection + post-processing.

### Recommendations to Reach A+

#### 2.1 Dynamic Vocabulary Loading
```python
# Allow hot-reloading vocab without restart
def reload_vocab(self):
    self.custom_vocab = load_vocab(self.vocab_path)
    logger.info("Reloaded %d custom terms", len(self.custom_vocab))

# Add menubar option: "Reload Vocabulary"
```

#### 2.2 Per-App Profiles
```yaml
# config/profiles.yaml
profiles:
  cursor:
    mode: "raw"
    extra_vocab: ["async", "await", "kwargs"]
  notes:
    mode: "formatted"
    extra_vocab: []
  slack:
    mode: "formatted"
    replacements:
      "at channel": "@channel"
```

**Why:** Different apps need different behavior. Coding needs raw, Slack needs formatted.

#### 2.3 Learning Mode
```python
# Log corrections for future analysis
def log_correction(self, original: str, corrected: str):
    with open("logs/corrections.jsonl", "a") as f:
        json.dump({
            "timestamp": time.time(),
            "original": original,
            "corrected": corrected,
            "app": self.target_app
        }, f)
        f.write("\n")
```

**Why:** Build a dataset of your corrections to auto-generate new replacement rules.

---

## Category 3: Performance

### Current State: C (3.5s latency, CPU-only)
This is the biggest gap. WhisperKit achieves 0.45s on Apple Silicon.

### What Best-In-Class Looks Like
- **WhisperKit:** 0.45s latency, 72x real-time on M2 Ultra
- **whisper.cpp:** Metal acceleration, ~10x faster than CPU

### Recommendations

#### 3.1 Enable VAD Filter (Quick Win)
```python
# In engine.py transcribe():
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

**Impact:** Filters silence before processing, reduces wasted inference time.

#### 3.2 Switch to mlx-whisper (Medium Effort)
```bash
pip install mlx-whisper
```

```python
# New engine option in config:
if config.get("engine") == "mlx":
    import mlx_whisper
    self.transcribe = mlx_whisper.transcribe
```

**Impact:** Apple MLX framework uses Metal/Neural Engine. Expected 3-5x speedup on M-series chips.

**Benchmark targets:**
| Model | CPU (current) | MLX (target) |
|-------|---------------|--------------|
| distil-medium.en | 3.5s | ~0.8s |
| large-v3 | 6.3s | ~1.5s |

#### 3.3 Parallel Model Loading (Medium Effort)
```python
# Load model in background thread at startup
def __init__(self):
    self.model_ready = threading.Event()
    threading.Thread(target=self._load_model, daemon=True).start()

def _load_model(self):
    self.model = WhisperModel(...)
    self.model_ready.set()

def transcribe(self, ...):
    self.model_ready.wait()  # Block until model ready
    ...
```

**Impact:** App starts instantly, model loads in background.

#### 3.4 Streaming Transcription (High Effort)
```python
# Instead of batch transcription, stream results
async def transcribe_streaming(self, audio_stream):
    buffer = AudioBuffer()
    async for chunk in audio_stream:
        buffer.append(chunk)
        if buffer.has_speech_segment():
            partial = self.model.transcribe(buffer.get_segment())
            yield partial
```

**Impact:** Text appears as you speak, not after. WhisperKit does this.

#### 3.5 Ultimate: WhisperKit Migration (High Effort)
For sub-500ms latency, the only path is native CoreML:

```swift
// Swift implementation using WhisperKit
import WhisperKit

let whisper = try await WhisperKit()
let result = try await whisper.transcribe(audioPath: url)
```

**Impact:** 0.45s latency, 72x real-time. But requires Swift rewrite.

**Hybrid approach:** Keep Python for config/UI, call Swift binary for transcription:
```python
result = subprocess.run(
    ["./whisperkit-cli", "--audio", temp_path],
    capture_output=True, text=True
)
```

---

## Category 4: UX Polish

### Current State: B (Bubble works, but focus issues)

### What Best-In-Class Looks Like
- **Superwhisper (commercial):** Seamless focus handling, never steals focus
- **Raycast:** Instant response, beautiful animations

### Recommendations

#### 4.1 Wire Up Focus Restoration (Critical!)

This is the "unwired fix" - the code exists but isn't connected.

**Step 1: Add helper functions to injection.py**
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
    time.sleep(0.15)  # Allow focus to settle
```

**Step 2: Update inject_text signature**
```python
def inject_text(text, force_applescript=False, restore_app=None):
    # Restore focus if requested
    if restore_app:
        activate_app(restore_app)
    # ... rest of function
```

**Step 3: Capture target in start_recording (main.py)**
```python
def start_recording(self):
    if self.is_recording:
        return

    # Capture target app IMMEDIATELY
    from src.injection import get_active_app
    self.target_app = get_active_app()
    print(f"🎯 Target App: {self.target_app}")

    # ... rest of function
```

**Step 4: Pass target to inject_text (menubar_app.py)**
```python
# Line 155, change:
success = inject_text(processed_text)
# To:
success = inject_text(processed_text, restore_app=self.stt.target_app)
```

#### 4.2 Increase Timing Margins for Electron Apps
```python
# In menubar_app.py:
self.bubble.hide()
time.sleep(0.25)  # Increase from 0.15s

# In injection.py inject_text_clipboard():
time.sleep(0.25)  # Increase from 0.2s
```

**Why:** VS Code, Cursor, Slack are all Electron apps with slow focus handling.

#### 4.3 Add Sound Feedback
```python
import subprocess

def play_sound(name):
    """Play system sound."""
    sounds = {
        "start": "/System/Library/Sounds/Pop.aiff",
        "stop": "/System/Library/Sounds/Blow.aiff",
        "success": "/System/Library/Sounds/Glass.aiff",
        "error": "/System/Library/Sounds/Basso.aiff"
    }
    subprocess.run(["afplay", sounds.get(name, sounds["success"])])
```

**Why:** Audio confirmation without looking at screen. Superwhisper does this.

#### 4.4 Animated Bubble States
```python
# Pulse animation while recording
def animate_recording(self):
    while self.is_recording:
        for alpha in [0.85, 0.7, 0.85]:
            self.window.setAlphaValue_(alpha)
            time.sleep(0.3)
```

---

## Category 5: Reliability

### Current State: B- (Pre-roll helps, but issues remain)

### What Best-In-Class Looks Like
- **Otter.ai:** 99%+ uptime, graceful error handling
- **Whispr:** Robust silence detection

### Recommendations

#### 5.1 Use Deque for Pre-roll Buffer
```python
from collections import deque

# In __init__:
self.pre_roll_buffer = deque(maxlen=self.pre_roll_max_chunks)

# In audio_callback (simpler, O(1)):
self.pre_roll_buffer.append(chunk)
# No need for manual pop - deque auto-evicts
```

**Impact:** O(1) vs O(n) for buffer management. Matters at 60+ callbacks/second.

#### 5.2 Synchronous Bubble Hide
```python
# Current (async, race condition):
self.bubble.hide()  # Schedules on main thread
time.sleep(0.15)    # Hope it's done

# Better (synchronous wait):
import threading

def hide_and_wait(self):
    done = threading.Event()

    def _hide():
        self.window.orderOut_(None)
        done.set()

    AppHelper.callAfter(_hide)
    done.wait(timeout=0.5)  # Block until actually hidden
```

#### 5.3 Retry Logic for Injection
```python
def inject_text_with_retry(text, restore_app=None, max_retries=3):
    for attempt in range(max_retries):
        if restore_app:
            activate_app(restore_app)
            time.sleep(0.1 * (attempt + 1))  # Increasing backoff

        if inject_text_clipboard(text):
            return True

        logger.warning(f"Injection attempt {attempt + 1} failed, retrying...")

    return inject_text_applescript(text)  # Final fallback
```

#### 5.4 Health Checks on Startup
```python
def check_permissions(self):
    """Verify all required permissions are granted."""
    issues = []

    # Check microphone
    if not self._check_mic_permission():
        issues.append("Microphone access not granted")

    # Check accessibility
    if not self._check_accessibility():
        issues.append("Accessibility permission not granted")

    if issues:
        self._show_permission_dialog(issues)
        return False
    return True
```

#### 5.5 Graceful Degradation
```python
def transcribe_safe(self, audio_path, **kwargs):
    """Transcribe with fallback options."""
    try:
        return self.transcribe(audio_path, **kwargs)
    except MemoryError:
        logger.warning("OOM - falling back to smaller model")
        self.load_model("tiny.en")
        return self.transcribe(audio_path, **kwargs)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"text": "", "error": str(e)}
```

---

## Category 6: Portability

### Current State: B+ (Works on Intel, unlike competitors)

### What Best-In-Class Looks Like
- Works on Intel AND Apple Silicon
- Optional GPU acceleration where available
- Graceful fallback

### Recommendations

#### 6.1 Auto-Detect Best Backend
```python
import platform

def get_optimal_config():
    """Detect hardware and return optimal configuration."""
    machine = platform.machine()

    if machine == "arm64":  # Apple Silicon
        return {
            "engine": "mlx",  # or "whisperkit" if installed
            "model": "distil-large-v3",
            "device": "mps"
        }
    else:  # Intel
        return {
            "engine": "faster-whisper",
            "model": "distil-medium.en",
            "device": "cpu",
            "compute_type": "int8"
        }
```

#### 6.2 Optional Dependencies
```python
# In engine.py:
try:
    import mlx_whisper
    HAS_MLX = True
except ImportError:
    HAS_MLX = False

def create_engine(config):
    if config.engine == "mlx" and HAS_MLX:
        return MLXWhisperEngine(config)
    else:
        return FasterWhisperEngine(config)
```

---

## Implementation Priority

### Phase 1: Quick Wins (1 day)
| Task | Impact | Effort | Files |
|------|--------|--------|-------|
| Wire up focus restoration | High | Low | injection.py, main.py, menubar_app.py |
| Enable VAD filter | Medium | Trivial | engine.py |
| Use deque for pre-roll | Low | Trivial | main.py |
| Increase timing margins | Medium | Trivial | menubar_app.py, injection.py |

### Phase 2: Medium Effort (1 week)
| Task | Impact | Effort | Files |
|------|--------|--------|-------|
| Add mlx-whisper support | High | Medium | engine.py, config |
| Add sound feedback | Medium | Low | New file |
| Proper logging | Medium | Medium | All files |
| Config dataclass | Medium | Medium | New file |

### Phase 3: High Effort (2+ weeks)
| Task | Impact | Effort | Files |
|------|--------|--------|-------|
| Streaming transcription | Very High | High | engine.py, main.py |
| WhisperKit integration | Very High | Very High | New Swift code |
| Per-app profiles | Medium | Medium | config, main.py |
| Learning mode | Medium | Medium | New file |

---

## Success Metrics

### Target Benchmarks

| Metric | Current | Target | Best-in-Class |
|--------|---------|--------|---------------|
| Latency | 3.5s | <1s | 0.45s (WhisperKit) |
| First-word capture | ~80% | 99% | 99% |
| Focus restoration | ~70% | 99% | 99% |
| Cold start | ~5s | <2s | <1s |
| Custom vocab accuracy | ~90% | 95% | 95%+ |

### Definition of A+

- [ ] Latency under 1 second on Apple Silicon
- [ ] First word never cut off
- [ ] Text always appears in correct app
- [ ] Works in full-screen apps
- [ ] Works with Electron apps (VS Code, Cursor, Slack)
- [ ] Graceful error handling
- [ ] No crashes or hangs
- [ ] Sound/visual feedback at each stage
- [ ] Hot-reload configuration

---

## Final Thoughts

You're closer than you think. The architecture is solid, customization is already best-in-class, and the fixes for reliability are mostly written - they just need to be connected.

**The three highest-impact changes:**
1. **Wire up focus restoration** - This is the #1 user-facing bug
2. **Enable VAD filter** - One line change, immediate benefit
3. **Add mlx-whisper** - 3-5x speedup on Apple Silicon

Do these three things and you'll jump from B+ to A-.

The path to A+ requires streaming transcription or WhisperKit - that's the only way to match 0.45s latency. But A- with rock-solid reliability is better than A+ with bugs.

---

*"Best-in-class isn't about having every feature. It's about the features you have working flawlessly."*

— Claude Code (Opus 4), December 2025
