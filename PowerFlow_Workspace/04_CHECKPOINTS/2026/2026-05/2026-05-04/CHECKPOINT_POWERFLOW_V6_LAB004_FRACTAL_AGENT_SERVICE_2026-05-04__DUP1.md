# CHECKPOINT — PowerFlow V6 / LAB_004 Fractal Window / Agent Service

**Date :** 2026-05-04  
**Statut :** LAB_004 validé trader + 4 agents opérationnels mis en service  
**Mode :** combat / read-only DB / sans cockpit / sans Telegram

---

## 1. Décision actée

Le Lab validé n’est pas seulement une famille Gravity.

Nom officiel :

```text
LAB_004_TEMPORAL_WINDOW_FRACTAL_IMBRICATION
```

Nature :

```text
fenêtre temporelle fractale
node énergétique
imbrication HTF/LTF
couche multidevise
tempo par devise
sous-pattern Gravity Respring
fabrication du temps
```

Phrase noyau :

```text
Un node n’est pas seulement un croisement.
C’est un ancrage énergétique qui permet à plusieurs timeframes de s’imbriquer dans une histoire supérieure.
```

---

## 2. Screens intégrés

Screens fournis :

```text
Weekly
Daily
H4
H1
M30
M15
M5
```

Légende :

```text
GBP = orange
USD = cyan
EUR = vert
AUD = rouge
JPY = magenta
CHF = blanc
CAD = jaune
```

Fenêtre lab indiquée :

```text
ligne verticale blanche
LAB_004 — 2026-05-04 09:00→10:15
```

M1 visuel :

```text
non disponible au-delà de 4h
mais DB M1 exploitable
```

---

## 3. DB validée

Film LAB_004 extrait :

```text
09:00→09:20 PRE_FIELD
09:21→09:28 NODE_BIRTH
09:30→09:48 CONFIRMATION
09:48→10:01 COUNTER_BREATH
10:02→10:08 ABSORPTION
```

Scène :

```text
GRAVITY_RESPRING_NODE
```

État :

```text
WINDOW_ACTIVE_AFTER_BREATH
```

Next watch :

```text
WATCH_SECOND_LEG
```

---

## 4. Nouveaux concepts validés

```text
LAB_004_TEMPORAL_WINDOW_FRACTAL_IMBRICATION
TEMPORAL_WINDOW_FRACTAL_IMBRICATION
ENERGETIC_NODE_ANCHOR
HTF_PRE_NODE_FIELD
H4_CROSS_CONFIRMATION_LATE
M15_SCENE_BUILDING
M5_TACTICAL_NODE_BIRTH
PRICE_LAG_THEN_CATCHUP
TEMPORAL_ELASTICITY_FIELD
TIME_COMPRESSION_PHASE
TIME_STRETCHING_PHASE
TIME_FABRICATION_FIELD
STRATEGIC_TEMPORAL_ORCHESTRATION
HIGHER_STORY_FIELD
FRACTAL_CONTRADICTION_FIELD
FLAT_SCENE_HIDDEN_MICROSTRUCTURE
TIME_AMPLITUDE_COLLAPSE
TEMPORAL_WALL_FIELD
ENERGY_ZONE_DISJUNCTION
MULTI_TF_BREATH_SYNC
GRAVITY_RESPRING_MULTICURRENCY_LAYER
TEMPO_BY_CURRENCY_LAYER
```

---

## 5. Agents mis en service

### Agent 1 — DBVisionGuard

Statut :

```text
ACTIVE_SERVICE
```

Fichiers :

```text
pf_db_vision_guard.py
run_db_vision_guard_once.py
```

Mission :

```text
vérifier si PowerFlow voit vraiment
distinguer legacy / v2 / gaps / live
```

Commande service :

```powershell
python run_db_vision_guard_once.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60,240 --recent-minutes 60 --gap-threshold-minutes 180
```

---

### Agent 2 — FlowEventExtractor

Statut :

```text
ACTIVE_SERVICE
```

Fichiers :

```text
pf_flow_event_extractor.py
run_flow_event_extractor_once.py
```

Version validée :

```text
0.1.3
```

Mission :

```text
extraire le film brut :
PRE_FIELD / NODE_BIRTH / CONFIRMATION / COUNTER_BREATH / ABSORPTION
```

Commande service LAB :

```powershell
python run_flow_event_extractor_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --timeframes 1,5,15
```

Règle fixée :

```text
Une respiration contraire ne doit pas voler le node principal.
```

---

### Agent 3 — SceneNamer

Statut :

```text
ACTIVE_SERVICE
```

Fichiers :

```text
pf_scene_namer.py
run_scene_report_once.py
```

Version validée :

```text
0.1.0
```

Mission :

```text
nommer la scène
produire un rapport court
sortir next_watch
```

Commande service :

```powershell
python run_scene_report_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --timeframes 1,5,15 --out scene_report_lab004.txt
```

---

### Agent 4 — WeeklyAgentScan / LabCandidateScanner

Statut :

```text
ACTIVE_SERVICE
```

Fichiers :

```text
run_weekly_agent_scan_v03.py
```

Version validée :

```text
0.3_GAP_AWARE
```

Mission :

```text
scanner l’historique
clusteriser les fenêtres
sortir candidats Lab
gérer DB trouée
```

Commande service :

```powershell
python run_weekly_agent_scan_v03.py --db powerflow.db --symbol GBPUSD --start 2026-04-27T00:00:00 --end 2026-05-04T00:00:00 --timeframes 1,5,15 --window-minutes 90 --step-minutes 30 --cluster-gap-minutes 45 --max-cluster-minutes 180 --min-rows-window 20 --top 20 --out weekly_scan_gbpusd_v03.txt
```

---

## 6. Agent suivant non encore service

### FractalWindowEngine V0.1

Statut :

```text
NEXT_TO_CODE
```

Mission future :

```text
relier événements LTF et contexte HTF
qualifier compression / étirement du temps
détecter confirmation H4 tardive
classer contradictions fractales
```

Sorties futures :

```text
HTF_PRE_NODE_FIELD
LTF_BIRTH_ACTIVE
H4_CROSS_CONFIRMATION_LATE
FRACTAL_CONTRADICTION_FIELD
TIME_COMPRESSION_PHASE
TIME_STRETCHING_PHASE
HIGHER_STORY_FIELD
```

---

## 7. Prochaines missions

Ordre recommandé :

```text
1. Sauver les fichiers .md dans Docs / Checkpoints / Lexique.
2. Coder FractalWindowEngine V0.1.
3. Coder FlowEventExtractor V0.2 Extended avec OHLC / volume / pips / spread / NZD.
4. Créer DailyAgentScan V0.1.
5. Préparer cockpit_state_v2.json.
```

---

## 8. Phrase de reprise

```text
LAB_004 est validé comme fenêtre temporelle fractale.
Les 4 agents V0.1 sont en service.
La prochaine brique est FractalWindowEngine.
```
