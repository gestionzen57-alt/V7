# Commandes T0169 — B9 Dashboard Surfaces Recovery

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0169_b9_dashboard_surfaces_recovery.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0169_b9_dashboard_surfaces_recovery.ps1"
```

## CLI runtime

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
python tools\build_t0169_b9_reality_board_surface_adapter_candidate.py --core-root . --output-root outputs
```

## Validation ciblée

```powershell
python -m py_compile tools\build_t0169_b9_reality_board_surface_adapter_candidate.py
python -m pytest -q tests\test_t0169_b9_reality_board_surfaces.py
python tools\build_t0169_b9_reality_board_surface_adapter_candidate.py --core-root . --input-root samples\t0169_b9_dashboard_surfaces_v0 --output-root outputs\t0169_sample_validation --strict-exit
```
