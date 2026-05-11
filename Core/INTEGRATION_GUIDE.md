# PowerFlow V7.2 — Integration Guide Session Overlay + Dashboard Dual Display

## Objectif

Ce pack livre deux durcissements architecturaux :

1. `pf_session_overlay.py` V2 complet : qualification UTC ASIAN / LONDON / NY / OVERLAP / DEAD_ZONE.
2. Dashboard dual display : Legacy/HMM et Rolling/Wavelet toujours côte à côte, avec freshness visible.

La session qualifie l'alerte. Elle ne la filtre jamais.

## Installation

Copier les fichiers à la racine `Core` du projet PowerFlow :

```powershell
Copy-Item .\pf_session_overlay.py .\Core\pf_session_overlay.py -Force
Copy-Item .\run_session_overlay_once.py .\Core\run_session_overlay_once.py -Force
Copy-Item .\patch_behavioral_alert_mapper.py .\Core\patch_behavioral_alert_mapper.py -Force
Copy-Item .\test_session_overlay.py .\Core\test_session_overlay.py -Force
Copy-Item .\dashboard_freshness_module.js .\Core\dashboard_freshness_module.js -Force
Copy-Item .\dashboard_dual_display_patch.html .\Core\dashboard_dual_display_patch.html -Force
Copy-Item .\dashboard_session_card.html .\Core\dashboard_session_card.html -Force
Copy-Item .\dashboard_contract_v2.json .\Core\dashboard_contract_v2.json -Force
```

## Tests rapides

```powershell
python -m py_compile pf_session_overlay.py
python -m py_compile patch_behavioral_alert_mapper.py
python test_session_overlay.py
python run_session_overlay_once.py --pretty
```

Cas attendus :

```text
22:15 UTC -> ASIAN / IGNITION
07:05 UTC -> LONDON / IGNITION
13:30 UTC -> OVERLAP / MAX_VELOCITY_BATTLEFIELD
20:30 UTC -> DEAD_ZONE / DEAD_ZONE
```

## Injection mapper

```powershell
python patch_behavioral_alert_mapper.py --file pf_behavioral_alert_mapper.py
python -m py_compile pf_behavioral_alert_mapper.py
```

Contrat d'alerte :

```python
alert["session_context"] = get_session_context()
```

Aucune alerte n'est retenue par la session. `DEAD_ZONE` est un contexte, pas un filtre.

## Dashboard

Le patch HTML expose :

- B1 Legacy et B1+ HMM séparés.
- B4 Rolling et B4+ Wavelet séparés.
- Session overlay card.
- Freshness `FRESH / AGING / STALE / MISSING`.
- `data-brick`, `data-method`, `data-symbol` sur chaque bloc.

Les blocs STALE deviennent rouges/grisés. Les blocs MISSING affichent un message clair.

## Validation contract V2

```powershell
Get-Content .\dashboard_contract_v2.json | ConvertFrom-Json | Out-Null
```

Le contrat interdit les fusions visuelles Legacy/HMM et Rolling/Wavelet.
