# CHECKPOINT — V7.3.4b B6 PARSER HOTFIX

## À vérifier

Après hotfix, GBPUSD doit sortir proche de :

```text
B6 state=RELEASED
B6 bias=PAIR_DOWN
B6 action=WATCH
```

Et la synthèse doit éviter :

```text
B6_STATE_UNKNOWN
daily=MIXED pour SHORT_ACCUMULATION
```

## Commande

```powershell
python dashboard_normalize_b6_live_fusion.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --output output/dashboard_surface/b6_live_fusion_dashboard.json --pretty
python pf_powerflow_multiread_synthesis_once.py --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/powerflow_multiread_synthesis.json --pretty
python dashboard_normalize_multiread_synthesis.py --input output/dashboard_surface/powerflow_multiread_synthesis.json --output output/dashboard_surface/multiread_synthesis_dashboard.json --pretty
```
