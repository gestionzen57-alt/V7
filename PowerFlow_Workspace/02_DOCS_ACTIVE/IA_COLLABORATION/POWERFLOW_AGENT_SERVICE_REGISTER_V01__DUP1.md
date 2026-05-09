# POWERFLOW AGENT SERVICE REGISTER V0.1

**Date :** 2026-05-04  
**Statut :** 4 agents opérationnels en service  
**Mode :** read-only DB / sans cockpit / sans Telegram

---

## Agents actifs

```text
1. DBVisionGuard
2. FlowEventExtractor
3. SceneNamer
4. WeeklyAgentScan / LabCandidateScanner
```

---

## 1. DBVisionGuard

```text
STATUS: ACTIVE_SERVICE
ROLE: vérifier la vision DB
FILES:
- pf_db_vision_guard.py
- run_db_vision_guard_once.py
```

Commande :

```powershell
python run_db_vision_guard_once.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60,240 --recent-minutes 60 --gap-threshold-minutes 180
```

Sorties attendues :

```text
SCHEMA_EXTENDED_OK
LIVE_EXTENDED_ACTIVE
TACTICAL_OK
DATA_PARTIAL
DATA_BLIND
HISTORICAL_GAP_DETECTED
```

---

## 2. FlowEventExtractor

```text
STATUS: ACTIVE_SERVICE
ROLE: extraire le film brut
FILES:
- pf_flow_event_extractor.py
- run_flow_event_extractor_once.py
VERSION: 0.1.3
```

Commande LAB_004 :

```powershell
python run_flow_event_extractor_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --timeframes 1,5,15
```

Sorties attendues :

```text
PRE_FIELD
NODE_BIRTH
CONFIRMATION
COUNTER_BREATH
ABSORPTION
```

---

## 3. SceneNamer

```text
STATUS: ACTIVE_SERVICE
ROLE: nommer la scène
FILES:
- pf_scene_namer.py
- run_scene_report_once.py
VERSION: 0.1.0
```

Commande LAB_004 :

```powershell
python run_scene_report_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --timeframes 1,5,15 --out scene_report_lab004.txt
```

Sorties attendues :

```text
GRAVITY_RESPRING_NODE
WINDOW_ACTIVE_AFTER_BREATH
WATCH_SECOND_LEG
```

---

## 4. WeeklyAgentScan / LabCandidateScanner

```text
STATUS: ACTIVE_SERVICE
ROLE: scanner historique et proposer candidats Lab
FILES:
- run_weekly_agent_scan_v03.py
VERSION: 0.3_GAP_AWARE
```

Commande historique :

```powershell
python run_weekly_agent_scan_v03.py --db powerflow.db --symbol GBPUSD --start 2026-04-27T00:00:00 --end 2026-05-04T00:00:00 --timeframes 1,5,15 --window-minutes 90 --step-minutes 30 --cluster-gap-minutes 45 --max-cluster-minutes 180 --min-rows-window 20 --top 20 --out weekly_scan_gbpusd_v03.txt
```

Sorties attendues :

```text
RAW_HITS
CLUSTERS
TOP CLUSTERS
LAB_MATCH candidates
RAW_VARIANT_ROTATION candidates
```

---

## Agent suivant

```text
FractalWindowEngine V0.1
STATUS: NEXT_TO_CODE
```

Mission :

```text
relier LTF / HTF
qualifier temporal elasticity
détecter H4 late confirmation
classer higher story field
```

---

## Règle de service

```text
Les agents lisent.
Les agents nomment.
Les agents ne décident pas.
Le cockpit n’écrit pas.
Le trader valide.
```

Fin du registre.
