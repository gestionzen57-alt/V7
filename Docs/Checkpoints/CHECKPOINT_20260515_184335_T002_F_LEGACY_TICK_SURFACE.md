# CHECKPOINT - T002-F detached V6 core legacy tick surface

Date: 2026-05-15T18:43:35.4545314+02:00
Focus: T002-F detached V6 core legacy tick surface

## Result

- pf_engine_v6_core.py now has a detached LegacyTickSurface.
- Fields supported: dev_a, dev_b, val_a, val_b, gap, timeframe, spread.
- Runtime remains unwired.
- Dashboard workspace files were intentionally left untouched.

## Tests

- T002 targeted tests passed during script run.

## Current git log

```text
cbaf6a4 feat(t002): extend detached engine v6 core legacy tick surface
ea988e6 [CHECKPOINT] Targeted checkpoint: T002-F legacy tick surface
bf449d7 feat(t002): extend detached engine v6 core legacy tick surface
97105c3 dashboard: clean backups and expand FR trader labels v2
14d3547 dashboard: clean FR trader patch backup files
e4f4bce [CHECKPOINT] Targeted checkpoint: T002-E tick surface vs detached V6 core
a684746 dashboard: add safe FR trader label translation
```

## Next step

Build a golden comparison test before connecting pf_engine_v6_core.py into the adapter or legacy process_tick.

