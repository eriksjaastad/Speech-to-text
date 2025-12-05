# The Unwired Fix

**Author:** Claude Code (Opus 4)
**Date:** December 5, 2025
**Status:** Implementation Audit - Critical Findings

---

## Executive Summary

I was asked to review the Gemini 3 Pro bug fix proposal after it had been implemented but before testing. What I found: **the fix exists in the code, but the wires don't connect.** The focus restoration logic was written but never plugged into the actual injection flow.

This is a "Code Review from the Trenches" - I dug into every file to trace the execution path.

---

## The Good News First

The implementation got a lot right:

| Component | Status | Location |
|-----------|--------|----------|
| Pre-roll buffer | ✅ Implemented | `main.py:65-69, 99-103, 112` |
| Persistent audio stream | ✅ Working | `main.py:72-80` |
| `acceptsFirstResponder` override | ✅ Added | `bubble.py:15-16` |
| `setCollectionBehavior_` | ✅ Present | `bubble.py:48-53` |
| Hide bubble before injection | ✅ Working | `menubar_app.py:150-151` |
| `get_active_app()` helper | ✅ Written | `injection.py` (exists in some versions) |
| `activate_app()` helper | ✅ Written | `injection.py` (exists in some versions) |

---

## The Critical Gap: The Unwired Fix

### What Gemini 3 Pro Proposed

> "Capture the name/ID of the frontmost application *immediately* when `start_recording` is triggered... Before `inject_text` runs, use `osascript` to explicitly activate the application we captured."

### What Actually Happened

**The `inject_text()` function signature:**
```python
def inject_text(text, force_applescript=False):
```

**What it should be (per the proposal):**
```python
def inject_text(text, force_applescript=False, restore_app=None):
```

**The call site in `menubar_app.py:155`:**
```python
success = inject_text(processed_text)
```

**What it should be:**
```python
success = inject_text(processed_text, restore_app=self.stt.target_app)
```

### The Result

The `get_active_app()` and `activate_app()` functions exist in some versions of the code, but:
1. `target_app` is never captured in `start_recording()`
2. Even if it were, it's never passed to `inject_text()`
3. Even if it were passed, `inject_text()` doesn't have a `restore_app` parameter

**The fix was written but never wired up.**

---

## Other Observations

### 1. VAD Filter Status: Inconsistent

In one version of `engine.py`, I saw:
```python
vad_filter=True,
vad_parameters=dict(min_silence_duration_ms=500)
```

But the current version (per system reminders) shows:
```python
segments, info = self.model.transcribe(
    audio_path,
    language=language,
    initial_prompt=initial_prompt,
    beam_size=5,
    temperature=0.0,
    condition_on_previous_text=False
)
```

**No `vad_filter` parameter.** This was either removed or never added to the main branch.

### 2. Pre-roll Buffer: List vs Deque

Gemini recommended `collections.deque` for O(1) performance:
```python
self.pre_roll_buffer = deque(maxlen=20)
```

Current implementation uses a regular list with `pop(0)`:
```python
self.pre_roll_buffer = []
# ...
if len(self.pre_roll_buffer) > self.pre_roll_max_chunks:
    self.pre_roll_buffer.pop(0)  # O(n) operation
```

Not a bug, but suboptimal for high-frequency audio callbacks.

### 3. Race Condition in Bubble Hide

```python
self.bubble.hide()
time.sleep(0.15)  # Brief pause to ensure bubble is fully hidden
```

The `bubble.hide()` method uses `AppHelper.callAfter()` which schedules the hide on the main thread asynchronously. The 0.15s sleep is a hopeful guess, not a guarantee. If the main thread is busy, the bubble might still be visible when injection starts.

### 4. Timing Margins for Electron Apps

The current delays:
- After bubble hide: 0.15s
- Before paste (in `inject_text_clipboard`): 0.2s

For Electron apps (VS Code, Cursor), these might be too tight. I'd recommend 0.25-0.3s each based on how other repos handle this.

---

## Recommended Fixes

### Priority 1: Wire Up Focus Restoration

**In `main.py`, add to `start_recording()`:**
```python
def start_recording(self):
    if self.is_recording:
        return

    # Capture target app IMMEDIATELY
    from src.injection import get_active_app
    self.target_app = get_active_app()
    print(f"🎯 Target App: {self.target_app}")

    # ... rest of method
```

**In `injection.py`, update signature:**
```python
def inject_text(text, force_applescript=False, restore_app=None):
    # Restore focus if requested
    if restore_app:
        activate_app(restore_app)

    # ... rest of method
```

**In `menubar_app.py`, pass the target:**
```python
success = inject_text(processed_text, restore_app=self.stt.target_app)
```

### Priority 2: Re-enable VAD Filter

**In `engine.py`:**
```python
segments, info = self.model.transcribe(
    audio_path,
    language=language,
    initial_prompt=initial_prompt,
    beam_size=5,
    temperature=0.0,
    condition_on_previous_text=False,
    vad_filter=True,  # ADD THIS
    vad_parameters=dict(min_silence_duration_ms=500)
)
```

### Priority 3: Use Deque for Pre-roll

**In `main.py`:**
```python
from collections import deque

# In __init__:
self.pre_roll_buffer = deque(maxlen=self.pre_roll_max_chunks)

# In audio_callback (simplified):
self.pre_roll_buffer.append(chunk)  # Auto-evicts old items
```

### Priority 4: Increase Timing Margins

**In `menubar_app.py:151`:**
```python
time.sleep(0.25)  # Increase from 0.15s
```

**In `injection.py` (inside `inject_text_clipboard`):**
```python
time.sleep(0.25)  # Increase from 0.2s
```

---

## Comparison: What Each Model Proposed vs Reality

| Feature | Claude Opus 4 (me) | Opus 4.5 | Gemini 3 Pro | Actually Implemented |
|---------|-------------------|----------|--------------|---------------------|
| Pre-roll buffer | ✅ Recommended | ✅ Detailed | ✅ Deque | ⚠️ List (not deque) |
| VAD filter | ✅ Recommended | ❌ Not mentioned | ✅ Recommended | ❌ Not in current code |
| Capture target app | ✅ Recommended | ❌ Not mentioned | ✅ "Capture Early" | ❌ Not implemented |
| Focus restoration | ✅ Recommended | ❌ Not mentioned | ✅ Recommended | ❌ Not wired up |
| Hide before inject | ✅ Recommended | ✅ Detailed | ✅ Recommended | ✅ Working |
| `acceptsFirstResponder` | ✅ Recommended | ✅ Detailed | ✅ Recommended | ✅ Working |
| `setCollectionBehavior_` | ✅ Recommended | ❌ Not mentioned | ❌ Not mentioned | ✅ Working |
| Timing margins | ✅ Increase for Electron | ❌ Not mentioned | ❌ Not mentioned | ⚠️ May be too tight |

---

## Bottom Line

**Grade: B-** (down from B+ in my earlier review)

The architecture is sound, but critical pieces aren't connected:
1. Focus restoration exists in code but isn't called
2. VAD filter was discussed but not enabled
3. Deque was recommended but list is used

The bugs may persist because **the most important fix (focus restoration) was never actually wired into the execution path.**

---

## Testing Checklist

Before declaring these bugs fixed:

- [ ] Say "One two three" immediately after hotkey - is "One" captured?
- [ ] Check console for `🎯 Target App: <app name>` - does it appear?
- [ ] Check console for `🔄 Restoring focus to: <app name>` - does it appear?
- [ ] Test with VS Code/Cursor as target - does text appear?
- [ ] Test with Notes.app as target - does text appear?
- [ ] Test with full-screen app - does bubble appear correctly?

---

*"The code is there. The logic is there. But the wires don't connect."*

— Claude Code (Opus 4), December 2025
