# Best-In-Class Roadmap — Review (GPT 5.1 Codex Max)
Date: 2025-12-05

## Verdict
Strong directional plan; most recommendations align with prior findings. Main gaps are prioritization, wiring details, and risk of scope creep (MLX/WhisperKit) before stabilizing core bugs.

## Strengths
- Correctly spotlights the top deficits: performance (latency), focus/injection reliability, and missing wiring for the “unwired fix.”
- Concrete, actionable items: VAD enablement, pre-roll deque, focus capture/restore, timing bumps, DI for testability.
- Useful benchmarking targets and migration options (MLX, WhisperKit) with expected latency improvements.

## Issues / Risks
1) Priority clarity: The doc mixes quick wins (VAD, deque, wiring focus) with high-effort migrations (MLX, WhisperKit) without a “do-first” ordering. Risk of chasing latency while the focus bug persists.
2) Wiring specifics: Focus restoration steps are right, but the doc doesn’t insist on passing `restore_app` through the actual call sites and ensuring capture occurs before any UI changes. Needs explicit call-flow sequencing.
3) Timing guidance: Suggests 0.25s sleeps but doesn’t anchor on Electron variability or recommend a configurable knob.
4) Logging/diagnostics: Recommends logging but omits a minimal required log schema for debugging the two critical bugs (target app captured, restored app, timestamps for hide/paste).
5) Dependency injection scope: Good idea, but unspecified boundary (engine/injector only? config loader?); could sprawl without a small initial target.
6) Performance plan: MLX/WhisperKit are called out, but there’s no fallback path if Metal/MLX isn’t stable, nor a “stop after VAD + chunk-size tuning” checkpoint.

## What to Clarify / Tighten
- Explicit priority stack (P0→P2):
  - P0: Wire focus capture/restore into `start_recording` → `process_audio` → `inject_text`; hide bubble before paste; bump delays via config knob; add logs for target/restored app.
  - P0: Switch pre-roll to deque; enable VAD with safe defaults.
  - P1: Logging schema (JSONL): timestamp, target_app_captured, target_app_restored, hide_ts, paste_ts, success/fail.
  - P1: DI limited to engine + injector for testability; avoid broad refactors until bugs are green.
  - P2: MLX/whisper.cpp exploration behind a config flag; define success criteria (<1s E2E) before WhisperKit rewrite.
- Specify call wiring: `start_recording` captures app → stored in state → passed to `inject_text(restore_app=...)` → `inject_text` reactivates immediately before paste. Call this out as required, not optional.
- Make timing configurable: default 0.25s for bubble-hide and pre-paste, with a config key to tune for Electron targets.
- Guardrails: If focus restore fails, log and retry once; if VAD drops all audio, emit a warning instead of injecting nothing silently.

## Recommended Next Actions (no code, doc guidance)
- Add a “Minimal P0 Implementation” section to the roadmap with the exact call-flow wiring and required logs.
- Add a config snippet for timing knobs (`focus_settle_ms`, `clipboard_settle_ms`) and VAD defaults.
- Add success criteria: focus restored in >95% of paste attempts across Notes + VS Code; “first word captured” in 5/5 hot-start tests; E2E latency target (<3s CPU, stretch <1s with MLX flag).

