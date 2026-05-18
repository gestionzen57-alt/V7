# Commandes T0139

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0139_b9_session_replay_scorecard.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0139_b9_session_replay_scorecard.ps1"
```

## CLI sample

```powershell
python tools\build_t0139_b9_session_replay_scorecard.py --scan-root samples\b9_session_replay_scorecard_v0 --output-dir outputs\b9_session_replay_scorecard_v0_sample
```

## CLI réel avec T0126 si disponible

```powershell
python tools\build_t0139_b9_session_replay_scorecard.py --scan-root . --input-index-csv outputs\b9_runtime_replay_pack_collector_v0\B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv --output-dir outputs\b9_session_replay_scorecard_v0
```

## CLI réel avec mission parallèle 2

```powershell
python tools\build_t0139_b9_session_replay_scorecard.py --scan-root . --scan-csv "C:\Users\User\Downloads\b9_replay_corpus_real_20260518_144423\B9_REPLAY_CORPUS_REAL_SCAN_20260518_144423.csv" --output-dir outputs\b9_session_replay_scorecard_v0
```
