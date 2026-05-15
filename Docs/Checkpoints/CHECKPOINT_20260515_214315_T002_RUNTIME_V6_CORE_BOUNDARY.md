# CHECKPOINT - T002 runtime V6 core boundary

Date: 2026-05-15T21:43:15.3369331+02:00
Focus: T002 runtime integration boundary

## Result

- pf_engine_v6_adapter.py exposes a feature-flagged V6 core runtime route.
- Default live behavior remains legacy engine fallback.
- Activation flag: POWERFLOW_T002_USE_V6_CORE=1.
- Strict flag: POWERFLOW_T002_V6_CORE_STRICT=1.
- Targeted T002 tests passed after false-positive comment fix.

## Next step

- Run feature-flagged replay before default live activation.

## Recent git log

- 468cdc9 feat(t002): wire V6 core runtime adapter boundary
- 93d2ada docs: update current state for Claude after T004 requalification
- df6403e [CHECKPOINT] Auto-session checkpoint: fin
- 5be9798 docs(scheduler): update current state for Claude
- 5d05912 feat(scheduler): extend B8 FX cohort scope
- 6d807e3 [CHECKPOINT] Targeted checkpoint: T004-O requalification
- 870dc1b docs(t004): requalify USD-base cohort diagnosis
- 7cfc751 [CHECKPOINT] Targeted checkpoint: T004-N USD base polarity cohort
- 019ecc5 audit(t004): test USD base polarity routing with USDCAD
- 968cae2 fix(scheduler): filter overlap skip from turbo failures
