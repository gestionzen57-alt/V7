# Commandes T0130 — B9 Center Path Internal Film V0

## Install one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0130_b9_center_path_internal_film.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0130_b9_center_path_internal_film.ps1"
```

## CLI direct

```powershell
python tools\build_t0130_b9_center_path_internal_film.py `
  --sequence-summary-json samples\b9_center_path_internal_film_v0\sample_t009_sequence_summary_center_path.json `
  --output-dir outputs\b9_center_path_internal_film_v0
```

## Tests

```powershell
python -m py_compile pf_t009_center_path_internal_film.py tools\build_t0130_b9_center_path_internal_film.py
python -m pytest tests\test_t0130_b9_center_path_internal_film.py
```
