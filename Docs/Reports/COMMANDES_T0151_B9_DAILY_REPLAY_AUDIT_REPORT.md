# Commandes T0151

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0151_b9_daily_replay_audit_report.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0151_b9_daily_replay_audit_report.ps1"
```

## CLI runtime recommandé

```powershell
python tools\build_t0151_b9_daily_replay_audit_report.py `
  --replay-results-csv outputs\b9_real_replay_day_pack_runner_v0\B9_REAL_REPLAY_DAY_RESULTS_V0.csv `
  --session-scorecard-csv outputs\b9_session_replay_scorecard_v0\B9_SESSION_REPLAY_SCORECARD_ROWS_V0.csv `
  --golden-cases-csv Docs\Reports\T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv `
  --output-dir outputs\b9_daily_replay_audit_report_v0
```
