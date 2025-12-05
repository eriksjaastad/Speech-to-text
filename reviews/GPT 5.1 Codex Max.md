# Bug Review — GPT 5.1 Codex Max
Date: 2025-12-05

## Scope
- Review of the two active bugs in `BUILD_TODO.md`: (1) Audio truncation / silence and (2) focus stealing / injection failure.
- Assessed current implementation in `src/main.py`, `src/injection.py`, and `src/ui/bubble.py`.

## Findings

1) Audio truncation / silence (“Ghost Recording”) — **partially mitigated, still risky for first/last syllables**
- A persistent `sounddevice.InputStream` is started at app init to remove stream spin-up delay, and stop adds a 0.5s tail buffer, which should help with mid-sentence capture.  
```
64:73:src/main.py
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=self.audio_callback
        )
        self.stream.start()
```
```
105:108:src/main.py
        # Wait a moment to capture the tail of the audio
        time.sleep(0.5)
```
- Gaps: no pre-roll/ring buffer before the hotkey is detected, so the very first word can still be clipped if speech starts at the same moment as the key combo. There is no silence/amplitude guardrail; a muted/permission-blocked stream would still produce a file and proceed to transcription, manifesting as “empty” results even though duration logs look fine.
- Recommendations:
  - Add a short circular buffer (e.g., 300–500ms) that is always filling while idle and prepend it when `start_recording()` flips on, to guarantee leading syllables.
  - Log and validate amplitude before transcribing (e.g., RMS/peak check with a user-facing warning if below threshold), and early-exit instead of sending silence to Whisper.
  - Surface `status` warnings from the callback to catch device/permission issues instead of suppressing them.

2) Focus stealing / injection failure (“Missing Paste”) — **still unresolved, high risk**
- The hotkey is currently Option+Space with no suppression; macOS Spotlight/Raycast will take focus when that combo fires, so the paste often targets Spotlight instead of the desired app.  
```
204:212:src/main.py
        if 'option' in self.pressed_keys and keyboard.Key.space in self.pressed_keys:
            if self.is_recording:
                self.stop_recording()
            else:
                self.start_recording()
```
- The injection path pastes into whichever app is frontmost at the moment of `osascript`, with only a best-effort log of the active app and no attempt to re-focus the previously active target.  
```
61:69:src/injection.py
    try:
        res = subprocess.run(["osascript", "-e", 'tell application "System Events" to name of first application process whose frontmost is true'], capture_output=True, text=True)
        print(f"👀 Active App for Injection: {res.stdout.strip()}")
    except:
        pass
```
- The bubble UI is configured as `NSPanel` + `NSWindowStyleMaskNonactivatingPanel` and ignores mouse events, so it likely isn’t the focus thief, but the menubar app calls `orderFront_` on the bubble during transcription; if Spotlight is also invoked, focus remains unpredictable.
- Recommendations:
  - Revert the default hotkey to the “safe” F13 (or another non-system combo) until Option+Space suppression is implemented; or require users to disable Spotlight/Raycast before enabling Option+Space.
  - Capture the frontmost app **before** starting transcription and explicitly reactivate it immediately before `Cmd+V`, so the paste cannot land on the bubble/Spotlight.
  - Add a retry/verification step: if the frontmost app changes between capture and inject, warn and retry once after reactivation.

## Testing gaps
- No automated checks for amplitude/silence; no regression test for “first word missing”.
- No integration test that asserts paste lands in the intended app with Option+Space enabled.

## Suggested next steps
- Implement the pre-roll buffer + amplitude guard, re-test the ghost-recording repro case.
- Ship a temporary “Safe Hotkey” mode (F13) in `settings.yaml`, default it on, and block Option+Space unless the user explicitly opts in and confirms Spotlight is remapped.
- Add “reactivate previous app” around `inject_text` to harden against focus loss; keep the active-app log for diagnostics.

