Here’s your “one more final review” 😊 — focused on the **BUILD_TODO.md implementation plan** and how well it lines up with the earlier architecture + reviews. 

I’ll keep it tight and opinionated so you can either ship it as-is or make 2–3 tweaks and be done.

---

## 1. Big Picture: Is this TODO good enough to build from?

**Short answer: yes.**

This TODO:

* Walks you cleanly from **empty repo → end-to-end working hotkey STT tool in one day**.
* Has **clear DONE criteria** for every step (audio OK, model fast enough, terms recognized, text injected, etc.).
* Embeds **specific code snippets** that are realistic for your stack and hardware.
* Matches the v1 architecture we settled on: `faster-whisper` + vocab injection, rule-based post-processing, AppleScript injection, hotkey glue.

You could absolutely just follow this and get a solid v1.

The rest of this review is “polish + landmines”: small changes that will save you pain later.

---

## 2. Places Where This Shines

These parts are especially strong and don’t need more design work:

* **Step-wise structure (0–6):** Each step is testable in isolation and progressively builds toward full app behavior. 
* **Explicit macOS quirks:** mic permissions, Accessibility, AppleScript injection, clipboard fallback are all acknowledged and tested directly. 
* **Personalization flow:** `vocab.yaml` + `initial_prompt` + `replacements.yaml` is wired in early (Step 3–4), not bolted on at the end. 
* **Modes A/B as functions:** `process_mode_a` and `process_mode_b` are clean, deterministic functions instead of opaque magic. 
* **Future phases parked correctly:** correction loop, learned corrections, possible cloud fallback are clearly “later” and won’t derail v1. 

From a project-management point of view, this doc is *already* a solid “build script” for your day.

---

## 3. Small but Important Issues to Fix

### 3.1 Import Paths / Package Layout

Right now, some snippets assume you can do:

```python
# src/main.py
from engine import WhisperEngine, load_vocab
from post_process import load_replacements, process_mode_a, process_mode_b
from injection import inject_text_applescript
```

That only works if:

* Your working directory is `src/` **and**
* Python can see `src` as the root.

To avoid annoying “ModuleNotFoundError”s:

* Add an `__init__.py` inside `src/`, **and**
* Standardize imports to be package-style when run from project root, e.g.:

```python
# src/main.py
from src.engine import WhisperEngine, load_vocab
from src.post_process import load_replacements, process_mode_a, process_mode_b
from src.injection import inject_text_applescript
```

And in your test scripts at the repo root, do the same (`from src.audio_capture import ...`). This is the #1 thing that will randomly bite you when you’re tired.

---

### 3.2 Model Choice Consistency

The TODO currently uses **`large-v3`** everywhere: in `WhisperEngine(model_size="large-v3")` and in `settings.yaml`. 

Earlier we’d leaned toward **`distil-large-v3` as a nice balance** for your M4 Pro. Either choice is fine for your hardware, but *pick one* and make it **config-only**:

* In code, default to something like:

  ```python
  def __init__(self, config):
      model_size = config["whisper"]["model"]
      ...
  ```

* Then let `config/settings.yaml` be the single source of truth:

  ```yaml
  whisper:
    model: "large-v3"    # OR "distil-large-v3" — but pick one
  ```

That keeps you from having to hunt down multiple hardcoded model strings later.

---

### 3.3 Hotkey Behavior (Space vs Option+Space)

Step 6 uses **Space alone** for recording (good for initial testing), while later you define **Option+Space** as the production hotkey in `settings.yaml`. 

Two tweaks I’d suggest:

1. **Document the transition explicitly in Step 6 or Step 7:**

   * “For Day 1, use SPACE-only for simplicity. After everything works, switch to Option+Space as configured in settings.”

2. When you implement `settings.yaml` in Step 7, bite the bullet and actually parse the hotkey string (`"option+space"`) into modifier+key. If that’s too annoying day one, at least force everything through a single `HotkeyConfig` helper so you don’t hard-wire spacebar in multiple places.

Not fixing this doesn’t break v1, but it will feel janky if you forget and keep using space forever.

---

### 3.4 Two Audio Paths (Capture vs Main)

You currently have:

* `src/audio_capture.py` with a nice standalone `record_audio()` / `save_audio()` for tests. 
* Duplicated-but-slightly-different recording logic directly inside `ErikSTT.start_recording()` in `main.py`. 

This is fine for a hack day, but:

* Future-you will eventually want **one canonical audio module** (for input device selection, debugging, etc.).
* A simple improvement: let `main.py` call functions from `audio_capture.py` (or move shared logic into a new `src/audio.py`) instead of re-implementing the callback pattern.

I wouldn’t block v1 on this, but I’d at least mentally note: “Audio duplication is technical debt to clean up in v1.1.”

---

### 3.5 AppleScript Injection Edge Cases

The `inject_text_applescript` helper is good enough to get you going, but a couple edge cases to be aware of: 

* Very long strings + quotation marks + newlines can make the AppleScript fail due to quoting.
* Some apps handle keystroke injection slower than others, so you might see dropped characters with very big paste chunks.

For v1, this is fine. Just:

* Keep your v1 dictation segments *shortish* (which fits your 2–3s latency target anyway).
* If you start seeing weirdness, fall back to clipboard-based paste for **all** text (it’s slower but more robust).

---

### 3.6 YAML & Missing Config Files

The TODO assumes `vocab.yaml`, `replacements.yaml`, and `settings.yaml` always exist and are valid YAML. 

I’d strongly recommend:

* In each loader (`load_vocab`, `load_replacements`, `load_settings`), wrap in try/except and fall back to **empty defaults with a console warning**, not a crash.

This keeps “first run” smooth even if a file is missing/empty or you typo a key in YAML at 1:00 a.m.

---

## 4. “Top 3 Changes” If You Only Touch a Little

If you don’t want to fuss, I’d do *just these* before coding:

1. **Fix imports & package layout**

   * Add `__init__.py` to `src/`
   * Use `from src.engine import ...` everywhere you import app modules.

2. **Make model & mode config-only**

   * No hardcoded `"large-v3"` or `"raw"` in the Python files — read from `settings.yaml`.

3. **Add defensive config loading**

   * `load_vocab`, `load_replacements`, `load_settings` should all gracefully handle missing/empty files and just log a message.

Do those three, and the rest of the TODO is more than good enough to start building.

---

## 5. Bottom Line

* As a **build script for v1**, this TODO is solid. You can follow it and get a working Erik-only STT tool that’s already better than Superwhisper for your use.
* The remaining issues are implementation details, not design flaws: imports, config robustness, and long-term code organization.

If you want, next step I can **edit this TODO into a “rev B”** version (or make a `BUILD_TODO_v2.md`) with the 2–3 changes baked in so you don’t have to keep mental notes.
