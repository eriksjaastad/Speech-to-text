# Erik STT Project — Review #3 (Integrated Design Review)

**Reviewer:** ChatGPT  
**Date:** December 2025  
**Scope:** Integrated review combining the project outline, Review #1, Review #2, and the follow‑up Q&A decisions.

---

## 1. Context & Current State

At this point you have:

- A clear, well‑scoped **project outline** that frames this as a single‑user, English‑only, Mac‑only STT system optimized for Erik’s voice and workflows, with local/offline capability and a focus on predictable, non‑creative dictation.  
- Two detailed **technical reviews** that converge on a Python + `faster-whisper` architecture with macOS integration, personal vocabulary via `initial_prompt`, and rule‑based post‑processing.  
- A **Q&A decisions file** that locks in key choices: hardware baseline (M4 Pro, 24GB RAM), acceptable latency (2–3 seconds), no Transform/Mode C in v1, local‑only logs with finite retention, and a willingness to reorder phases so learned corrections come before cloud fallback.

Together, these documents move the project from “idea” to a fairly mature technical plan. Review #3’s job is to **synthesize**, resolve remaining tensions, and give you a concrete, opinionated roadmap you can code against.

---

## 2. What’s Solid and Doesn’t Need More Debating

These decisions are strong and should be treated as **locked in for v1** unless reality proves otherwise:

### 2.1 Problem & Scope

- **Single user, single language, one platform.** You’re not building a product; you’re building a personal instrument. That’s the right constraint and should keep complexity in check.
- **Goal is “better than Superwhisper for Erik,” not “state‑of‑the‑art for everyone.”** This focuses all decisions on *your* error patterns, *your* vocabulary, and *your* workflows.

### 2.2 Core Architecture

- **Engine:** `faster-whisper` (or equivalent CTranslate2‑backed Whisper) as the local STT engine.
- **Runtime:** Python for the core logic, with a thin macOS integration layer (menu bar, hotkeys, AppleScript text insertion).
- **Personalization:**
  - Primary: `initial_prompt` injection based on a custom vocab file.
  - Secondary: rule‑based replacement map (`replacements.yaml`) for recurring mis‑hearings.
- **Modes in v1:**
  - **Mode A – Raw / Safe Dictation:** Faithful transcription with only mechanical, deterministic fixes.
  - **Mode B – Light Cleanup:** Slightly more polished output while still avoiding meaning changes.
  - **Mode C – Transform:** **Explicitly out of scope for v1.**

### 2.3 Hardware & Performance Targets

- Hardware: MacBook Pro with **M4 Pro + 24GB RAM** — plenty for `distil-large-v3` or `large-v3` Whisper models.
- Latency tolerance: **2–3 seconds** for a typical dictation burst is acceptable.
- This means you should **aim high on model size**: start with `distil-large-v3` for v1; drop down only if latency feels bad.

---

## 3. Updated Design Decisions (Incorporating All Inputs)

### 3.1 Model & Audio Defaults

**Model choice for v1:**

- **Primary:** `distil-large-v3` (or equivalent distilled large English model).
- **Fallback:** `medium.en` if something about the distilled model misbehaves, but given your hardware, large‑class models are realistic.

**Audio capture defaults:**

- Sample rate: **16,000 Hz** (mono)
- Channels: **1** (mono)
- Data type: `float32`

Capturing at 16kHz mono natively avoids extra resampling cost and keeps the pipeline simple.

### 3.2 Modes & Post‑Processing Strategy (v1)

The earlier reviews floated LLM‑based cleanup for Mode B. Given your constraints and the “local‑first, simple‑first” philosophy, Review #3 recommends:

- **Mode A – Raw / Safe Dictation**
  - Whisper with:
    - `temperature = 0.0`
    - `beam_size = 5` (tuneable)
    - `condition_on_previous_text = false` by default
  - Post‑processing:
    - Trim whitespace
    - Apply `replacements.yaml` (deterministic regex/text replace)
  - No LLM, no grammar magic.

- **Mode B – Light Cleanup (Deterministic Only for v1)**
  - Start from Mode A output.
  - Add **rule‑based** cleanup only, e.g.:
    - Normalize spacing after punctuation.
    - Capitalize sentence starts (regex on `.?!` + space).
    - Optional: lightweight punctuation insertion using a small, deterministic model/lib rather than a general LLM.
  - Avoid full LLM cleanup in v1; keep behavior predictable and debuggable.

You can revisit LLM‑based cleanup later as a **Phase 4+ experiment**, once the core tool feels solid.

### 3.3 Configurability: Context Conditioning

Review #2 correctly pointed out the trade‑off of `condition_on_previous_text`. For your use:

- Default: **`condition_on_previous_text = false`** (avoids “YouTube hallucination” type outputs for short snippets).
- Config option in `settings.yaml` to enable it for longer dictation sessions once you’ve tested the behavior in practice.

This keeps v1 safe while leaving the door open.

---

## 4. Refined Roadmap (Reordered Phases)

Taking into account your Q&A preferences (no Transform mode, learned corrections before cloud, finite log lifetime), here’s an updated, **opinionated** roadmap.

### Phase 0 — Repo & Skeleton (You’re basically here)

- Create repo with structure:

  ```text
  erik-stt/
  ├── config/
  │   ├── settings.yaml
  │   ├── vocab.yaml
  │   └── replacements.yaml
  ├── src/
  │   ├── audio_capture.py
  │   ├── engine.py
  │   ├── post_process.py
  │   ├── injection.py        # AppleScript/clipboard logic
  │   └── menubar_app.py
  ├── logs/
  └── docs/
      └── PROJECT_OVERVIEW.md
  ```

- Commit the existing project outline and reviews into `docs/` so they travel with the code.

### Phase 1 — CLI Prototype (Raw Path End‑to‑End)

Success criteria for Phase 1:

- Record audio from the default mic via CLI.
- Transcribe with `faster-whisper` using a hardcoded `vocab` list for `initial_prompt`.
- Apply a simple `replacements.yaml` for 1–3 known mis‑hearings.
- Log each run to JSONL with:
  - timestamp
  - engine config
  - raw transcript
  - post‑processed text

This proves: mic → Whisper → personalization → logging all work on your actual Mac.

### Phase 2 — macOS Menubar & Hotkey Integration

Key tasks:

- Add `rumps` menubar app:
  - Show idle/recording/transcribing status.
  - Expose a simple drop‑down to select Mode A vs Mode B.
- Implement global hotkey (e.g., `⌘⌥D`) using `pynput` or an alternative if permissions are ugly.
- Handle macOS permissions explicitly:
  - Start‑up check for microphone + Accessibility permissions.
  - If missing, show a clear instruction dialog with screenshots/text.
- Implement text injection via AppleScript, with clipboard+paste fallback if the primary method fails.

Success criteria:

- From any app, pressing the hotkey lets you dictate a short sentence and see it appear at the cursor in under ~3 seconds for a “normal” utterance.
- When permissions are missing or something fails, you get a **clear signal**, not silent failure.

### Phase 3 — Personal Vocab & Manual Correction Loop

Now that the core UX works, Phase 3 is about making it **“Erik’s STT”** instead of “just Whisper with a hotkey.”

Components:

1. **`vocab.yaml` + `replacements.yaml` wired in for real:**
   - Build an initial vocab file with your trading, coding, van‑life, and tool terms.
   - Implement a small helper script or UI to add new words as you notice errors.

2. **Correction feedback hotkey:**
   - Maintain “last transcript” in memory.
   - Secondary hotkey (e.g., `⌘⌥Z`) opens a small window where you can correct the text.
   - Save both `raw_transcript` and `corrected_text` into the logs.

3. **Log retention:**
   - Keep JSONL logs **local‑only** under `~/Documents/erik-stt/logs/`.
   - Implement a simple monthly rotation & retention policy:
     - e.g., “keep 90 days; older logs get archived or deleted.”

This phase is where you start building the **training corpus for future learned correction** while also improving the rule‑based mapping.

### Phase 4 — Learned Personal Correction (Before Cloud)

With enough corrected pairs, you can experiment with a small text‑level corrector:

- Start very simple:
  - Scripts that scan logs, count frequent `raw → corrected` pairs, and suggest new entries for `replacements.yaml`.
- Only if needed, explore a small sequence‑to‑sequence model or other lightweight ML to propose corrections.
- Keep this as an **optional post‑processing step** for Mode B only.

Only after this feels “maxed out” does it make sense to consider cloud STT as a **Phase 5 / optional** add‑on for niche cases.

---

## 5. Risk Review & Mitigations (Updated)

### 5.1 macOS Security & Permissions

**Risk:** App works one day and mysteriously breaks the next due to revoked permissions or OS updates.

**Mitigations:**

- Centralized “health check” at startup that verifies:
  - Mic access
  - Accessibility access (for hotkeys and injection)
- If something is missing:
  - Show a small, clear window with instructions and a “Re‑check” button.
- Document a “First Run Setup” sequence in `docs/` so you can redo it after OS upgrades.

### 5.2 Latency and Model Size Mis‑match

**Risk:** Large model feels too slow in real, messy usage.

**Mitigations:**

- Make model choice a config, not code change.
- Instrument basic timing (per dictation):
  - Capture audio duration + inference time + total latency.
- If average latency climbs above your 2–3s comfort band for typical snippets, step down to a smaller model.

### 5.3 Over‑Clever Mode B

**Risk:** Even without an LLM, a “cleanup” layer can still unintentionally change meaning.

**Mitigations:**

- Build Mode B as a composition of small, auditable steps:
  - `normalize_spacing()`, `capitalize_sentences()`, `apply_replacements()`
- Add a config flag to **disable Mode B entirely** if it ever annoys you.
- Consider visual cues (e.g., prefixing first run of Mode B with a special symbol in logs) so you can spot problematic outputs.

### 5.4 Log Bloat & Privacy

**Risk:** Logs grow unbounded or store more of your speech history than you’re comfortable with.

**Mitigations:**

- Implement retention in code (e.g., simple script that deletes logs older than N days on startup).
- Keep logs under a clearly marked folder so you can manually nuke them anytime.
- Avoid logging **app context** or other metadata unless you discover that you really need it later.

---

## 6. Concrete Recommendations & Next Actions

If you want a crisp “do this next” list, here it is:

1. **Create the repo** with the structure above and drop all four key docs (outline + 2 reviews + Q&A) into `docs/`.
2. **Add `settings.yaml`, `vocab.yaml`, and `replacements.yaml` stubs** under `config/` with the key fields already named.
3. **Implement Phase 1 CLI prototype**:
   - Use `faster-whisper` with `distil-large-v3`.
   - Hardcode a small vocab list and a couple of replacements.
   - Make sure you can consistently get under ~3 seconds for a short utterance.
4. **Once Phase 1 feels good, immediately move to Phase 2** for hotkey + menubar integration — this is where it becomes a real daily driver.
5. **After a week or two of real use**, start Phase 3:
   - Add the correction hotkey.
   - Begin building `vocab.yaml` and `replacements.yaml` from actual mistakes.

At that point, you’ll have something that is already better than Superwhisper **for you**, and the rest of the work is iterative refinement rather than foundational design.

---

## 7. Summary

Review #1 gave you the **engine and glue**.  
Review #2 sharpened the **risks, configs, and phase boundaries**.  
Your Q&A decisions removed ambiguity about **hardware, latency, modes, and logs**.

Review #3’s role is to **freeze a v1 architecture and roadmap** so you can stop re‑deciding and start building. With your Mac’s horsepower and your tolerance for a 2–3 second “thinking pause,” a high‑accuracy, highly personalized, offline‑capable STT tool is absolutely within reach.

From here on out, the most valuable “review” will be your own lived experience using v1 every day—and adjusting the system around the ways *you* actually speak.
