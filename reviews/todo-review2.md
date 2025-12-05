Let me see the truncated portion to give you a complete review.Got it. Here's my final review:

---

## BUILD_TODO.md — Final Review

**Verdict:** This is ready to execute. Well-structured, incrementally testable, and follows the architecture we agreed on.

### What's Good

1. **Step 0 addition** — Smart move. Setting up the project structure and venv *before* Day 1 means you're not debugging pip issues when you want to be writing code.

2. **scipy added to requirements** — Good catch. `scipy.io.wavfile.write` is cleaner than rolling your own WAV writer.

3. **"DONE when" checklists** — These are excellent. Every step has concrete, testable success criteria. No ambiguity about when to move on.

4. **Incremental testing philosophy** — Each step builds on the previous and is independently testable. If Step 2 breaks, you know the problem is Whisper, not audio capture.

5. **Hotkey progression** — Using Spacebar for Day 1 testing, then upgrading to Option+Space later is pragmatic. Modifier key detection with `pynput` can be finicky; better to prove the core flow first.

6. **Code is complete** — Not pseudocode. You can literally copy-paste these snippets and run them. That's the right level of detail for a build doc.

### Minor Issues to Be Aware Of

**1. AppleScript keystroke escaping (Step 5)**

The current escape logic handles `\` and `"`, but will break on newlines. If you ever dictate something with line breaks:

```python
# Current (will fail on newlines)
escaped = text.replace('\\', '\\\\').replace('"', '\\"')

# Safer version
escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
```

Not urgent for v1 (you'll mostly dictate single sentences), but worth noting.

**2. Temp file cleanup on crash (Step 6)**

The `process_audio()` method uses a `try/finally` to clean up the temp file, which is good. But if the app crashes mid-recording (before `process_audio` is called), you could accumulate orphan temp files. Low priority, but a future cleanup script could help.

**3. Model download timing (Step 2)**

First run downloads ~3GB. The doc mentions this in the Notes section, but consider adding a dedicated "Step 1.5: Download Model" that does *only* the download so you're not waiting during the actual test:

```python
# pre_download_model.py
from faster_whisper import WhisperModel
print("Downloading large-v3... this may take a few minutes.")
model = WhisperModel("large-v3", device="cpu", compute_type="int8")
print("Done!")
```

**4. Post-Day-1 section ordering**

Steps 7–10 are labeled but Step numbers restart awkwardly (Step 7 after Step 6 is fine, but the "Future Phases" section uses different numbering). Minor formatting thing — doesn't affect execution.

### Questions Section — My Input

You asked:

> **Error handling:** How verbose do you want error messages?

**Recommendation:** Terminal logs for Day 1, then add popup dialogs only for permission errors once you have the menubar app (Step 8). You don't want dialogs interrupting your flow for recoverable errors.

> **Test phrases / Success threshold**

For test phrases, I'd suggest:
- "I'm looking at MNQ and ES futures on TradeZella"
- "Spin up a Runpod instance with Ollama"
- "Check the Victron battery in Cochise County"

For success threshold: If 9 out of 10 of your jargon terms are recognized correctly on first try (before adding to `replacements.yaml`), that's a win. The whole point is that corrections compound over time.

### Final Verdict

**Ship it.** This doc is ready to guide a Day 1 build. The structure is sound, the code is functional, and the testing criteria are clear.

Start with Step 0. Say "done" when you're ready for questions or hit a snag.