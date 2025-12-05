# Erik STT Project — Review #2

**Reviewer:** Claude  
**Date:** December 2025  
**Scope:** Comprehensive analysis synthesizing the project outline and Review #1

---

## Executive Summary

This project has a solid foundation. The original outline correctly identifies the core problem (generic STT tools optimize for breadth, not depth), and Review #1 provides excellent technical scaffolding with the `faster-whisper` + Python stack recommendation. 

This second review focuses on:
1. Validating and extending the technical recommendations
2. Identifying implementation risks not yet addressed
3. Suggesting refinements to the phased approach
4. Highlighting decision points that need resolution before coding begins

**Bottom line:** This is buildable in a reasonable timeframe. The `initial_prompt` injection strategy from Review #1 is the right approach for personalization without model fine-tuning.

---

## Part 1: What's Working Well

### 1.1 Problem Definition

The outline nails the core frustration: commercial STT tools like Superwhisper try to be "smart" for everyone, which makes them unpredictable for power users with niche vocabulary. The explicit decision to build a **single-user, single-language** tool is the right constraint—it dramatically simplifies the problem space.

### 1.2 Mode Separation

The three-mode design (Raw → Light Cleanup → Transform) is well-conceived:

| Mode | Purpose | Risk Level |
|------|---------|------------|
| **A (Raw)** | Faithful transcription | Low — mechanical fixes only |
| **B (Light Cleanup)** | Readable but unchanged meaning | Medium — requires careful guardrails |
| **C (Transform)** | Intentional restructuring | High — but user-initiated, so acceptable |

This separation prevents the "surprise rewrite" problem that plagues tools trying to be too helpful.

### 1.3 Technical Stack (from Review #1)

Review #1's recommendations are sound:

- **`faster-whisper`** — Correct choice. CTranslate2 backend gives 4-6x speedup over vanilla Whisper.
- **`rumps`** for menubar — Lightweight, Python-native, good fit for this scope.
- **`pynput`** for hotkeys — Works, though has some macOS permission quirks (see Risks below).
- **AppleScript for text injection** — Safer than `pyautogui` keystroke simulation.

### 1.4 The `initial_prompt` Strategy

This is the most important insight from Review #1. Whisper's `initial_prompt` parameter biases the model's token predictions toward words it has "seen" recently. Injecting your custom vocabulary here is:

- **Low-effort** (no model training required)
- **Immediately effective** (works on first use)
- **Dynamically updatable** (just edit a YAML file)

This should be the **primary personalization mechanism** in v1.

---

## Part 2: Gaps and Risks

### 2.1 macOS Permissions — The Silent Killer

Neither document adequately addresses the **Accessibility and Input Monitoring permissions** required on modern macOS. This is not a minor detail—it's a common source of "it works on my machine but not after reboot" bugs.

**What's needed:**
- **Accessibility permission** — Required for `pynput` to capture global hotkeys
- **Microphone permission** — Required for `sounddevice` audio capture
- **Input Monitoring** — May be required depending on how hotkeys are implemented

**Recommendation:** Phase 2 should include explicit documentation for:
1. How to grant permissions via System Settings → Privacy & Security
2. A startup check that verifies permissions and shows a helpful error if missing
3. Code signing considerations (unsigned apps get extra permission friction)

### 2.2 Audio Format and Sample Rate

The outline mentions `sounddevice` + `numpy` but doesn't specify audio parameters. Whisper expects:
- **16kHz sample rate** (will resample if different, but adds latency)
- **Mono audio**
- **16-bit PCM or float32**

**Recommendation:** Capture at 16kHz mono natively to avoid resampling overhead. Add this to `settings.yaml`:

```yaml
audio:
  sample_rate: 16000
  channels: 1
  dtype: float32
```

### 2.3 Mode B's "Light Cleanup" Is Harder Than It Looks

Review #1 suggests using a local LLM (Phi-3, Mistral-7B via Ollama) for Mode B cleanup. This introduces several concerns:

1. **Latency** — Even small LLMs add 500ms–2s of processing time
2. **Reliability** — LLMs sometimes "help" too much despite instructions
3. **Dependency bloat** — Now you're running Whisper *and* Ollama

**Alternative approach for v1:**
Skip the LLM for Mode B. Instead, use deterministic rules:
- Capitalize sentence starts (regex: after `.!?` followed by space)
- Basic punctuation via a lightweight library like `punctuator` or `deepmultilingualpunctuation`
- Save LLM-based cleanup for v2 after you have real usage data

### 2.4 The `condition_on_previous_text` Trade-off

Review #1 recommends `condition_on_previous_text=False` to prevent hallucinations. This is good advice for **short, isolated dictations**, but has a downside: if you dictate in multiple chunks within the same "thought," the model loses context between chunks.

**Recommendation:** Make this configurable:
```yaml
whisper:
  condition_on_previous_text: false  # Default: safe
  # Set to true for long-form dictation sessions
```

### 2.5 Log Privacy and Storage Growth

The logging design (JSONL with raw + final text) is good for training but will accumulate quickly. At ~500 bytes per entry and 50 dictations/day, you're looking at:
- **~750KB/month**
- **~9MB/year**

Not huge, but worth having:
1. A log rotation strategy (archive monthly?)
2. A "purge old logs" script
3. Clear documentation that logs contain your raw speech

---

## Part 3: Refined Phase Recommendations

### Phase 0 → Phase 1 Bridge (Add This)

Before writing code, resolve these decisions:

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Whisper model | `medium.en`, `large-v3`, `distil-large-v3` | Start with `distil-large-v3` (speed + accuracy) |
| Hotkey activation | Hold-to-record vs Toggle | Hold-to-record (more predictable) |
| Text injection method | AppleScript vs Clipboard+Paste | AppleScript (cleaner), clipboard as fallback |
| Mode B implementation | LLM vs Rules-only | Rules-only for v1 |

### Phase 1 Refinement

Review #1's prototype suggestion is good. Add these acceptance criteria:

**Phase 1 is complete when:**
- [ ] CLI records audio while spacebar is held
- [ ] Transcription completes in <3 seconds for a 10-second clip
- [ ] Custom vocabulary injection demonstrably improves "MNQ" recognition
- [ ] Output is logged to JSONL with timestamp and raw text

### Phase 2 Refinement

Add explicit permission handling:

**Phase 2 is complete when:**
- [ ] Menubar app launches at login (optional)
- [ ] Global hotkey works from any app
- [ ] App detects missing permissions and shows setup instructions
- [ ] Text appears at cursor in at least: Cursor, Notes, Safari

### New: Phase 2.5 — Correction Feedback Loop

Insert a phase between 2 and 3:

**Goal:** Make it trivial to correct mistakes and feed them back into the system.

**Implementation:**
- After text insertion, keep the last transcription in memory
- Secondary hotkey (e.g., `⌥⌘Z`) opens a small correction window
- User edits the text; both versions are logged
- Over time, this builds your `replacements.yaml` automatically

This is where the "learns from you" magic happens without requiring ML expertise.

---

## Part 4: Technical Recommendations

### 4.1 Suggested `requirements.txt`

```
faster-whisper>=0.10.0
sounddevice>=0.4.6
numpy>=1.24.0
rumps>=0.4.0
pynput>=1.7.6
PyYAML>=6.0
```

### 4.2 Configuration Schema

Consolidate Review #1's suggested configs into one `settings.yaml`:

```yaml
# settings.yaml
hotkeys:
  record: "cmd+alt+d"
  correct_last: "cmd+alt+z"

audio:
  sample_rate: 16000
  channels: 1
  device: null  # null = system default

whisper:
  model: "distil-large-v3"
  language: "en"
  beam_size: 5
  temperature: 0.0
  condition_on_previous_text: false

modes:
  default: "raw"  # raw | cleanup | transform

logging:
  enabled: true
  path: "~/Documents/erik-stt/logs/"
  retention_days: 90
```

### 4.3 Error Handling Philosophy

For a personal tool, fail loudly rather than silently:
- If Whisper model isn't loaded → Show notification, don't silently skip
- If audio capture fails → Beep + notification
- If text injection fails → Copy to clipboard as fallback, notify user

---

## Part 5: Open Questions for Erik

Before Phase 1 begins, consider:

1. **Hardware baseline** — What Mac are you building on? (M1/M2/M3? RAM?) This affects model size choices.

2. **Latency tolerance** — What's acceptable? <1s feels "instant," 2-3s feels "processing," >5s feels broken.

3. **Transform mode scope** — Is Mode C actually needed in v1? It adds significant complexity (LLM integration, prompt design). Consider deferring to v2.

4. **Cloud fallback priority** — Phase 4 (cloud engine) might be lower priority than Phase 5 (learned corrections) given your "local-first, van life" use case. Worth reordering?

5. **Backup/sync strategy** — Will logs live only on the Mac, or sync somewhere? Relevant for the "fine-tune on your voice" goal.

---

## Conclusion

This project is well-scoped and achievable. The combination of:
- `faster-whisper` for the engine
- `initial_prompt` injection for personalization
- Deterministic post-processing for Mode A/B
- JSONL logging for future learning

...gives you a solid v1 without over-engineering.

**Suggested immediate next steps:**

1. Create the repo with the file structure from Review #1
2. Resolve the "Open Questions" above
3. Build the Phase 1 CLI prototype (Review #1 offered to generate this)
4. Test with your actual vocabulary to validate the `initial_prompt` approach

The path from "document" to "working tool" is clear. Time to write some code.

---

*End of Review #2*
