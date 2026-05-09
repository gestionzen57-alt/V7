# PATCH — FlowEventExtractor V0.2.1 Extended + Cockpit Extended Layer

## Statut

V0.2.1 calibre la force du signal micro-window.

## Changement principal

```text
MICRO_WINDOW_ACTIVE_WEAK
MICRO_WINDOW_ACTIVE_STRONG
```

## Règle

```text
WEAK  = M1/M5 node + PRICE_LAG ou pression partielle
STRONG = M1/M5 node + PRICE_LAG + VOLUME_PRESSURE_SPIKE ou PIP_RANGE_EXPANSION
```

## Cockpit

`cockpit_agentic_state_v01.py` passe en V0.1.1 et ajoute :

```text
extended_summary
extended_flags
extended_schema_state
extended
```

## Dashboard

`dashboard_live_agentic_v03.html` ajoute une carte :

```text
EXTENDED V0.2
```

## Commandes

```powershell
python run_flow_event_extractor_v02_extended_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T18:00:00 --end 2026-05-04T21:15:00 --timeframes 1,5,15 --out flow_extended_v2_live.txt
```

```powershell
python run_cockpit_agentic_state_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T18:00:00 --end 2026-05-04T21:15:00 --visual-htf-story confirmed --out output/cockpit_agentic_state_v01.json --pretty
```
