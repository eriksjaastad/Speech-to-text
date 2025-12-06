# Erik STT Sprint Plan

**Author:** Claude Code (Opus 4)
**Date:** December 5, 2025
**Philosophy:** No timelines. Just done criteria. Crystal clear workflow.

---

## Session Notes (December 5, 2025)

### What We Fixed

**Bug 1: Paste Not Working in Cursor (Electron app)**
- **Root cause:** AppleScript `keystroke "v" using command down` doesn't work reliably with Electron apps
- **Fix:** Added CGEvent (Quartz framework) paste method that posts keystrokes directly to HID event tap
- **Files changed:** `src/injection.py`

**Bug 2: Transcription Truncated (only "Testing." from full sentences)**
- **Root cause:** `initial_prompt` with vocab terms was breaking faster-whisper output
- **Fix:** Disabled vocab injection via initial_prompt; jargon handled via regex post-processing instead
- **Files changed:** `src/engine.py`

### Testing Performed
1. ✅ "testing 123 testing" → Transcribed and pasted correctly
2. ✅ MNQ variations tested → "M-N-Q" correctly replaced with "MNQ"
3. ✅ Paste working in Cursor via Option+Space
4. ✅ Cmd+V manual paste also works (clipboard is correct)

### Key Learnings
- **CGEvent > AppleScript** for Electron apps (Cursor, VS Code, Slack)
- **Regex post-processing > initial_prompt** for jargon (more reliable, deterministic)
- **Timing matters:** Increased delays to 0.3-0.4s for Electron focus/clipboard settle

### MNQ Replacements Added
```yaml
"m-n-q": "MNQ"
"m in-n-q": "MNQ"
"m-and-q": "MNQ"
"m&q": "MNQ"
"m & q": "MNQ"
```

---

## Sprint Overview

| Sprint | Name | Goal |
|--------|------|------|
| **Sprint 1** | Verify & Lock | Verify bug fixes are working, add test coverage, lock the foundation |
| **Sprint 2** | MLX Turbo | Integrate mlx-whisper, benchmark, decide if WhisperKit is needed |
| **Sprint 3** | WhisperKit Blower | Build Swift binary, integrate bridge (only if Sprint 2 says we need it) |
| **Sprint 4** | Polish & Flames | Sound feedback, logging, retry logic, final hardening |

---

# Sprint 1: Verify & Lock

## Goal
Confirm that all bug fixes are working. Add test coverage so we never regress. Lock the foundation before adding performance upgrades.

---

## Tasks

### 1.1 Verify Focus Restoration Wiring ✅ COMPLETE

**What to check (injection.py):**
- [x] `src/injection.py` has `get_active_app()` function
- [x] `src/injection.py` has `activate_app()` function
- [x] `inject_text()` signature includes `restore_app=None` parameter
- [x] `inject_text()` calls `activate_app(restore_app)` before pasting

**What to check (main.py):**
- [x] `src/main.py` `ErikSTT` class has `self.target_app` attribute
- [x] `start_recording()` captures target app: `self.target_app = get_active_app()`
- [x] `start_recording()` prints `🎯 Target App: <name>` to console

**What to check (menubar_app.py):**
- [x] `src/menubar_app.py` passes `restore_app` to injection (via main.py:199)
- [x] Call looks like: `inject_text(processed_text, restore_app=self.target_app)`

**Additional fixes applied during verification:**
- [x] Added CGEvent (Quartz) for paste - fixes Electron apps like Cursor
- [x] Increased timing delays for focus settle (0.3s) and clipboard (0.4s)

---

### 1.2 Verify VAD Filter Enabled ✅ COMPLETE

**What to check:**
- [x] `src/engine.py` `transcribe()` method includes `vad_filter=True`
- [x] `vad_parameters` dict is present with `min_silence_duration_ms=500`

**File location:** `src/engine.py`, inside the `transcribe()` method, in the `self.model.transcribe()` call.

**Note (Dec 5, 2025):** 
- VAD re-enabled after debugging
- `initial_prompt` (vocab injection) was removed — it caused truncated transcriptions
- Jargon (MNQ, etc.) handled via regex post-processing instead (more reliable!)

---

### 1.3 Verify Pre-roll Buffer Uses Deque ✅ COMPLETE

**What to check:**
- [x] `src/main.py` imports `deque` from `collections` (line 14)
- [x] `self.pre_roll_buffer` is initialized as `deque(maxlen=20)` (line 68)
- [x] `audio_callback()` does NOT have manual `pop(0)` logic

---

### 1.4 Verify Bubble Behavior ✅ COMPLETE

**What to check:**
- [x] `src/ui/bubble.py` `NonActivatingPanel` class has:
  - `canBecomeKeyWindow()` returning `False` (line 6)
  - `canBecomeMainWindow()` returning `False` (line 9)
  - `acceptsFirstResponder()` returning `False` (line 12)
- [x] `StatusBubble.__init__()` calls `setCollectionBehavior_()` (line 47) with:
  - `NSWindowCollectionBehaviorCanJoinAllSpaces`
  - `NSWindowCollectionBehaviorStationary`
  - `NSWindowCollectionBehaviorIgnoresCycle`
  - `NSWindowCollectionBehaviorFullScreenAuxiliary`
- [x] `hide()` method includes a delay (0.25s) after calling `orderOut_`

---

### 1.5 Verify Timing Configuration ✅ COMPLETE

**What to check:**
- [x] `src/injection.py` `inject_text_clipboard()` has delay before paste: **0.4s** (increased for Electron)
- [x] `src/injection.py` `activate_app()` has delay after activation: **0.3s** (increased for Electron)
- [x] `src/ui/bubble.py` `hide()` has delay: **0.25s**

**Optional enhancement:**
- [ ] Timing values are in `config/settings.yaml` instead of hardcoded
- [ ] Config keys: `focus_settle_ms`, `clipboard_settle_ms`, `bubble_hide_ms`

**Note:** Timing values increased from original to support Electron apps (Cursor, VS Code)

---

### 1.6 Create Test Script

**Create file:** `tests/test_manual.py`

This script runs manual verification tests. Human observes results.

```
Test 1: First Word Capture
- Record "One two three" immediately after hotkey
- PASS: Transcription includes "One"
- FAIL: Transcription starts with "two" or "three"

Test 2: Focus Restoration (Notes.app)
- Open Notes.app, position cursor
- Run transcription
- PASS: Text appears in Notes.app
- FAIL: Text appears elsewhere or nowhere

Test 3: Focus Restoration (VS Code)
- Open VS Code, position cursor in editor
- Run transcription
- PASS: Text appears in VS Code editor
- FAIL: Text appears elsewhere or nowhere

Test 4: Focus Restoration (Cursor)
- Open Cursor, position cursor in editor
- Run transcription
- PASS: Text appears in Cursor editor
- FAIL: Text appears elsewhere or nowhere

Test 5: Silence Handling
- Press hotkey, say nothing for 3 seconds, release
- PASS: No text injected OR warning shown
- FAIL: Random hallucinated text injected
```

---

### 1.7 Run Tests and Record Results

**Create file:** `tests/sprint1_results.md`

Run each test 5 times. Record pass/fail for each run.

| Test | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Pass Rate |
|------|-------|-------|-------|-------|-------|-----------|
| First Word Capture | | | | | | /5 |
| Focus: Notes.app | | | | | | /5 |
| Focus: VS Code | | | | | | /5 |
| Focus: Cursor | | | | | | /5 |
| Silence Handling | | | | | | /5 |

---

## Done Criteria for Sprint 1

**All of these must be true:**

- [ ] All code verification checks (1.1 - 1.5) pass
- [ ] Test script exists at `tests/test_manual.py`
- [ ] Test results recorded in `tests/sprint1_results.md`
- [ ] First Word Capture: 5/5 passes
- [ ] Focus Notes.app: 4/5 or better
- [ ] Focus VS Code: 4/5 or better
- [ ] Focus Cursor: 4/5 or better
- [ ] Silence Handling: 5/5 passes
- [ ] Console shows `🎯 Target App:` when recording starts
- [ ] Console shows `🔄 Restoring focus to:` before injection

**If any test fails consistently (less than 4/5):**
- Document the failure
- Fix the bug
- Re-run all tests
- Do not proceed to Sprint 2 until all criteria pass

---

## Artifacts Produced

- [ ] `tests/test_manual.py` - Manual test script
- [ ] `tests/sprint1_results.md` - Test results with pass rates
- [ ] All existing code verified (no new code required if bugs are already fixed)

---

# Sprint 2: MLX Turbo

## Goal
Integrate `mlx-whisper` as an alternative engine. Benchmark performance. Decide if WhisperKit is needed or if MLX is "good enough."

---

## Prerequisites
- Sprint 1 Done Criteria: ALL PASSED
- macOS with Apple Silicon (M1/M2/M3/M4)

---

## Tasks

### 2.1 Install MLX-Whisper

**Commands:**
```bash
pip install mlx-whisper
```

**Verify installation:**
```bash
python -c "import mlx_whisper; print('MLX-Whisper installed')"
```

- [ ] Installation completes without errors
- [ ] Import succeeds

---

### 2.2 Create MLX Engine Wrapper

**Create file:** `src/engine_mlx.py`

This file wraps `mlx-whisper` with the same interface as `WhisperEngine`.

**Required functions/classes:**
- `MLXWhisperEngine` class with:
  - `__init__(self, model="distil-large-v3")`
  - `transcribe(self, audio_path, language="en", custom_vocab=None)` returning dict with:
    - `text`: transcribed text
    - `inference_time`: time in seconds
    - `engine`: "mlx"

**Key difference from faster-whisper:**
- MLX uses different model names
- MLX API is `mlx_whisper.transcribe(audio_path, path_or_hf_repo=model)`
- May not support `initial_prompt` - document this limitation

---

### 2.3 Create Engine Factory

**Create file:** `src/engine_factory.py`

Factory function that returns the appropriate engine based on config.

```python
def create_engine(config):
    """
    Create the best available transcription engine.

    Priority:
    1. MLX (if available and configured)
    2. faster-whisper (fallback)
    """
```

**Config options in `settings.yaml`:**
```yaml
whisper:
  engine: "auto"  # "auto", "mlx", or "faster-whisper"
  mlx_model: "mlx-community/distil-whisper-large-v3"
  fallback_model: "distil-medium.en"
```

- [ ] Factory created
- [ ] Returns MLXWhisperEngine when engine="mlx" or engine="auto" and MLX available
- [ ] Returns WhisperEngine when engine="faster-whisper" or MLX unavailable
- [ ] Prints which engine is being used on startup

---

### 2.4 Integrate Factory into Main App

**Modify:** `src/main.py`

Change engine initialization to use factory:

```python
# Old:
from src.engine import WhisperEngine
self.engine = WhisperEngine(config=self.settings)

# New:
from src.engine_factory import create_engine
self.engine = create_engine(self.settings)
```

- [ ] Main app uses factory
- [ ] App starts and shows which engine is active
- [ ] Transcription works with MLX engine

---

### 2.5 Benchmark: MLX vs faster-whisper

**Create file:** `tests/benchmark_engines.py`

Script that runs the same audio file through both engines and compares:

```
Benchmark Results
=================
Audio file: test_benchmark.wav
Audio duration: X.XX seconds

faster-whisper (distil-medium.en):
  - Transcription: "..."
  - Inference time: X.XX seconds
  - Real-time factor: X.Xx

mlx-whisper (distil-large-v3):
  - Transcription: "..."
  - Inference time: X.XX seconds
  - Real-time factor: X.Xx

Speed improvement: X.Xx faster
```

**Run benchmark:**
1. Record a 5-10 second test audio with speech
2. Run benchmark script
3. Record results

---

### 2.6 Record Benchmark Results

**Create file:** `tests/sprint2_benchmark.md`

| Metric | faster-whisper | mlx-whisper | Difference |
|--------|----------------|-------------|------------|
| Model | distil-medium.en | distil-large-v3 | |
| Inference Time | | | |
| Real-time Factor | | | |
| Transcription Accuracy | | | |
| Jargon Accuracy (MNQ, etc.) | | | |

**Decision point:** Based on results, answer these questions:
1. Is MLX inference time < 1 second? (Target: Yes)
2. Is transcription accuracy acceptable? (Target: Yes)
3. Is jargon accuracy acceptable? (Target: Yes, or fixable via regex)

---

### 2.7 Daily Driver Test

Use MLX engine as your daily driver for at least one work session.

**Record in `tests/sprint2_daily_driver.md`:**
- [ ] Date of test session
- [ ] Number of transcriptions attempted
- [ ] Number of successful injections
- [ ] Any issues encountered
- [ ] Subjective feel: Is it fast enough?

---

## Done Criteria for Sprint 2

**All of these must be true:**

- [ ] `mlx-whisper` installed and importable
- [ ] `src/engine_mlx.py` exists with `MLXWhisperEngine` class
- [ ] `src/engine_factory.py` exists with `create_engine()` function
- [ ] `config/settings.yaml` has engine configuration options
- [ ] Main app uses engine factory
- [ ] App prints which engine is active on startup
- [ ] Benchmark script exists at `tests/benchmark_engines.py`
- [ ] Benchmark results recorded in `tests/sprint2_benchmark.md`
- [ ] Daily driver test completed and documented

**Decision Gate:**
Based on benchmark and daily driver results, choose ONE:

**Option A: MLX is good enough**
- Inference time < 1 second
- Accuracy acceptable
- Mark Sprint 3 as SKIPPED
- Proceed to Sprint 4

**Option B: Need more speed**
- Inference time > 1 second OR accuracy issues
- Proceed to Sprint 3 (WhisperKit)

---

## Artifacts Produced

- [ ] `src/engine_mlx.py` - MLX engine wrapper
- [ ] `src/engine_factory.py` - Engine factory
- [ ] `config/settings.yaml` - Updated with engine config
- [ ] `tests/benchmark_engines.py` - Benchmark script
- [ ] `tests/sprint2_benchmark.md` - Benchmark results
- [ ] `tests/sprint2_daily_driver.md` - Daily driver notes
- [ ] Decision documented: Proceed to Sprint 3 or Skip to Sprint 4

---

# Sprint 3: WhisperKit Blower

## Goal
Build a Swift CLI binary using WhisperKit. Integrate it with Python via subprocess bridge. Achieve < 0.5 second transcription.

**NOTE:** Only execute this sprint if Sprint 2 Decision Gate selected "Option B: Need more speed"

---

## Prerequisites
- Sprint 2 Decision: "Need more speed"
- Xcode installed
- macOS 14 (Sonoma) or later
- Swift 5.9 or later

---

## Tasks

### 3.1 Create Swift Project Structure

**Create directory:** `whisperkit-cli/`

```
whisperkit-cli/
├── Package.swift
├── Sources/
│   └── whisperkit-cli/
│       └── main.swift
└── README.md
```

- [ ] Directory structure created
- [ ] Can navigate to `whisperkit-cli/` directory

---

### 3.2 Create Package.swift

**Create file:** `whisperkit-cli/Package.swift`

```swift
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "whisperkit-cli",
    platforms: [
        .macOS(.v14)
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

- [ ] Package.swift created
- [ ] `swift package resolve` succeeds (downloads dependencies)

---

### 3.3 Create main.swift

**Create file:** `whisperkit-cli/Sources/whisperkit-cli/main.swift`

**Required functionality:**
- Accept audio file path as argument
- Accept `--model` flag for model selection
- Accept `--json` flag for JSON output
- Output transcription to stdout
- Output errors to stderr
- Exit codes:
  - 0: Success
  - 1: General error
  - 2: File not found
  - 3: Model not found

**JSON output format:**
```json
{
  "text": "transcribed text here",
  "inference_time_ms": 423,
  "model": "large-v3-turbo"
}
```

- [ ] main.swift created with all required functionality
- [ ] Handles missing file gracefully
- [ ] Handles missing model gracefully

---

### 3.4 Build Release Binary

**Commands:**
```bash
cd whisperkit-cli
swift build -c release
```

**Verify build:**
```bash
.build/release/whisperkit-cli --help
```

- [ ] Build completes without errors
- [ ] Binary exists at `.build/release/whisperkit-cli`
- [ ] Binary runs and shows help/usage

---

### 3.5 Test Swift Binary Standalone

**Test 1: Basic transcription**
```bash
.build/release/whisperkit-cli /path/to/test.wav
```
- [ ] Outputs transcription text

**Test 2: JSON output**
```bash
.build/release/whisperkit-cli /path/to/test.wav --json
```
- [ ] Outputs valid JSON
- [ ] JSON contains `text`, `inference_time_ms`, `model`

**Test 3: Measure inference time**
- [ ] Inference time < 500ms for 5-10 second audio

**Test 4: Error handling**
```bash
.build/release/whisperkit-cli /nonexistent/file.wav
```
- [ ] Exits with code 2
- [ ] Prints error to stderr

---

### 3.6 Install Binary

**Copy to accessible location:**
```bash
cp .build/release/whisperkit-cli ~/bin/whisperkit-cli
```

OR

```bash
cp .build/release/whisperkit-cli /usr/local/bin/whisperkit-cli
```

- [ ] Binary accessible from any directory
- [ ] `which whisperkit-cli` returns path

---

### 3.7 Create Python Bridge

**Create file:** `src/engine_whisperkit.py`

**Required functionality:**
- `WhisperKitEngine` class with same interface as other engines
- Calls Swift binary via `subprocess.run()`
- Parses JSON output
- Includes timeout (30 seconds)
- Handles errors gracefully
- Falls back to faster-whisper if binary not found

```python
class WhisperKitEngine:
    def __init__(self, binary_path=None, model="large-v3-turbo"):
        ...

    def transcribe(self, audio_path, language="en", custom_vocab=None):
        # Returns dict with: text, inference_time, engine
        ...
```

- [ ] WhisperKitEngine class created
- [ ] Uses subprocess with timeout
- [ ] Parses JSON output correctly
- [ ] Handles binary not found
- [ ] Handles timeout
- [ ] Handles invalid JSON

---

### 3.8 Update Engine Factory

**Modify:** `src/engine_factory.py`

Add WhisperKit to the priority list:

```python
def create_engine(config):
    """
    Priority:
    1. WhisperKit (if available and configured)
    2. MLX (if available)
    3. faster-whisper (fallback)
    """
```

**Config options:**
```yaml
whisper:
  engine: "auto"  # "auto", "whisperkit", "mlx", or "faster-whisper"
  whisperkit_binary: "~/bin/whisperkit-cli"
  whisperkit_model: "large-v3-turbo"
```

- [ ] Factory updated to include WhisperKit
- [ ] Config options documented

---

### 3.9 Benchmark WhisperKit

**Update:** `tests/benchmark_engines.py`

Add WhisperKit to benchmark comparison.

**Run benchmark and record in `tests/sprint3_benchmark.md`:**

| Metric | faster-whisper | mlx-whisper | whisperkit |
|--------|----------------|-------------|------------|
| Inference Time | | | |
| Real-time Factor | | | |
| Total Latency (E2E) | | | |

---

### 3.10 Daily Driver Test (WhisperKit)

Use WhisperKit engine as daily driver for at least one work session.

**Record in `tests/sprint3_daily_driver.md`:**
- [ ] Date of test session
- [ ] Number of transcriptions attempted
- [ ] Number of successful injections
- [ ] Any issues encountered
- [ ] Comparison to MLX feel

---

## Done Criteria for Sprint 3

**All of these must be true:**

- [ ] Swift project structure exists at `whisperkit-cli/`
- [ ] `Package.swift` valid and dependencies resolve
- [ ] `main.swift` implements all required functionality
- [ ] Release binary builds without errors
- [ ] Binary passes all standalone tests (3.5)
- [ ] Binary installed to accessible path
- [ ] `src/engine_whisperkit.py` exists with `WhisperKitEngine` class
- [ ] Engine factory updated to include WhisperKit
- [ ] Benchmark completed and recorded
- [ ] WhisperKit inference time < 500ms
- [ ] Daily driver test completed
- [ ] App works end-to-end with WhisperKit engine

---

## Artifacts Produced

- [ ] `whisperkit-cli/` - Complete Swift project
- [ ] `~/bin/whisperkit-cli` - Installed binary
- [ ] `src/engine_whisperkit.py` - Python bridge
- [ ] `src/engine_factory.py` - Updated factory
- [ ] `tests/sprint3_benchmark.md` - Benchmark results
- [ ] `tests/sprint3_daily_driver.md` - Daily driver notes

---

# Sprint 4: Polish & Flames

## Goal
Add quality-of-life improvements. Harden error handling. Make it feel premium.

---

## Prerequisites
- Sprint 1: PASSED
- Sprint 2: PASSED (and decision made)
- Sprint 3: PASSED or SKIPPED

---

## Tasks

### 4.1 Add Structured Logging

**Create file:** `src/logging_utils.py`

**Log schema (JSONL format):**
```json
{
  "timestamp": "2025-12-05T14:30:00Z",
  "event": "transcription",
  "target_app": "Cursor",
  "engine": "mlx",
  "audio_duration_ms": 5230,
  "inference_time_ms": 450,
  "total_latency_ms": 820,
  "text_length": 42,
  "injection_success": true
}
```

**Log location:** `logs/transcriptions.jsonl`

- [ ] Logging utility created
- [ ] Log file created on first transcription
- [ ] Each transcription appends one JSON line
- [ ] Logs are parseable with `jq`

---

### 4.2 Add Log Rotation

**Requirements:**
- Rotate log when file exceeds 10MB
- Keep 1 backup file (`transcriptions.jsonl.1`)
- Delete older backups

- [ ] Log rotation implemented
- [ ] Tested by creating large log file

---

### 4.3 Add Sound Feedback (Optional)

**Create file:** `src/audio_feedback.py`

**Sounds:**
- Recording start: Subtle tick
- Recording stop: Subtle pop
- Injection success: Subtle glass
- Injection error: Subtle basso

**Config:**
```yaml
audio:
  enabled: false  # Off by default
  volume: 0.2     # 20% volume
```

- [ ] Sound module created
- [ ] Sounds are subtle (not jarring)
- [ ] Disabled by default in config
- [ ] Volume configurable

---

### 4.4 Add Retry Logic for Injection

**Modify:** `src/injection.py`

**Behavior:**
- If clipboard injection fails, wait 100ms and retry once
- If retry fails, fall back to AppleScript
- Log retry attempts

- [ ] Retry logic implemented
- [ ] Retry logged
- [ ] Fallback works

---

### 4.5 Add Warning for Empty Transcription

**Modify:** `src/main.py` or `src/menubar_app.py`

**Behavior:**
- If VAD filters out all audio (silence), show warning
- Do NOT inject empty string
- Log the event

**Console output:**
```
⚠️ No speech detected. Nothing to inject.
```

- [ ] Warning shown for silence
- [ ] Empty string not injected
- [ ] Event logged

---

### 4.6 Add Config Validation on Startup

**Create file:** `src/config_validator.py`

**Checks:**
- All required config keys exist
- Engine setting is valid ("auto", "mlx", "whisperkit", "faster-whisper")
- Timing values are positive numbers
- Model names are non-empty strings

**On invalid config:**
- Print specific error message
- Use safe defaults
- Continue running (don't crash)

- [ ] Validator created
- [ ] Invalid config shows helpful error
- [ ] App continues with defaults

---

### 4.7 Create README with Quick Start

**Update:** `README.md`

**Sections:**
1. What is Erik STT
2. Quick Start (3 commands to get running)
3. Configuration options
4. Troubleshooting common issues
5. Engine comparison (speed vs accuracy)

- [ ] README updated
- [ ] Quick start works for new user
- [ ] All config options documented

---

### 4.8 Final End-to-End Test

Run complete test suite:

1. Fresh start (cold boot)
2. First transcription (model load)
3. 10 consecutive transcriptions
4. Test in Notes.app
5. Test in VS Code
6. Test in Cursor
7. Test silence handling
8. Test long recording (30 seconds)

**Record in `tests/sprint4_final.md`:**
- [ ] All tests documented
- [ ] Pass rate for each test
- [ ] Any remaining issues noted

---

## Done Criteria for Sprint 4

**All of these must be true:**

- [ ] Structured logging implemented and working
- [ ] Log rotation working
- [ ] Sound feedback available (if user enables it)
- [ ] Retry logic for injection working
- [ ] Empty transcription warning working
- [ ] Config validation working
- [ ] README complete and helpful
- [ ] Final E2E test completed with >90% pass rate
- [ ] No critical bugs remaining

---

## Artifacts Produced

- [ ] `src/logging_utils.py` - Logging utilities
- [ ] `src/audio_feedback.py` - Sound feedback
- [ ] `src/config_validator.py` - Config validation
- [ ] `logs/transcriptions.jsonl` - Log file (created at runtime)
- [ ] `README.md` - Updated documentation
- [ ] `tests/sprint4_final.md` - Final test results

---

# Summary: The Complete Journey

```
Sprint 1: Verify & Lock
    └── Confirm bugs are fixed
    └── Test coverage in place
    └── Foundation locked
            │
            ▼
Sprint 2: MLX Turbo
    └── Install mlx-whisper
    └── Benchmark vs faster-whisper
    └── Daily driver test
    └── DECISION: MLX enough?
            │
      ┌─────┴─────┐
      │           │
      ▼           ▼
   [SKIP]    Sprint 3: WhisperKit
      │       └── Build Swift CLI
      │       └── Python bridge
      │       └── Benchmark
      │           │
      └─────┬─────┘
            │
            ▼
Sprint 4: Polish & Flames
    └── Logging
    └── Sound feedback
    └── Retry logic
    └── README
    └── Final testing
            │
            ▼
        🔥 DONE 🔥
```

---

*"No timelines. Just done criteria. Ship when it's ready."*

— Claude Code (Opus 4), December 2025
