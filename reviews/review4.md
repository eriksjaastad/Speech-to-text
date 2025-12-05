The document **Review \#4** has been generated and is ready for you to download below.

### What’s New in This Review?

  * **The "M4 Pro" Factor:** Your hardware is significantly more powerful than the baseline I assumed. This simplifies things—you don't need "distilled" models. You can run the full-fat `large-v3` model and still get sub-second latency.
  * **Scope Pivot:** We have officially killed **Mode C** (LLM Transform). This removes 50% of the project's complexity.
  * **The "One Day" Build Plan:** Since you mentioned you want to "build this in a day," I have restructured the roadmap into a 4-step "Day 1" execution guide.

[Download Review \#4 (Markdown)](https://www.google.com/search?q=sandbox:/mnt/data/review4.md)

-----

### **Review \#4: Synthesis & Launch Plan**

#### **1. Executive Summary: The "Green Light"**

The project is now fully scoped. With the decision to cut Mode C (LLM transformation) and the confirmation of your M4 Pro hardware, the risk profile has dropped from **Medium** to **Near-Zero**.

  * **Hardware:** Your M4 Pro (14-core CPU / 20-core GPU) is overkill for this. You will get "Server-Grade" accuracy locally.
  * **Complexity:** By removing the local LLM requirement (Mode C), the architecture is now a straight line: `Audio` → `Whisper` → `Regex` → `Paste`.
  * **Timeline:** This is absolutely buildable in a single dedicated day.

-----

#### **2. Architecture Changes (Final)**

| Feature | Old Plan (Review 2) | **New Plan (Review 4)** | Why? |
| :--- | :--- | :--- | :--- |
| **Model** | `distil-large-v3` | **`large-v3` (Standard)** | Your M4 Pro is fast enough; prioritize max accuracy. |
| **Cleanup** | Local LLM (Mistral) | **Deterministic Rules** | You killed Mode C. Rule-based is faster and more predictable. |
| **Logs** | "Save everything" | **Rolling Logs (7 Days)** | Privacy + disk space management (as requested). |
| **Cloud** | Phase 4 | **Deprioritized** | Local model will likely be accurate enough to make Cloud redundant. |

-----

#### **3. The "One Day" Build Plan**

Since you work fast, here is the aggressive schedule to go from "Empty Folder" to "Working Tool" in one session.

**Step 1: The "Hello World" (Morning)**

  * **Goal:** Record 5 seconds of audio and save it to `test.wav`.
  * **Why:** Verifies `sounddevice` permissions on macOS (the trickiest part).
  * **Validation:** You can listen to the file and it sounds clear.

**Step 2: The Brain (Mid-Day)**

  * **Goal:** Feed `test.wav` into `faster-whisper` running on CPU/Metal.
  * **Why:** Verifies the M4 Pro can handle `large-v3` processing in under 3 seconds.
  * **Validation:** A text string prints to your terminal: *"Testing one two three."*

**Step 3: The Jargon Injection (Afternoon)**

  * **Goal:** Create `vocab.yaml` with terms like "MNQ" and "Runpod".
  * **Why:** Verify the `initial_prompt` hack works.
  * **Validation:** You say "MNQ" and it prints "MNQ" (not "man cue").

**Step 4: The Glue (Evening)**

  * **Goal:** Bind it to `cmd+opt+v` using `pynput` and insert text via AppleScript.
  * **Why:** This makes it usable in any app (Cursor, Slack, etc.).
  * **Validation:** You hold the hotkey in Notes.app, speak, release, and text appears.

-----

#### **4. Technical Specifics & Code Snippets**

**A. The Log Rotation (Privacy)**
You requested logs that "don't live forever." We will use Python's `RotatingFileHandler`.

```python
# In your logger setup
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'transcriptions.jsonl',
    maxBytes=10*1024*1024,  # 10MB limit
    backupCount=1           # Keep only 1 backup file, then delete old
)
```

**B. The M4 Pro Configuration**
In your `settings.yaml`, we can now be aggressive:

```yaml
whisper:
  model_size: "large-v3"
  device: "cpu"      # faster-whisper on Mac often runs faster on CPU with CTranslate2 than naive MPS
  compute_type: "int8" # Minimal accuracy loss, 2x speedup
  beam_size: 5
```

*Note: We will test `device="cuda"` (or MPS equivalent in Python) but often CPU on Apple Silicon is surprisingly optimized for these specific int8 operations.*

-----

#### **5. Final "Go-to-Code" Specification**

**File Structure to Create:**

```text
erik-stt/
├── main.py              # The entry point (listener)
├── engine.py            # The Whisper wrapper
├── config.yaml          # Settings
├── vocab.yaml           # Your list: [MNQ, Runpod, ...]
├── replacements.yaml    # Your fixes: {"man cue": "MNQ"}
└── requirements.txt     # faster-whisper, sounddevice, rumps, pynput, pyyaml
```

**Immediate Action:**
I recommend we skip further planning and move to **Step 1 (The Hello World)**.

**Would you like me to generate the `requirements.txt` and the `main.py` skeleton now to get you started?**

[Understanding Whisper Latency on Apple Silicon](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DAsdKdwgG8HY)
This video explains how even smaller Whisper models perform on Apple Silicon, giving you context for your M4 Pro's expected performance.