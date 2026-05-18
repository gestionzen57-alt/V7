# Commandes T0126 — B9 Runtime Replay Pack Collector

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0126_b9_runtime_replay_pack_collector.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0126_b9_runtime_replay_pack_collector.ps1"
```

## CLI directe

```powershell
python tools\build_t0126_b9_runtime_replay_pack_collector.py `
  --scan-root . `
  --output-dir outputs\b9_runtime_replay_pack_collector_v0
```

## T0125 ensuite sur batch reel

Utiliser les chemins KEEP produits dans :

```text
outputs\b9_runtime_replay_pack_collector_v0\B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv
```
