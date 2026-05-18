# Commandes T0124 — B9 V4 Regression Guard + Golden Replay Cases V2

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0124_b9_v4_regression_guard_golden_replay_cases.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0124_b9_v4_regression_guard_golden_replay_cases.ps1"
```

## CLI

```powershell
python tools\build_t0124_b9_v4_regression_guard_golden_replay_cases.py `
  --input-summary-json samples\b9_v4_regression_guard_golden_replay_cases_v0\sample_b9_v4_golden_replay_cases_input.json `
  --output-dir outputs\b9_v4_regression_guard_golden_replay_cases_v0
```

## Tests

```powershell
python -m py_compile tools\build_t0124_b9_v4_regression_guard_golden_replay_cases.py
python -m pytest tests\test_t0124_b9_v4_regression_guard_golden_replay_cases.py
```


## Correctif V2

V2 aligne pytest et CLI sur le fallback local déterministe afin d’éviter le drift observé quand pytest importe un contrat natif disponible dans le repo alors que la CLI exécutée depuis tools/ utilise le fallback. T0122/T0123 restent les validations natives du hook/summarizer.
