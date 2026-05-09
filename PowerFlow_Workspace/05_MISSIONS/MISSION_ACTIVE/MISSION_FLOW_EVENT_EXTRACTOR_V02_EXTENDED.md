# MISSION — FlowEventExtractor V0.2 Extended

## Statut

V0.2 Extended créé sans casser V0.1.3.

## Fichiers

```text
pf_flow_event_extractor_v02_extended.py
run_flow_event_extractor_v02_extended_once.py
```

## Objectif

Ajouter la couche extended `force_snapshots_v2` :

```text
tick_volume
pip_range
pip_body
pip_change
spread_pips
force_nzd
OHLC
bid/ask/mid
```

## Nouvelles sorties

```text
MICRO_WINDOW_ACTIVE
M1_NODE_BIRTH
M5_NODE_BIRTH
VOLUME_PRESSURE_SPIKE
PIP_RANGE_EXPANSION
PRICE_LAG_AT_NODE
PRICE_CATCHUP_CONFIRMATION
PRICE_LAG_THEN_CATCHUP
SPREAD_FRICTION_FIELD
SPREAD_CLEAN_FIELD
M5_TACTICAL_CONFIRMATION
M15_SCENE_CONFIRMATION
NZD_AVAILABLE
```

## Commande live V2

```powershell
python run_flow_event_extractor_v02_extended_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T18:00:00 --end 2026-05-04T21:15:00 --timeframes 1,5,15 --out flow_extended_v2_live.txt
```

## Commande strict V2

```powershell
python run_flow_event_extractor_v02_extended_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T18:00:00 --end 2026-05-04T21:15:00 --timeframes 1,5,15 --no-fallback-legacy --out flow_extended_v2_strict.txt
```

## Règle

V0.2 Extended mesure la microstructure.
V0.1.3 reste le film legacy validé.
