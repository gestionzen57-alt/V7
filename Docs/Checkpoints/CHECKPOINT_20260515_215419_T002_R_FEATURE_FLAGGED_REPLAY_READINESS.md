# CHECKPOINT - T002-R feature-flagged replay readiness

Date: 2026-05-15T21:54:19.4230061+02:00
Focus: T002-R feature-flagged replay readiness

## Result

- Feature-flag boundary tests added.
- Default legacy fallback verified.
- V6 route under POWERFLOW_T002_USE_V6_CORE verified with fake compatible core.
- Strict missing-entrypoint behavior verified.
- Readiness contract created.

## Stop rule

- Do not enable V6 core by default until real replay contract passes.

## Recent git log

- 59a3889 test(t002): validate feature-flagged V6 runtime readiness
- 9d144b1 [CHECKPOINT] Targeted checkpoint: T002 runtime V6 core boundary
- 468cdc9 feat(t002): wire V6 core runtime adapter boundary
- 93d2ada docs: update current state for Claude after T004 requalification
- df6403e [CHECKPOINT] Auto-session checkpoint: fin
- 5be9798 docs(scheduler): update current state for Claude
- 5d05912 feat(scheduler): extend B8 FX cohort scope
- 6d807e3 [CHECKPOINT] Targeted checkpoint: T004-O requalification
- 870dc1b docs(t004): requalify USD-base cohort diagnosis
- 7cfc751 [CHECKPOINT] Targeted checkpoint: T004-N USD base polarity cohort
