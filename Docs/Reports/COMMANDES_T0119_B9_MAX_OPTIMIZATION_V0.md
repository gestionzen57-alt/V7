# Commandes T0119 — B9 Max Optimization V0

## Installer

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0119_b9_max_optimization_v0.ps1"
```

## Lancer le CLI

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core

python tools\build_t0119_b9_max_optimization_v0.py `
  --sequence-summary-json samples\b9_max_optimization_v0\sample_t009_sequence_summary_raw_calibrated.json `
  --analysis-docs Docs\Reports `
  --output-dir outputs\b9_max_optimization_v0
```

## Tests

```powershell
python -m py_compile tools\build_t0119_b9_max_optimization_v0.py
python -m pytest tests\test_t0119_b9_max_optimization_v0_contract.py
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0119_b9_max_optimization_v0.ps1"
```
