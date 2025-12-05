# The Muscle Car Roadmap — GPT 5.1 Codex Max Review
Date: 2025-12-05

## Verdict
Ambitious and well-sequenced (fix first, then speed), but high risk of overreach without guardrails. The Swift/WhisperKit stages are credible yet optional; P0 bug fixes must be enforced with explicit wiring and test gates before any bridge work.

## Strengths
- Correctly insists on fixing focus restoration, VAD, and pre-roll before performance work.
- Clear staging (1→4) with success criteria and timing targets; keeps Python UX/customization intact while adding a Swift “blower.”
- Provides concrete Swift CLI plan (Package.swift, CLI args, JSON output) and a Python bridge with fallback to faster-whisper.
- Sets measurable performance targets (<0.5s transcription, <1s total) and success checks for focus/first-word capture.

## Critical Issues / Gaps
1) Wiring still implied, not mandated: Must require capture/restore of target app in `start_recording` → `process_audio` → `inject_text(restore_app=…)`; failure to wire keeps the “unwired fix” alive. Add this as a hard gate in Stage 1 acceptance.
2) Tests undefined for focus and first-word: Success criteria are listed, but no minimal test script/log schema is specified. Risk: “pass” becomes subjective.
3) Timing values hardcoded: Recommends 0.2–0.25s but lacks config-driven tuning per target app (Electron vs Cocoa). Needs config keys and default + override guidance.
4) Swift bridge failure modes: No rollback plan if WhisperKit binary is missing, slow to initialize, or crashes. Needs explicit timeout, error mapping, and automatic fallback to faster-whisper without user interruption.
5) Custom vocab gap in Swift path: Bridge notes vocab handled via post-process, but no test to ensure parity (e.g., jargon terms preserved) when using WhisperKit output.
6) Pre-roll sizing & deque: Specifies deque but not sample/frame assumptions; needs explicit chunk size and target pre-roll duration (ms) so QA can validate.
7) Scope creep risk: Stage 2–3 could eclipse core bug fixes; must freeze P0/P1 before touching Swift/MLX.

## What to Tighten (actionable doc edits, no code)
- Stage 1 acceptance gates (must-have logs/tests):
  - Log schema (JSONL): `t_start`, `target_app_captured`, `t_hide_bubble`, `t_focus_restore`, `t_paste`, `inject_success`, `text_len`.
  - Test cases required to pass: (a) “one two three” hot-start 5/5 first-word captured; (b) VS Code and Notes focus restore 5/5; (c) silence/VAD test: silence yields no injection + warning.
- Wiring requirement: Explicitly state that Stage 1 is incomplete unless `restore_app` is passed through the call chain and invoked immediately before paste; document the exact call sites.
- Config knobs: Add `focus_settle_ms` and `clipboard_settle_ms` defaults (e.g., 250ms) with per-app overrides; add `pre_roll_ms` target and chunk assumptions (e.g., 1024 frames @16kHz ≈64ms).
- Fallback/timeout for Swift CLI: Define a max startup/transcribe time; on timeout/error, auto-fallback to faster-whisper and log the failure.
- Vocab parity test: Require a jargon test phrase through both engines to verify post-process preserves custom terms.
- Freeze rule: No Stage 2/3 work starts until Stage 1 gates pass and are documented.

## Priority Order (recommended)
- P0: Wire focus capture/restore, enable VAD, swap pre-roll to deque with defined duration, add timing knobs, add minimal logging + tests.
- P1: Harden injection timing (configurable), add retry/backoff, define fallback behavior on focus-restore failure.
- P2: Swift/WhisperKit bridge behind a flag with timeout and auto-fallback; confirm vocab parity.
- P3: Nice-to-haves (sounds, animations) only after reliability + bridge stability.

## Risks to track
- Focus restore still not wired in code paths → bug persists.
- Electron timing variance → under-delays yield missed paste; over-delays hurt perceived latency.
- WhisperKit availability/permissions/build breaks → user stuck if fallback isn’t automatic.
- Jargon loss in Swift path → regressions masked by speed gains.

