# Commandes T0127 — B9 Timestamp Remap Guard V0

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0127_b9_timestamp_remap_guard.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0127_b9_timestamp_remap_guard.ps1"
```

## CLI sample

```powershell
python tools\build_t0127_b9_timestamp_remap_guard_v0.py `
  --sequence-summary-json samples\b9_timestamp_remap_guard_v0\sample_t009_sequence_summary_shifted.json `
  --replay-report-json samples\b9_timestamp_remap_guard_v0\sample_t009_replay_sequence_report.json `
  --output-dir outputs\b9_timestamp_remap_guard_v0
```

## CLI sur summary réel

```powershell
python tools\build_t0127_b9_timestamp_remap_guard_v0.py `
  --sequence-summary-json "CHEMIN\VERS\t009_sequence_summary.json" `
  --replay-report-json "CHEMIN\VERS\t009_replay_sequence_report.json" `
  --output-dir outputs\b9_timestamp_remap_guard_v0_real
```
