# Gemini 3 Pro Bugs Solution Proposal

**Author:** Gemini 3 Pro
**Date:** December 5, 2025
**Based on:** Reviews by Claude Code (Opus 4), GPT 5.1 Codex Max, and Claude (Opus 4.5)

---

## Executive Summary

After reviewing the codebase and the analyses from previous AI agents, I have synthesized a comprehensive solution for the two critical bugs affecting the Erik STT application. The consensus is clear: **Audio Truncation** is due to the lack of a pre-roll buffer, and **Focus Stealing** is a timing and state management issue between the UI bubble, the injection logic, and the OS focus system.

This proposal outlines the definitive fixes required to stabilize the application.

---

## Bug 1: Audio Truncation ("The Ghost Recording")

### Diagnosis
The application utilizes a persistent audio stream (`sd.InputStream`), which is excellent for latency. However, `audio_callback` in `src/main.py` only captures data when `self.is_recording` is `True`.
- **The Gap:** Human reaction time means users often start speaking *milliseconds before* the hotkey press is fully registered.
- **Current State:** Data flowing through the stream before `start_recording()` is discarded.
- **Result:** The first syllable or word is lost.

### Solution: Circular Pre-Roll Buffer
We must implement a "always-on" circular buffer that retains the last 0.5 to 1.0 seconds of audio.

#### Implementation Plan
1.  **Modify `src/main.py` (`ErikSTT` class):**
    -   Initialize a `collections.deque` with a fixed max length corresponding to ~0.5s of audio.
    -   In `audio_callback`: Always append incoming chunks to this deque.
    -   In `start_recording`: Prepend the contents of this deque to `self.audio_data` before starting the main capture.

2.  **Secondary Measure: VAD Filter**
    -   Modify `src/engine.py` to enable `vad_filter=True` in the Whisper model options. This prevents the engine from hallucinating text from silence if the recording captures only background noise.

---

## Bug 2: Focus Stealing ("The Missing Paste")

### Diagnosis
There are two compounding issues here:
1.  **Timing:** In `src/menubar_app.py`, `run_processing_thread` calls `self.original_stop()`. This method runs transcription **AND** injection. The bubble is only hidden *after* `original_stop()` returns. This means the bubble is visible and potentially interfering with window layering during the injection phase.
2.  **Focus Loss:** The application does not explicitly track or restore the "target application." If the user interacts with the bubble or if Spotlight/Raycast (often triggered by similar hotkeys) intervenes, the focus is lost.

### Solution: Focus Restoration & UI Orchestration

#### Implementation Plan

1.  **Capture Target App Early:**
    -   In `src/main.py` (or `src/menubar_app.py`), capture the name/ID of the frontmost application *immediately* when `start_recording` is triggered. This is when the user is guaranteed to be looking at their target editor.

2.  **Decouple Injection from Processing:**
    -   Refactor `ErikSTT.process_audio` in `src/main.py`. It currently does everything. It should ideally return the text, and let `menubar_app.py` handle the injection.
    -   *Alternative (Less invasive):* Modify `menubar_app.py` to hide the bubble *before* triggering the injection logic, or inside the `process_audio` flow if we pass a callback.

3.  **Explicit Focus Restoration:**
    -   Before `inject_text` runs, use `osascript` to explicitly activate the application we captured in step 1.

4.  **Hardening `NonActivatingPanel`:**
    -   In `src/ui/bubble.py`, add `acceptsFirstResponder` returning `False` to `NonActivatingPanel` to ensure it strictly rejects focus.

---

## Consolidated Action Plan

### Step 1: Fix Audio Truncation (The "Ghost")
- [ ] Import `deque` from `collections` in `src/main.py`.
- [ ] Add `self.pre_roll_buffer` to `ErikSTT.__init__`.
- [ ] Update `audio_callback` to feed the pre-roll buffer.
- [ ] Update `start_recording` to consume the pre-roll buffer.

### Step 2: Fix Focus & Injection (The "Missing Paste")
- [ ] Modify `ErikSTT.process_audio` to accept an optional `on_transcription_complete` callback.
- [ ] In `menubar_app.py`, pass a callback that hides the bubble.
- [ ] *Crucially*: In `process_audio`, invoke this callback *after* transcription but *before* injection.
- [ ] Add `activate_app(app_name)` helper in `src/injection.py`.
- [ ] Update `ErikSTT.start_recording` to capture `self.target_app`.
- [ ] Update `ErikSTT.process_audio` to restore `self.target_app` before injection.

### Step 3: Enhancements
- [ ] Enable `vad_filter=True` in `src/engine.py`.
- [ ] Add `acceptsFirstResponder` to `src/ui/bubble.py`.

---

## Comparison with Previous Proposals

| Feature | Claude Opus 4 | GPT 5.1 Codex | Opus 4.5 | **Gemini 3 Pro (This Proposal)** |
| :--- | :--- | :--- | :--- | :--- |
| **Pre-Roll** | ❌ | ✅ (Conceptual) | ✅ (Detailed) | **✅ (Deque Implementation)** |
| **VAD** | ✅ | ✅ | ❌ | **✅ (As Secondary)** |
| **Focus Fix** | Focus Restore | Safe Hotkey | Hide First | **Capture Early + Restore + Hide First** |
| **UI Fix** | - | - | `acceptsFirstResponder` | **`acceptsFirstResponder`** |

This proposal combines the robust buffer logic (Opus 4.5), the safety of VAD (Claude/GPT), and adds the critical "Capture Early" focus logic which was missing from others.

