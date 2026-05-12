# CHECKPOINT — V7.3 TURBO WRAPPER

## Commit cible

`V7.3: integrate topdown reader into turbo wrapper`

## Fichiers principaux

- `scheduler_powerflow_turbo_wrapper.py`
- `README_V73_TURBO_WRAPPER.md`
- `RAPPORT_V73_TURBO_WRAPPER.md`
- `CHECKPOINT_V73_TURBO_WRAPPER.md`
- `LEXIQUE_PATCH_V73_TURBO_WRAPPER.md`
- `REGISTRE_BRIQUES_PATCH_V73_TURBO_WRAPPER.md`

## Test manuel

```powershell
python -m py_compile scheduler_powerflow_turbo_wrapper.py
python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD,EURUSD,USDJPY
```

Attendu :

```text
TURBO_V73_CYCLE_OK
```

## Verification scheduler

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows_task_scheduler_turbo.ps1 `
  -Action status `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
```

La tache doit appeler :

```text
python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD,EURUSD,USDJPY
```

## Nettoyage apres commit

Ne pas commiter :

- `dashboard_data.json`
- `_pending_usdjpy_diag/`
- dossiers temporaires `_v73_*`
- backups `.bak_*`
- outputs runtime `output/*` si ignores.
