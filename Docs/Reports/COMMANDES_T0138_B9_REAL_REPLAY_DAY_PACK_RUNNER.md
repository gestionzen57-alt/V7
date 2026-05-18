# Commandes T0138

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0138_b9_real_replay_day_pack_runner.ps1"
```

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0138_b9_real_replay_day_pack_runner.ps1"
```

CLI direct :

```powershell
python tools\build_t0138_b9_real_replay_day_pack_runner.py --scan-root . --input-index-csv outputs\b9_runtime_replay_pack_collector_v0\B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv --output-dir outputs\b9_real_replay_day_pack_runner_v0
```


## Correction V2

Le test sample accepte maintenant les candidats KEEP ou REVIEW selon la couverture réelle des champs locaux. RAW_UNAVAILABLE-only reste rejeté. Pytest et CLI restent bloquants.
