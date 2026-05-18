# Commandes T0134 — B9 French Trader Scene Report V0

## Installation one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0134_b9_french_trader_scene_report.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0134_b9_french_trader_scene_report.ps1"
```

## CLI direct

```powershell
python tools\build_t0134_b9_french_trader_scene_report.py `
  --sequence-summary-json samples\b9_french_trader_scene_report_v0\sample_t009_sequence_summary_french_report.json `
  --memory-brief-json samples\b9_french_trader_scene_report_v0\sample_b9_memory_brief_v0.json `
  --output-dir outputs\b9_french_trader_scene_report_v0
```

## Tests

```powershell
python -m py_compile pf_t009_french_trader_scene_report.py tools\build_t0134_b9_french_trader_scene_report.py
python -m pytest tests\test_t0134_b9_french_trader_scene_report.py
```
