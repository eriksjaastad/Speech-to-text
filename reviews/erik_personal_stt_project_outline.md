# Personal Speech-to-Text Project (Erik-Only STT)

**Working Title:** _Erik STT_ (better name later)  
**Owner:** Erik  
**Platform:** macOS (primary)  
**Scope:** English-only, optimized for Erik’s voice, projects, and jargon.

---

## 1. Vision & Goals

### 1.1 Core Vision

Build a **personal speech-to-text system** that feels **more accurate, predictable, and trustworthy** than Superwhisper _for Erik_, by:
- Focusing **only** on one speaker (you) and one language (English).
- Adapting aggressively to your **voice, accent, and vocabulary**.
- Avoiding “smart” hallucinations and meaning changes in normal dictation.

This is not a generic STT app. It is a **custom tool for your daily workflow**, tuned to your projects and habits.

### 1.2 Primary Goals

1. **“Better than Superwhisper for Erik”**
   - Fewer obvious mis-hearings on your common phrases and jargon.
   - Much more predictable behavior in “normal dictation” mode (no surprise rewrites).

2. **Personalized to Your Voice & Domains**
   - Learns your regular vocabulary: trading, coding, image workflows, van life, etc.
   - Incorporates your corrections over time as first-class training data.

3. **Offline-Capable**
   - **Local-first**: usable with no internet (e.g., in the van with bad signal).
   - Optional **cloud fallback** for “maximum accuracy” mode, but not required.

4. **Integrated Into Daily Workflow**
   - System-wide hotkey for dictation.
   - Drops text into any active app (Cursor, Notes, email, browser, etc.).
   - Simple UX: one main “trusted dictation” mode, plus optional “rewrite” mode.

5. **Incrementally Improve Over Time**
   - Logs enough data (with your consent) to:
     - Improve text post-processing (error correction).
     - Enable future fine-tuning on your voice without changing daily habits.

### 1.3 Non-Goals

- Competing with commercial STT for **all users** or all languages.
- Real-time multi-speaker transcription for meetings.
- Hardcore mobile app support (v1 is macOS-focused).
- Doing “creative rewrites” automatically in the core dictation mode.

---

## 2. High-Level Architecture

### 2.1 Overview

The system has four main layers:

1. **Capture Layer (Client)** – macOS app / helper:
   - Listens to microphone input.
   - Handles push-to-talk or toggle hotkey.
   - Sends audio to the STT engine (local or cloud).
   - Inserts resulting text into the focused app and/or logs it.

2. **Base STT Engine Layer**
   - **Local engine (primary):**
     - Likely `whisper.cpp` or similar Whisper-based engine optimized for macOS.
     - English model (medium/large) configured for high accuracy.
   - **Cloud engine (optional / secondary):**
     - Pluggable API (e.g., OpenAI STT or comparable service) for “maximum accuracy” mode when online.

3. **Personalization & Post-Processing Layer**
   - Custom vocabulary & phrase bias (domain dictionary).
   - Text-level corrections (error mapping, regex rules, learned patterns).
   - Mode-specific behavior:
     - _Raw Dictation_: faithful transcription, minimal changes.
     - _Clean Dictation_: light punctuation and basic grammar fixes, no content changes.
     - _Transform Mode_: optional, explicitly allowed to reshape into tasks/emails, etc.

4. **Logging, Feedback & Training Layer**
   - Saves:
     - Raw transcript from the engine.
     - Final edited version (if you approve / opt in).
     - Simple metadata (date, mode, engine, etc.).
   - This enables:
     - Building a **personal error-correction map**.
     - Optional future **fine-tuning** on your voice.

---

## 3. Modes & UX Design

### 3.1 Dictation Modes

1. **Mode A: Raw / Safe Dictation (Default)**
   - Goal: “Write exactly what Erik said, plus punctuation. Do not invent or rephrase.”
   - Behavior:
     - Takes engine output.
     - Applies only **mechanical fixes** (whitespace, simple punctuation).
     - Applies **strict, reversible normalization** (e.g., fix very common specific mis-hearings via a mapping table).

2. **Mode B: Light Cleanup**
   - Goal: Make the text more readable **without changing meaning**.
   - Behavior:
     - Small grammar/punctuation fixes.
     - Capitalization and sentence boundaries.
     - No content additions or stylistic rewrites.

3. **Mode C: Transform / Prompt Mode (Optional)**
   - Goal: Intentionally rewrite into a different style or structure.
   - Behavior:
     - Uses an LLM to turn speech into emails, tasks, summaries, etc.
     - Only activated when explicitly chosen (e.g., different hotkey or UI toggle).

### 3.2 macOS Integration

- **System-wide hotkey** (e.g., `⌥⌘V` or `⌥⌘D`):
  - Press & hold (or toggle-on) to record.
  - Release (or toggle-off) to transcribe.
- **Insertion behavior**:
  - Outputs text at the cursor in the active app.
  - Optionally also logs a copy to a local file (for training / archive).

- **Status feedback**:
  - Small menu bar icon (recording / transcribing / idle).
  - Optional transient notification on failure.

---

## 4. Technical Components

### 4.1 Local STT Engine

**Candidate:** Whisper-based engine (e.g., `whisper.cpp` or similar).

Requirements:
- Runs efficiently on macOS (Apple Silicon preferred but not required).
- Supports English-only mode for speed and accuracy.
- Exposes:
  - Streaming or chunk-based transcription.
  - Configuration for model size, beam search, temperature, etc.

Configuration goals:
- Start with a high-accuracy English model (medium/large).
- Tune for:
  - Reasonable latency for everyday dictation.
  - High transcription quality, especially on your typical speaking style.

### 4.2 Cloud STT Engine (Optional)

Pluggable backend (e.g., OpenAI or similar) with:
- Endpoint receiving audio blobs or streams.
- Return JSON with transcript + timing (if available).

Usage policy:
- Only used when:
  - Explicitly requested (e.g., “max accuracy” mode).
  - Internet is available.
- Otherwise, local engine has priority.

### 4.3 Personal Vocabulary & Domain Dictionary

A small, version-controlled text file (e.g., YAML or JSON) like:

```yaml
custom_terms:
  - MNQ
  - ES
  - Runpod
  - Meshy
  - Cochise County
  - 80/20 aluminum
  - TradeZella
  - Make.com
  - n8n
  - Victron
```

- Used by:
  - STT engine (if it supports custom vocabulary / bias lists).
  - Post-processing layer to prefer these tokens when close matches appear.

### 4.4 Error-Correction & Post-Processing

Two main mechanisms:

1. **Static Rule-Based Mapping**
   - Hand-maintained file of common mis-hearings:
     ```yaml
     replacements:
       "man cue": "MNQ"
       "co cheese": "Cochise"
       "pod runner": "Runpod"
       "make dot com": "Make.com"
     ```
   - Applied in Mode A/B, carefully and reversibly.

2. **Learned Correction Model (Later Phase)**
   - Train a small text model or sequence-correction component using:
     - `raw_transcript` → `final_corrected_text` pairs from your edits.
   - Used only in Mode B (light cleanup) or as an optional post-pass.

### 4.5 Logging & Data Storage

Design a simple data format for logs, e.g. JSONL files:

```json
{
  "timestamp": "2025-01-10T12:34:56Z",
  "mode": "raw",
  "engine": "whisper_local_v1",
  "raw_transcript": "raw text from engine...",
  "final_text": "after any post-processing...",
  "context_app": "Cursor",
  "session_id": "uuid-1234"
}
```

- Logs stored locally (e.g., under `~/Documents/erik-stt/logs/`).
- You can regularly back them up / sync as needed.

---

## 5. Phased Plan

### Phase 0 – Setup & Decisions

**Goals:**
- Confirm toolchain and architecture.
- Create repo & project skeleton.

**Tasks:**
- Create Git repo (e.g., `erik-stt` or similar name).
- Add this document as `PROJECT_OVERVIEW.md`.
- Choose:
  - Local STT engine implementation (e.g., `whisper.cpp` wrapper).
  - Preferred model size for v1.
- Decide basic tech for macOS client (e.g., Python + menubar wrapper, or a small Swift app that calls a local server).

**Deliverables:**
- Repo initialized.
- Project overview committed.
- Initial `TODO.md` with Phase 1 tasks.

---

### Phase 1 – Local STT Prototype (CLI First)

**Goals:**
- End-to-end local transcription on macOS.
- No UI yet, just verify quality and performance.

**Tasks:**
- Wire up CLI script:
  - Record short audio clips from mic.
  - Send to local STT engine.
  - Print transcript to terminal.
- Add configuration for:
  - Model size.
  - English-only mode.
  - Basic settings for speed vs accuracy.

**Deliverables:**
- CLI command like:
  ```bash
  ./stt_record_and_transcribe.sh
  ```
- Initial notes on quality vs speed.

---

### Phase 2 – macOS Integration & Hotkey

**Goals:**
- System-wide hotkey to dictate into any app.
- Basic menu bar UI / indicator.

**Tasks:**
- Implement a small macOS app or background service that:
  - Listens for a global hotkey.
  - Records microphone input while active.
  - Calls the local STT engine.
  - Inserts text into the active app via paste/keystrokes.
- Add minimal UI:
  - Menu bar icon showing idle/recording/transcribing.
  - Simple config window for:
    - Mode selection (Raw vs Light Cleanup vs Transform).
    - Engine selection (Local vs Cloud when online).

**Deliverables:**
- Usable v1 dictation tool on macOS using local STT only.
- Documented hotkey and basic usage instructions.

---

### Phase 3 – Personalization & Error Correction

**Goals:**
- Start making it “Erik-specific.”
- Reduce recurring mistakes.

**Tasks:**
- Build **custom vocabulary** file with your common terms.
- Add **rule-based replacements** for top mis-hearings.
- Implement logging:
  - Save raw transcripts and final text (with opt-in toggles).
- (Optional) Build a simple UI or script to:
  - Review logs.
  - Extract common raw→corrected patterns.

**Deliverables:**
- Personalized vocabulary system in place.
- A few rounds of rule-based corrections implemented.
- Log files accumulating for future learning.

---

### Phase 4 – Cloud Fallback & Max Accuracy Mode (Optional)

**Goals:**
- Optional “super accuracy” mode when online.
- Keep local mode as default.

**Tasks:**
- Add support for a cloud STT API as a secondary engine.
- Add UI/setting:
  - Choose engine: Local / Cloud / Auto (Local by default, Cloud on demand).
- Ensure privacy/usage is clearly controlled by you.

**Deliverables:**
- A working dual-engine pipeline (local-first, cloud-optional).
- Clear docs on when cloud is used and how.

---

### Phase 5 – Learned Personal Correction (Optional, Later)

**Goals:**
- Use your accumulated data to train a small correction model.
- Further reduce errors on your voice and vocabulary.

**Tasks:**
- Export `raw_transcript` vs `final_text` training pairs from logs.
- Experiment with:
  - Lightweight sequence-to-sequence model.
  - Or clever heuristics + n-gram/LM-based correction.
- Integrate this as an additional optional post-processing step in Mode B.

**Deliverables:**
- A prototype learned corrector.
- Metrics and subjective evaluation: “Did this actually feel better?”

---

## 6. Risks & Constraints

- **Accuracy vs Latency Trade-Off**
  - Larger models are slower but more accurate.
  - Need to find a comfortable middle ground for everyday use.

- **Hardware Constraints**
  - macOS only; actual performance will depend on your CPU/GPU/RAM.
  - Later we can tailor model selection once hardware details are locked in.

- **Complexity Creep**
  - Easy to overbuild:
    - Keep v1 focused on **local engine + hotkey + basic personalization**.
    - Cloud + learned correction can come later.

- **Data Privacy & Storage**
  - All logs are local-only by default.
  - You choose what (if anything) is synced or backed up.

---

## 7. Minimal Success Criteria (v1)

We consider v1 a success if:

1. On your Mac, you can press a hotkey, speak, and see text appear in Cursor/Notes/etc. using **local STT only**.
2. In everyday use, you feel:
   - Fewer “WTF” errors compared to Superwhisper on your typical content.
   - More trust that “raw dictation mode” will not creatively rewrite what you said.
3. The system logs enough information (locally) that we can improve it over time without disrupting your workflow.

After that, Phase 3+ becomes about polishing and pushing accuracy further, not reinventing the basics.
