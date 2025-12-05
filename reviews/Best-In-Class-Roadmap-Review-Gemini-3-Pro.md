# Best-in-Class Roadmap Review: Gemini 3 Pro

**Author:** Gemini 3 Pro
**Date:** December 5, 2025
**Subject:** Critical Review of "Best-In-Class Roadmap" (Claude Code Opus 4)

---

## Executive Summary

The **Best-In-Class Roadmap** provides an excellent high-level strategic vision, particularly regarding the transition to Apple Silicon acceleration (Phase 2). However, its tactical assessment of the "Current State" (Phase 1) is already lagging behind reality.

**Verdict:**
*   **Strategic Vision (Phase 2/3):** ⭐⭐⭐⭐⭐ (Spot on).
*   **Tactical Accuracy (Phase 1):** ⭐⭐⭐ (Outdated).

---

## 1. The "Unwired Fix" is Solved
The roadmap repeatedly emphasized that the focus restoration logic (the "#1 user-facing bug") was "unwired."
**Correction:** As of the latest commit (`Implement Gemini 3 Pro Bug Fixes`), this is **FALSE**.
*   We *do* capture `target_app` in `main.py`.
*   We *do* pass `restore_app` in `menubar_app.py`.
*   We *do* use it in `injection.py`.
*   **Status:** The "Quick Wins" for reliability are already deployed.

## 2. Strong Endorsement: The MLX Path (Phase 2)
The recommendation to switch to `mlx-whisper` (Apple MLX framework) is the single most valuable technical insight in the document.
*   **Why:** `faster-whisper` is CPU-bound (Int8). The Neural Engine (ANE) on M-series chips is sitting idle.
*   **Benefit:** Moving to MLX should theoretically drop latency from ~3.5s to <1s *without* a generic Swift rewrite.
*   **Action:** This should be the immediate next priority after verification.

## 3. Critique of "Phase 3: Streaming"
The roadmap suggests investigating "Streaming Transcription" in Python (`async for chunk...`).
**Counter-Point:** This is a trap.
*   **Complexity:** Implementing robust streaming VAD and partial audio merging in Python is notoriously brittle.
*   **Diminishing Returns:** If `mlx-whisper` gets us to <1s latency, the complexity of streaming isn't worth it.
*   **Better Path:** If <1s isn't fast enough, skip Python streaming and go straight to **WhisperKit (Swift)**. Don't waste weeks building a fragile Python streaming engine.

## 4. Architecture: Practicality vs. Purity
The roadmap suggests "Dependency Injection" and "Config Classes."
**Critique:** While technically "Best-in-Class," this is potential over-engineering for a single-developer desktop utility.
*   **Recommendation:** Stick to the current modular design. It's clean enough. Focus effort on **Performance (MLX)** rather than Refactoring for Refactoring's sake.

---

## Adjusted Prioritized Roadmap

Based on this review, here is the modified, optimized path forward:

### ✅ Phase 1: Reliability (DONE)
*   [x] Pre-roll Buffer (Deque)
*   [x] Focus Restoration (Wired Up)
*   [x] VAD Filter (Enabled)

### 🚀 Phase 2: Speed (Next)
*   [ ] **Switch Engine:** Replace `faster-whisper` with `mlx-whisper`.
*   [ ] **Goal:** <1s Latency on Apple Silicon.

### 🔮 Phase 3: The "Nuclear Option" (Long Term)
*   [ ] **Skip Python Streaming.**
*   [ ] **Go Native:** If MLX isn't fast enough, rewrite the core transcription engine in Swift using WhisperKit, keeping Python as the UI/Controller wrapper.

---

**Final Word:**
The roadmap is a solid guide, but we have already cleared the "Phase 1" hurdles. The only thing standing between Erik STT and "Best-in-Class" performance is the **MLX migration**.

**Let's go.**
