# PowerFlow V7.2 — Pack B1 HMM + B4 Wavelet + B6 Memory

Ce pack contient :

- `Core/pf_hmm_regime.py`
- `Core/run_hmm_regime_once.py`
- `Core/pf_wavelet_density.py`
- `Core/run_wavelet_density_once.py`
- `Core/pf_memory_engine.py`
- `Core/run_memory_query_once.py`
- `scripts/validate_b1_b4_b6.ps1`

## Installation sûre

Depuis la racine Git :

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
Expand-Archive -Path C:\chemin\powerflow_v72_b1_b4_b6_pack.zip -DestinationPath . -Force
```

## Validation

```powershell
.\scripts\validate_b1_b4_b6.ps1
```

## Validation + commit/push

```powershell
.\scripts\validate_b1_b4_b6.ps1 -Commit
```

Le script utilise `pf_close_session.ps1` s'il existe.

## Notes

- Acces DB read-only via `file:...?mode=ro`.
- Aucun import cockpit/dashboard/telegram.
- Aucune ecriture DB.
- `output/*.json` est produit localement et ne doit pas etre committe.
