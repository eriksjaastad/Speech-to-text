# Erik STT — Final Project Document

**Version:** 1.0  
**Date:** December 2025  
**Status:** Ready to Build

---

## Document History

This document synthesizes:
- Original project outline (Erik)
- Review #1 — Technical implementation strategy (AI Review)
- Review #2 — Gaps, risks, and phase refinements (Claude)
- Review #3 — Integrated design review (ChatGPT)
- Review #4 — M4 Pro optimizations and "One Day" build plan (Gemini)
- Open Questions — Hardware specs and key decisions (Erik)

---

## 1. Project Summary

### 1.1 What This Is

A **personal speech-to-text system** built exclusively for Erik. Not a product. Not generalizable. A custom instrument tuned to one voice, one language (English), one platform (macOS).

### 1.2 Core Problem

Commercial STT tools (Superwhisper, MacWhisper, etc.) optimize for *breadth* — they try to be "smart" for everyone, which makes them unpredictable for power users with niche vocabulary. They hallucinate, rewrite, and mangle domain-specific terms like "MNQ," "Runpod," and "n8n."

### 1.3 Success Criteria

v1 is a success if:

1. Press a hotkey → speak → text appears at cursor in any app (Cursor, Notes, browser, etc.)
2. Fewer "WTF" errors than Superwhisper on Erik's typical content
3. "Raw dictation mode" does exactly what it says — no surprise rewrites
4. The system logs enough data locally to improve over time
5. Works offline (van life compatible)

---

## 2. Locked Decisions

These are **final for v1** based on all reviews and Erik's answers. No more debating.

| Decision | Value | Source |
|----------|-------|--------|
| Target user | Erik only | Outline |
| Language | English only | Outline |
| Platform | macOS only | Outline |
| Hardware | MacBook Pro M4 Pro, 24GB RAM, 20-core GPU | Open Questions |
| Latency tolerance | 2–3 seconds acceptable | Open Questions |
| Mode C (Transform) | **Out of scope for v1** | Open Questions |
| Cloud fallback | **Deprioritized** (Phase 5 or later) | Open Questions |
| Log storage | Local only, finite retention | Open Questions |
| Primary engine | `faster-whisper` (CTranslate2 backend) | All reviews agree |
| Personalization method | `initial_prompt` injection + regex replacements | Reviews 1, 2, 3, 4 |
| Mode B cleanup | Deterministic rules only (no LLM) | Reviews 2, 3, 4 |

---

## 3. Architecture

### 3.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Flow                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [Hold Hotkey] → [Speak] → [Release] → [Text at Cursor]       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Technical Flow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Hotkey (pynput)                                               │
│       ↓                                                         │
│   Audio Capture (sounddevice + numpy)                           │
│       ↓                                                         │
│   Load vocab.yaml → Build initial_prompt                        │
│       ↓                                                         │
│   Whisper Inference (faster-whisper, large-v3)                  │
│       ↓                                                         │
│   Post-Processing (replacements.yaml regex)                     │
│       ↓                                                         │
│   Mode A: Return as-is                                          │
│   Mode B: + capitalize_sentences() + normalize_spacing()        │
│       ↓                                                         │
│   Text Injection (AppleScript, clipboard fallback)              │
│       ↓                                                         │
│   Log to JSONL                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Stack

| Layer | Tool | Why |
|-------|------|-----|
| Audio capture | `sounddevice` + `numpy` | Low latency, raw buffer access |
| STT engine | `faster-whisper` | CTranslate2 backend, 4-6x faster than vanilla Whisper |
| Menubar UI | `rumps` | Native macOS menu bar, pure Python |
| Global hotkeys | `pynput` | Background hotkey listening |
| Text injection | AppleScript (primary), clipboard+paste (fallback) | AppleScript is cleaner; clipboard is safer fallback |
| Config format | YAML | Human-readable, version-controllable |
| Log format | JSONL | Appendable, parseable, future-training-ready |

### 3.3 File Structure

```text
erik-stt/
├── config/
│   ├── settings.yaml       # Hotkeys, model config, modes
│   ├── vocab.yaml          # Custom terms for initial_prompt
│   └── replacements.yaml   # Regex fixes for mis-hearings
├── src/
│   ├── main.py             # Entry point
│   ├── audio_capture.py    # Mic input handling
│   ├── engine.py           # Whisper wrapper
│   ├── post_process.py     # Regex and text cleanup
│   ├── injection.py        # AppleScript/clipboard logic
│   └── menubar_app.py      # Rumps app + hotkey listener
├── logs/
│   └── transcriptions.jsonl
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   └── reviews/
│       ├── review1.md
│       ├── review2.md
│       ├── review3.md
│       └── review4.md
└── requirements.txt
```

---

## 4. Modes (v1)

### Mode A — Raw / Safe Dictation (Default)

**Goal:** "Write exactly what Erik said. Do not invent or rephrase."

**Processing:**
1. Whisper output with `temperature=0.0`, `beam_size=5`
2. Trim whitespace
3. Apply `replacements.yaml` (deterministic regex)
4. Done — no further changes

**Use when:** You want maximum fidelity to what you actually said.

### Mode B — Light Cleanup

**Goal:** Slightly more polished output without changing meaning.

**Processing:**
1. Everything from Mode A, plus:
2. Capitalize sentence starts (regex: after `.!?` + whitespace)
3. Normalize spacing after punctuation
4. Optionally: lightweight punctuation insertion (deterministic library, not LLM)

**Use when:** Drafting emails, notes, or anything that benefits from basic formatting.

### Mode C — Transform ❌

**Status:** Out of scope for v1. Revisit in v2 if needed.

---

## 5. Configuration

### 5.1 settings.yaml

```yaml
# Hotkeys
hotkeys:
  record: "cmd+alt+d"           # Hold to record
  correct_last: "cmd+alt+z"     # Open correction window (Phase 3)

# Audio
audio:
  sample_rate: 16000            # Whisper expects 16kHz
  channels: 1                   # Mono
  dtype: "float32"
  device: null                  # null = system default mic

# Whisper
whisper:
  model: "large-v3"             # M4 Pro can handle it
  language: "en"
  device: "cpu"                 # See "Ambiguous Areas" — test MPS too
  compute_type: "int8"          # 2x speedup, minimal accuracy loss
  beam_size: 5
  temperature: 0.0              # No creativity, strict accuracy
  condition_on_previous_text: false  # Prevents hallucinations

# Modes
modes:
  default: "raw"                # "raw" or "cleanup"

# Logging
logging:
  enabled: true
  path: "~/Documents/erik-stt/logs/"
  max_size_mb: 10               # Rotate after 10MB
  backup_count: 1               # Keep 1 backup, delete older
```

### 5.2 vocab.yaml

```yaml
# Terms to inject into initial_prompt
# These bias Whisper toward recognizing your jargon
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
  
  # Add more as you discover mis-hearings
```

### 5.3 replacements.yaml

```yaml
# Deterministic fixes for known mis-hearings
# Applied via case-insensitive regex
replacements:
  "man cue": "MNQ"
  "co cheese": "Cochise"
  "co-cheese": "Cochise"
  "pod runner": "Runpod"
  "run pod": "Runpod"
  "make dot com": "Make.com"
  "trade zella": "TradeZella"
  "and eight and": "n8n"
  
  # Add more as you encounter them
```

---

## 6. Implementation Roadmap

### Overview

Based on Erik's preference to "build this in a day," the roadmap is compressed but still logical. The "One Day" plan from Review #4 is the sprint; the phased approach is for ongoing refinement.

### Day 1: Minimum Viable Tool

**Step 1 — Hello World (Morning)**
- Goal: Record 5 seconds of audio, save to `test.wav`
- Validates: `sounddevice` works, macOS mic permissions granted
- Success: You can play back the file and it sounds clear

**Step 2 — The Brain (Mid-Day)**
- Goal: Feed `test.wav` into `faster-whisper` with `large-v3`
- Validates: M4 Pro handles the model, inference completes in <3s
- Success: Terminal prints your spoken words

**Step 3 — Jargon Injection (Afternoon)**
- Goal: Wire up `vocab.yaml` into `initial_prompt`
- Validates: The personalization hack actually works
- Success: Say "MNQ" and it prints "MNQ" (not "man cue")

**Step 4 — The Glue (Evening)**
- Goal: Bind to hotkey, inject text via AppleScript
- Validates: End-to-end flow works in any app
- Success: Hold hotkey in Notes.app, speak, release, text appears

### Post-Day-1 Phases

**Phase 2 — Polish & Permissions (Days 2–3)**
- Add `rumps` menubar with status indicator (idle/recording/transcribing)
- Implement startup permission checks (mic, Accessibility)
- Show clear error dialogs when permissions are missing
- Add Mode A / Mode B toggle in menubar dropdown
- Test in multiple apps: Cursor, Notes, Safari, Slack

**Phase 3 — Personal Correction Loop (Week 1–2)**
- Implement "last transcript" memory
- Add correction hotkey (`⌘⌥Z`) that opens a small edit window
- Log both `raw_transcript` and `corrected_text` to JSONL
- Build helper script to scan logs and suggest new `replacements.yaml` entries
- Grow `vocab.yaml` based on actual usage

**Phase 4 — Learned Corrections (Future)**
- Analyze `raw → corrected` pairs from logs
- Start with simple heuristics (frequent substitution patterns)
- Optionally explore lightweight ML correction model
- Only applies to Mode B as optional post-pass

**Phase 5 — Cloud Fallback (Optional/Future)**
- Pluggable cloud STT API for "max accuracy" mode
- Only if local model proves insufficient for specific use cases
- Given M4 Pro + `large-v3`, this may never be needed

---

## 7. Risk Mitigations

### 7.1 macOS Permissions (High Priority)

**Risk:** App breaks silently due to missing/revoked permissions.

**Mitigations:**
- Startup health check verifies: Microphone access, Accessibility access
- If missing: Show clear dialog with instructions and "Re-check" button
- Document "First Run Setup" in `docs/` for reference after OS updates
- Consider code signing to reduce permission friction

### 7.2 Latency Creep

**Risk:** Real-world latency exceeds the 2–3s comfort zone.

**Mitigations:**
- Instrument timing: log `audio_duration`, `inference_time`, `total_latency` per dictation
- Make model choice a config setting (easy to swap `large-v3` → `distil-large-v3` → `medium.en`)
- If average latency climbs, step down model size

### 7.3 Mode B Over-Correction

**Risk:** Even deterministic cleanup changes meaning unexpectedly.

**Mitigations:**
- Build Mode B as composable, auditable steps: `normalize_spacing()`, `capitalize_sentences()`, `apply_replacements()`
- Config flag to disable Mode B entirely
- Log which mode was used for each transcription
- When in doubt, default to Mode A

### 7.4 Log Bloat / Privacy

**Risk:** Logs grow unbounded or store more speech history than comfortable.

**Mitigations:**
- `RotatingFileHandler` with 10MB limit and 1 backup (from Review #4)
- Logs stored in clearly marked folder (`~/Documents/erik-stt/logs/`)
- Manual purge is always an option
- Don't log app context or unnecessary metadata

---

## 8. Ambiguous Areas / Needs Testing

These items have conflicting recommendations or need empirical validation on your specific hardware.

### 8.1 Model Size: `large-v3` vs `distil-large-v3`

| Recommendation | Source |
|----------------|--------|
| `distil-large-v3` (speed + accuracy balance) | Review #2, Review #3 |
| `large-v3` (M4 Pro can handle it, max accuracy) | Review #4 |

**Resolution:** Start with `large-v3`. If latency exceeds 3s on typical utterances, drop to `distil-large-v3`. Make this a config setting so switching is trivial.

### 8.2 Inference Device: CPU vs MPS

Review #4 notes that `faster-whisper` with CTranslate2 often runs faster on **CPU** than MPS (Metal) for int8 operations on Apple Silicon.

**Resolution:** Test both. Run the same 10-second clip through:
- `device: "cpu"` with `compute_type: "int8"`
- `device: "mps"` (if supported) or `device: "auto"`

Log the inference times and pick the faster option.

### 8.3 Log Retention Period

| Recommendation | Source |
|----------------|--------|
| 90 days, then archive/delete | Review #2 |
| 7 days rolling | Review #4 |
| "Shouldn't live forever" | Erik (Open Questions) |

**Resolution:** Start with the `RotatingFileHandler` approach (10MB cap, 1 backup). This is size-based rather than time-based, which is simpler. Revisit if you need time-based retention for training data purposes.

### 8.4 Exact Hotkey Binding

Various suggestions across reviews: `⌘⌥D`, `⌘⌥V`, `Spacebar` (for CLI testing).

**Resolution:** Pick one and make it configurable. Suggested default: `⌘⌥D` (D for Dictate). Avoid `⌘⌥V` since it's close to paste (`⌘V`) and could cause muscle-memory conflicts.

### 8.5 `condition_on_previous_text` Toggle

Review #2 suggested making this configurable for long-form dictation. Reviews #3 and #4 suggest hardcoding it to `false`.

**Resolution:** Default to `false` in config. Add the option to set it `true` but don't expose it in the UI for v1. You can manually edit `settings.yaml` if you want to experiment with long-form sessions.

### 8.6 Correction Hotkey UX

Review #2 proposed a Phase 2.5 "Correction Feedback Loop" with a secondary hotkey. Review #3 included it in Phase 3.

**Resolution:** Implement in Phase 3 as described. Keep "last transcript" in memory. `⌘⌥Z` opens a small correction window. Both versions get logged. This is where the personalization magic compounds over time.

---

## 9. Requirements

### 9.1 requirements.txt

```
faster-whisper>=0.10.0
sounddevice>=0.4.6
numpy>=1.24.0
rumps>=0.4.0
pynput>=1.7.6
PyYAML>=6.0
```

### 9.2 macOS Permissions Required

| Permission | Why | How to Grant |
|------------|-----|--------------|
| Microphone | Audio capture | System Settings → Privacy & Security → Microphone |
| Accessibility | Global hotkeys, text injection | System Settings → Privacy & Security → Accessibility |
| Input Monitoring | May be required for `pynput` | System Settings → Privacy & Security → Input Monitoring |

---

## 10. Code Snippets (Reference)

### 10.1 Initial Prompt Injection (engine.py)

```python
def transcribe(audio_segment, custom_vocab_list):
    """
    Transcribe audio with personalized vocabulary injection.
    """
    # Build the "Erik context" prompt
    prompt_str = "Key terms: " + ", ".join(custom_vocab_list) + "."
    
    segments, info = model.transcribe(
        audio_segment,
        language="en",
        initial_prompt=prompt_str,  # <-- THE SECRET SAUCE
        beam_size=5,
        temperature=0.0,
        condition_on_previous_text=False
    )
    
    return "".join([seg.text for seg in segments])
```

### 10.2 Replacements Post-Processing (post_process.py)

```python
import re
import yaml

def load_replacements(path="config/replacements.yaml"):
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("replacements", {})

def apply_replacements(text, replacements):
    """
    Apply deterministic regex replacements for known mis-hearings.
    """
    for wrong, right in replacements.items():
        pattern = r'\b' + re.escape(wrong) + r'\b'
        text = re.sub(pattern, right, text, flags=re.IGNORECASE)
    return text
```

### 10.3 Log Rotation Setup

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(log_path="logs/transcriptions.jsonl"):
    handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=1                # Keep 1 backup, delete older
    )
    logger = logging.getLogger("erik-stt")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

### 10.4 AppleScript Text Injection (injection.py)

```python
import subprocess

def inject_text_applescript(text):
    """
    Insert text at cursor using AppleScript.
    Falls back to clipboard if this fails.
    """
    # Escape quotes for AppleScript
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    
    script = f'''
    tell application "System Events"
        keystroke "{escaped}"
    end tell
    '''
    
    try:
        subprocess.run(["osascript", "-e", script], check=True)
        return True
    except subprocess.CalledProcessError:
        # Fallback: copy to clipboard
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        subprocess.run(["osascript", "-e", 
            'tell application "System Events" to keystroke "v" using command down'
        ], check=True)
        return False
```

---

## 11. Next Steps

1. **Create the repo** with the file structure from Section 3.3
2. **Drop all docs** (outline + 4 reviews + this final doc) into `docs/`
3. **Create config stubs** (`settings.yaml`, `vocab.yaml`, `replacements.yaml`)
4. **Execute Day 1 build plan** (Section 6)
5. **After Day 1:** Use it daily, grow `vocab.yaml` and `replacements.yaml` from real errors
6. **Phase 3:** Add correction hotkey and feedback loop

---

## 12. Final Notes

This project has been reviewed four times by three different AI systems. The consensus is clear:

- The architecture is sound
- The hardware is more than capable
- The scope is appropriately constrained
- The personalization strategy (`initial_prompt` + regex) is the right v1 approach

The most valuable "review" from here on is **your lived experience using v1 every day**. The system will improve as you feed it corrections and grow the vocabulary files.

Time to write some code.

---

*End of Final Project Document*
