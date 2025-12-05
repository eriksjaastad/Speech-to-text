# Opus 4.5 Bug Fix Proposal

**Author:** Claude (Opus 4.5)  
**Date:** December 5, 2025  
**Status:** Proposal (Not Implemented)

---

## Overview

This document proposes fixes for the two active bugs documented in `BUILD_TODO.md`. These are proposals for review—not implemented changes.

---

## Bug 1: Audio Truncation / Silence ("The Ghost Recording")

### Current Behavior
- User speaks a full sentence (e.g., "Quick test number two")
- Transcription output is either empty or captures only the middle/end (e.g., "test number two")
- Log shows reasonable audio duration (5s+), but result is silence or partial

### Root Cause Analysis

After reviewing `src/main.py`, I identified the following:

1. **Persistent stream is already implemented** (lines 64-72) - Good, this eliminates cold-start latency
2. **0.5s tail buffer exists** (line 105-106) - Good, this captures audio after key release
3. **Missing: Pre-roll buffer** - When the user presses the hotkey, we miss the ~200-500ms of speech that occurs *while* the key is being pressed

The issue is that `start_recording()` clears `audio_data = []` and only *then* starts collecting. Any audio captured by the persistent stream before `is_recording = True` is lost.

### Proposed Fix

**Add a pre-roll buffer** that continuously maintains the last ~0.5 seconds of audio even when not recording:

```python
# In __init__, add:
self.pre_roll_buffer = []
self.pre_roll_seconds = 0.5
self.pre_roll_max_chunks = int(self.pre_roll_seconds * self.sample_rate / 1024) + 2

# In audio_callback, change to:
def audio_callback(self, indata, frames, time_info, status):
    chunk = indata.copy()
    
    if self.is_recording:
        self.audio_data.append(chunk)
    else:
        # Maintain rolling pre-roll buffer
        self.pre_roll_buffer.append(chunk)
        if len(self.pre_roll_buffer) > self.pre_roll_max_chunks:
            self.pre_roll_buffer.pop(0)

# In start_recording, change to:
def start_recording(self):
    if self.is_recording:
        return
    
    # Include pre-roll buffer to capture first word
    self.audio_data = list(self.pre_roll_buffer)
    self.is_recording = True
    print("🎤 Recording...")
```

### Alternative Approaches

1. **Voice Activity Detection (VAD):** Use `silero-vad` or `webrtcvad` to detect speech onset and automatically adjust the buffer. More complex but more intelligent.

2. **Larger fixed buffer:** Instead of smart pre-roll, always keep a circular buffer of the last 2 seconds. Simpler but wastes memory/processing.

3. **Hardware-level fix:** Use a dedicated audio capture process that's always running, separate from the main app.

### Recommendation
I recommend **Approach 1 (Pre-roll buffer)** as it's the simplest fix that directly addresses the issue without over-engineering.

---

## Bug 2: Focus Stealing / Injection Failure ("The Missing Paste")

### Current Behavior
- Transcription completes successfully (console shows "✓ Text injected")
- Text does NOT appear in the target application
- Debug shows injection target might be `Electron` or the Bubble itself

### Root Cause Analysis

After reviewing `src/ui/bubble.py`, `src/menubar_app.py`, and `src/injection.py`:

1. **NonActivatingPanel class exists** (bubble.py lines 4-13) - Overrides `canBecomeKeyWindow` and `canBecomeMainWindow`
2. **NSWindowStyleMaskNonactivatingPanel is used** (line 22) - Good
3. **setIgnoresMouseEvents_(True)** (line 40) - Good

**However, the critical issue is timing:**

In `menubar_app.py`, the `run_processing_thread()` method:
1. Calls `self.original_stop()` which runs transcription AND injection
2. THEN hides the bubble

This means the bubble is **still visible** when `Cmd+V` is sent. Even with all the non-activating flags, the bubble's presence can interfere with focus routing.

### Proposed Fix

**Fix 1: Hide bubble BEFORE injection**

Restructure the processing flow so the bubble is hidden before text injection occurs:

```python
def run_processing_thread(self):
    # Step 1: Stop recording (get audio)
    time.sleep(0.5)  # Tail buffer
    self.stt.is_recording = False
    
    # Step 2: Transcribe (this is the slow part)
    # ... transcription code ...
    
    # Step 3: HIDE BUBBLE FIRST
    self.bubble.hide()
    time.sleep(0.15)  # Brief pause for focus to settle
    
    # Step 4: NOW inject text
    inject_text(processed_text)
    
    # Step 5: Reset UI
    self._reset_ui()
```

**Fix 2: Strengthen the NonActivatingPanel**

Add additional safeguards to the bubble window:

```python
class NonActivatingPanel(AppKit.NSPanel):
    def canBecomeKeyWindow(self):
        return False
    
    def canBecomeMainWindow(self):
        return False
    
    def acceptsFirstResponder(self):  # ADD THIS
        return False

# In StatusBubble.__init__, add:
self.window.setCollectionBehavior_(
    AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces |
    AppKit.NSWindowCollectionBehaviorStationary |
    AppKit.NSWindowCollectionBehaviorIgnoresCycle |
    AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
)
```

### Alternative Approaches

1. **Remove the bubble entirely during injection:** Instead of just hiding, destroy and recreate the bubble. More aggressive but guaranteed not to interfere.

2. **Use a different injection method:** Instead of `Cmd+V`, use `NSPasteboard` with direct text insertion via Accessibility APIs. More complex but doesn't rely on keyboard simulation.

3. **Explicit focus restoration:** Before injection, query the frontmost app and explicitly reactivate it:
   ```python
   # Get frontmost app before showing bubble
   frontmost_app = get_frontmost_app()
   # ... do work ...
   # Restore focus before injection
   activate_app(frontmost_app)
   inject_text(text)
   ```

### Recommendation
I recommend **both Fix 1 and Fix 2** together:
- Fix 1 (timing) addresses the primary cause
- Fix 2 (window behaviors) provides defense in depth

---

## Implementation Priority

| Bug | Severity | Complexity | Recommended Order |
|-----|----------|------------|-------------------|
| Bug 2 (Focus Stealing) | High | Medium | First |
| Bug 1 (Audio Truncation) | Medium | Low | Second |

Bug 2 is more impactful because it causes complete failure of the core use case (text doesn't appear at all). Bug 1 is annoying but partial transcription is better than no injection.

---

## Testing Plan

### Bug 1 Tests
1. Start recording and immediately say "One two three"
2. Verify "One" is captured in transcription
3. Test with different speaking speeds
4. Measure actual pre-roll captured (should be ~500ms)

### Bug 2 Tests
1. Open Notes.app, position cursor
2. Run STT workflow
3. Verify text appears in Notes (not in console only)
4. Test with different target apps: Cursor, Safari, TextEdit
5. Log the `Active App for Injection` debug output to confirm correct targeting

---

## Questions for Review

1. Is 0.5 seconds enough pre-roll, or should it be longer?
2. Should we add user-configurable pre-roll in `settings.yaml`?
3. For Bug 2, is the 150ms delay after hiding sufficient, or should it be longer?
4. Should we add a visual/audio confirmation when injection succeeds?

---

*This proposal is open for review by other AI agents and Erik before implementation.*

