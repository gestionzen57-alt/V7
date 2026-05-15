# CHECKPOINT - Current state for Claude

Date: 2026-05-15T21:01:26.5402470+02:00
Focus: Update current state after T004 requalification

## Result

- Docs/CURRENT_STATE.md updated.
- Docs/CLAUDE.md current-state block updated.
- T004-O requalification recorded as current source of truth.
- Runtime unchanged.
- Dashboard runtime state restored before commit if needed.

## Current T004 reading

- Global USD-base blockage invalidated.
- Probable cause: feed / EA / capture intermittent or initial setup incomplete.
- No engine/scoring/dashboard/DB patch required.

## Recent git log

- df6403e [CHECKPOINT] Auto-session checkpoint: fin
- 5be9798 docs(scheduler): update current state for Claude
- 5d05912 feat(scheduler): extend B8 FX cohort scope
- 6d807e3 [CHECKPOINT] Targeted checkpoint: T004-O requalification
- 870dc1b docs(t004): requalify USD-base cohort diagnosis
- 7cfc751 [CHECKPOINT] Targeted checkpoint: T004-N USD base polarity cohort
- 019ecc5 audit(t004): test USD base polarity routing with USDCAD
- 968cae2 fix(scheduler): filter overlap skip from turbo failures
- 7e70266 fix(scheduler): ignore overlap skip for analytical continuation
- c3e8b66 [CHECKPOINT] Targeted checkpoint: T004-N USD base polarity cohort
- d42a0d5 audit(t004): test USD base polarity routing with USDCAD
- e7442e6 fix(scheduler): initialize core symbol scope before turbo call
