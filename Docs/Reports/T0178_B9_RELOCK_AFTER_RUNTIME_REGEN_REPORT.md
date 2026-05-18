# T0178 - B9 Relock After Runtime Regen V0

## Mission

Relancer T0175 puis T0176 apres generation ou recuperation des artefacts runtime B9.

## Goal

Passer de `LOCK_BLOCKED_MISSING_REQUIRED` vers :

- `LOCK_READY_FOR_DASHBOARD_REVIEW`
- `LOCK_PARTIAL_OPTIONAL_MISSING`
- ou au minimum `DEGRADED_READY` / `OPERATIONAL_DEGRADED`

## Delivered files

- `tools/build_t0178_b9_relock_after_runtime_regen.py`
- `tests/test_t0178_b9_relock_after_runtime_regen.py`
- `scripts/RUN_T0178_B9_RELOCK_AFTER_RUNTIME_REGEN_FROM_DOWNLOADS.ps1`
- `samples/t0178_b9_relock_after_runtime_regen_v0/README.md`
- `Docs/Reports/T0178_B9_RELOCK_AFTER_RUNTIME_REGEN_REPORT.md`
- `Docs/Reports/T0178_B9_RELOCK_AFTER_RUNTIME_REGEN_MANIFEST.json`
- `Docs/Reports/COMMANDES_T0178_B9_RELOCK_AFTER_RUNTIME_REGEN.md`
- `Docs/Reports/MESSAGE_CLAUDE_T0178_B9_RELOCK_AFTER_RUNTIME_REGEN.md`

## Runtime outputs

- `outputs/t0178_b9_relock_after_runtime_regen_v0/B9_RELOCK_AFTER_RUNTIME_REGEN_V0.json`
- `outputs/t0178_b9_relock_after_runtime_regen_v0/B9_RELOCK_AFTER_RUNTIME_REGEN_V0.md`
- `outputs/t0178_b9_relock_after_runtime_regen_v0/B9_RELOCK_REMAINING_MISSING_INPUTS_V0.csv`
- `outputs/t0178_b9_relock_after_runtime_regen_v0/B9_RELOCK_REGEN_COMMANDS_V0.csv`
- `outputs/t0178_b9_relock_after_runtime_regen_v0/B9_RELOCK_COMMAND_RESULTS_V0.csv`
- `outputs/t0178_b9_relock_after_runtime_regen_v0/B9_RELOCK_AFTER_RUNTIME_REGEN_MANIFEST_V0.json`

## Contract

- No cockpit live modification.
- No DB touch.
- No Telegram.
- No BUY/SELL.
- No success probability.
- No decision button.
- Dashboard displays. It does not decide.
