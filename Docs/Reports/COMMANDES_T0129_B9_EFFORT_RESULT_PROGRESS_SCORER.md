# Commandes T0129 — B9 Effort / Résultat / Progrès Scorer V0

## Installer

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0129_b9_effort_result_progress_scorer.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0129_b9_effort_result_progress_scorer.ps1"
```

## CLI directe

```powershell
python tools\build_t0129_b9_effort_result_progress_scorer.py `
  --sequence-summary-json samples\b9_effort_result_progress_scorer_v0\sample_t009_sequence_summary_effort_result_progress.json `
  --output-dir outputs\b9_effort_result_progress_scorer_v0
```

## Tests

```powershell
python -m py_compile pf_t009_effort_result_progress_scorer.py tools\build_t0129_b9_effort_result_progress_scorer.py
python -m pytest tests\test_t0129_b9_effort_result_progress_scorer.py
```
