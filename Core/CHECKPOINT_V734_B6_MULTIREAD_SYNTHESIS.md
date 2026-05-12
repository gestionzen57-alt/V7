# CHECKPOINT — V7.3.4 B6 MULTIREAD SYNTHESIS

## État attendu

- B6 normalizer compile.
- Multi-read synthesis compile.
- Multi-read dashboard contract écrit.
- Option dashboard injectée.
- Option scheduler patchée.

## Commandes de contrôle

```powershell
python -m py_compile dashboard_normalize_b6_live_fusion.py pf_powerflow_multiread_synthesis_once.py dashboard_normalize_multiread_synthesis.py
python dashboard_normalize_b6_live_fusion.py --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/b6_live_fusion_dashboard.json --pretty
python pf_powerflow_multiread_synthesis_once.py --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/powerflow_multiread_synthesis.json --pretty
python dashboard_normalize_multiread_synthesis.py --input output/dashboard_surface/powerflow_multiread_synthesis.json --output output/dashboard_surface/multiread_synthesis_dashboard.json --pretty
```
