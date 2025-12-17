# Reliability and Testing Blueprint

**Purpose:** Make Erik STT more reliable than SuperWhisper through testability, not clever code.  
**Created:** December 17, 2025  
**Sources:** Consolidated from tail-cutoff test plan, test mode architecture, and reliability blueprint docs.

---

## The North Star

You're not trying to win "best transcription model." You're trying to win:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Tail retention** | 100% (last sentence intact) | Per-test scoring |
| **Time to first text** | <500ms | Log timestamps |
| **Time to final text** | <3s | Log timestamps |
| **Hang rate** | 0% | Sessions requiring manual intervention |
| **Predictability** | Same input → same output | Replay tests |

---

## Architecture: Three Isolatable Stages

Failures become debuggable when you separate the pipeline:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CAPTURE    │ →  │  TRANSCRIBE  │ →  │    POLISH    │
│ hotkey→audio │    │ audio→raw    │    │ raw→polished │
└──────────────┘    └──────────────┘    └──────────────┘
     ↓                    ↓                    ↓
 audio_raw.wav        raw.txt            polished.txt
```

Each stage logs start/end times and either returns success or an explicit failure. **No silent stalls.**

---

## Flight Recorder (Every Run)

Every hotkey run automatically produces a bundle:

```
sessions/
└── 2025-12-17T14-30-00/
    ├── audio_raw.wav        # What the mic captured
    ├── raw.txt              # Verbatim transcription
    ├── polished.txt         # (if polish enabled)
    ├── events.json          # Timing + config + outcome
    └── logs.txt             # Debug output
```

**events.json schema:**
```json
{
  "session_id": "2025-12-17T14-30-00",
  "timestamps": {
    "hotkey_down": "14:30:00.000",
    "first_audio_frame": "14:30:00.050",
    "last_audio_frame": "14:30:05.200",
    "first_text": "14:30:05.800",
    "final_text": "14:30:06.100"
  },
  "config": {
    "model": "medium.en",
    "vad_enabled": true,
    "rewrite_enabled": false
  },
  "outcome": {
    "tail_warning": false,
    "hang_detected": false,
    "retry_count": 0,
    "success": true
  }
}
```

This one decision unlocks "ridiculous testing" without manual effort.

---

## Two Modes: Real + Test

### Real Mode (Normal Usage)
- Hotkey down → start capture
- Hotkey up → stop capture
- Pipeline runs, text injected

### Test Mode (Replay)
```bash
python -m src.main --test audio.wav --events events.json
```
- Feed it audio file + pretend hotkey timing
- Runs exact same pipeline
- Outputs raw, polished, timings, logs

**This is what unlocks "compute goes brrrr" testing.**

---

## Tail-Loss Defenses

Tail-loss is the #1 bug. These defenses don't depend on model quality:

### 1. Tail Pad
Always keep recording **+2 seconds** after hotkey release (or apparent speech end).

### 2. Finalize Barrier
Don't finalize until:
- You've seen **N ms silence**, AND
- The transcription backend has returned the "final chunk"

### 3. Annotate, Don't Delete
If a sentence is incomplete, keep it and append: `[TRAILING]`

### 4. Two-Pass Output (Mandatory)
- **Raw transcript** = source of truth (verbatim)
- **Polished transcript** = optional layer

Add a "polish cannot delete content" guardrail:
- Length ratio check (polished can't be materially shorter than raw)
- Diff check (flag any missing content)

---

## Anti-Hang Defenses

### Watchdog Timers (Per Stage)
| Stage | Timeout | Action |
|-------|---------|--------|
| Capture | No audio frames for 5s | Restart input |
| Transcribe | No tokens for 10s | Restart worker (keep audio) |
| Polish | No response for 5s | Return raw only |

### Circuit Breaker
1. Retry transcription once with fallback config (smaller model)
2. If still stuck, return saved audio + failure code
3. **Never silent failure**

---

## Tail-Cutoff Test Plan

### Test Set (10 clips, 20-60 seconds each)

Record these deliberately "tail-fragile" clips:

| # | Scenario | Why It's Hard |
|---|----------|---------------|
| 1 | Clean stop | Baseline |
| 2 | Trailing clause | "…and that's why I think—" |
| 3 | Important last word | "…the password is *banana*" |
| 4 | Fast stop | Stop speaking + stop recording instantly |
| 5 | Soft fade | Speak quietly at end |
| 6 | Background noise | Fan/café noise |
| 7 | Breath + pause | Breath + 1s pause, then final sentence |
| 8 | Restart at end | "Wait—one more thing: ___" |
| 9 | Numbers at end | "…the number is 37.4 miles" |
| 10 | Two sentences | Final line is two short sentences |

### Scoring (Simple + Brutal)

For each clip:

| Metric | Score |
|--------|-------|
| Tail Present? | Y / N |
| Last sentence complete? | 0 = missing, 1 = partial, 2 = complete |
| Length ratio (Polished/Raw) | Red flag if polished < raw |

### Logging Template (Per Clip)

```
Clip ID:
Scenario:
Pipeline: (Raw / Raw+Polish)

Tail Present: Y/N
Last sentence expected:
Last sentence output:

Raw length (words):
Polished length (words):
Length ratio:

Notes:
```

---

## Polish Guardrails

### Polish Prompt (if using LLM rewrite)

```
You are a transcript editor. Your job is to improve readability 
WITHOUT removing any content.

Rules:
- Clean punctuation and paragraph breaks
- Optional light filler removal ONLY if it does not remove meaning
- Do NOT delete any sentences or clauses
- If incomplete, keep it and append: [TRAILING]
- If uncertain, keep it and mark: [UNCERTAIN: ...]
- Do NOT paraphrase in a way that changes meaning
- Preserve numbers, names, and technical terms exactly

Return:
1. POLISHED_TRANSCRIPT
2. CONTENT_PRESERVATION_CHECK — list any places you were tempted 
   to delete/merge and what you did instead.
```

### Guardrail Check (Post-Polish)

```
Compare RAW vs POLISHED. Identify any content in RAW that is 
missing or meaningfully altered in POLISHED.

Return:
- MISSING_CONTENT (quote the missing fragments)
- ALTERED_MEANING (raw vs polished snippets)
- PASS/FAIL (FAIL = any missing content)
```

---

## AI Agent Roles (For Batch Testing)

| Agent | Job | Output |
|-------|-----|--------|
| **Test Designer** | Generate test matrix + scenarios | test_matrix.yaml |
| **Benchmark Runner** | Run batches in Test Mode | results.csv |
| **Failure Triage** | Cluster failures (tail vs hang vs latency) | failure_report.md |
| **Rewrite Auditor** | Ensure polish never deletes content | diff_check.md |

---

## Implementation Checklist

### Phase 1: Flight Recorder
- [ ] Add session logging + audio saving on every run
- [ ] Save events.json with timing + config + outcome
- [ ] Store in `sessions/YYYY-MM-DDTHH-MM-SS/`

### Phase 2: Test Mode
- [ ] Add `--test audio.wav` flag to main.py
- [ ] Run same pipeline, output to stdout/files
- [ ] No hotkey required in test mode

### Phase 3: Tail Defenses
- [ ] Implement tail pad (+2s after hotkey release)
- [ ] Add finalize barrier (wait for final chunk)
- [ ] Add `[TRAILING]` annotation for incomplete sentences

### Phase 4: Anti-Hang
- [ ] Watchdog timer per stage
- [ ] Circuit breaker retry logic
- [ ] Fallback config (smaller model)

### Phase 5: Batch Testing
- [ ] Record 10-20 real clips with flight recorder
- [ ] Run replay tests in Test Mode
- [ ] Generate metrics dashboard

---

## Quick Reference: Where Tail-Loss Happens

| If cutoff is in... | Likely cause | Fix |
|--------------------|--------------|-----|
| **Raw transcript** | Audio capture ends too early | Tail pad, loosen VAD threshold |
| **Polish only** | Rewrite deleting content | Guardrail prompt, diff check |
| **Both** | Finalization timing | Finalize barrier, +1-3s grace period |

---

## Success Definition

Tool is "done" when:
1. ✅ 0 tail-loss failures across 10-clip test set
2. ✅ Time-to-final-text < 3 seconds
3. ✅ 0 hangs requiring manual intervention
4. ✅ Same audio → same output (predictable)
5. ✅ Better than SuperWhisper at Erik's specific pain points

---

*"You can't improve what you can't replay."*

