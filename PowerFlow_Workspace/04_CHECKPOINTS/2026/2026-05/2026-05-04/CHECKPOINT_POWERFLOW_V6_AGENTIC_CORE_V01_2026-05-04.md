# CHECKPOINT — PowerFlow V6 / Agentic Core V0.1

**Date :** 2026-05-04  
**Statut :** Agentic Core V0.1 validé  
**Mode :** combat / read-only DB / sans cockpit / sans Telegram

---

## 1. État global

```text
DBVisionGuard       OK
FlowEventExtractor  OK
SceneNamer          OK
Weekly Scan V0.3    OK
```

PowerFlow peut maintenant :

```text
vérifier la vision DB
lire un film force-only
détecter NODE_BIRTH / CONFIRMATION / COUNTER_BREATH / ABSORPTION
nommer GRAVITY_RESPRING_NODE
scanner une semaine trouée
clusteriser les fenêtres exploitables
```

---

## 2. DB

### Tables

```text
force_snapshots      = legacy force-only
force_snapshots_v2   = extended complet
```

### DBVisionGuard

Résultat :

```text
source_table: force_snapshots_v2
schema_state: SCHEMA_EXTENDED_OK
live_state: LIVE_EXTENDED_ACTIVE
vision_state: TACTICAL_OK
can_detect_ltf_birth: True
can_validate_htf_gravity: True
```

### Gap connu

```text
12h → 18h = historical gap
ne pas traiter comme panne live
```

### Temps

```text
DB time = broker time
broker time = local + 1h
```

---

## 3. Fichiers créés / actifs

```text
pf_db_vision_guard.py
run_db_vision_guard_once.py

pf_flow_event_extractor.py
run_flow_event_extractor_once.py

pf_scene_namer.py
run_scene_report_once.py

run_weekly_agent_scan.py
run_weekly_agent_scan_v02.py
run_weekly_agent_scan_v03.py
```

Version validée :

```text
pf_flow_event_extractor.py = V0.1.3
pf_scene_namer.py = V0.1.0
run_weekly_agent_scan_v03.py = 0.3_GAP_AWARE
```

---

## 4. LAB_004 validé

Fenêtre :

```text
GBPUSD
2026-05-04
09:00 → 10:15
```

Film extrait :

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

## 5. V2 live testé

Fenêtre :

```text
2026-05-04
18:00 → 21:15
force_snapshots_v2
```

Résultat :

```text
MODE: EXTENDED
SCENE: RAW_NODE_BIRTH
STATE: WINDOW_YOUNG
NEXT: WATCH_M5_CONFIRMATION
```

Film :

```text
20:30→20:45 PRE_FIELD
20:46→20:49 NODE_BIRTH
```

Conclusion :

```text
La V2 extended est lisible par les agents.
La V0.2 devra utiliser volume/pips/spread/NZD.
```

---

## 6. Scan semaine précédente

Commande V0.3 :

```powershell
python run_weekly_agent_scan_v03.py --db powerflow.db --symbol GBPUSD --start 2026-04-27T00:00:00 --end 2026-05-04T00:00:00 --timeframes 1,5,15 --window-minutes 90 --step-minutes 30 --cluster-gap-minutes 45 --max-cluster-minutes 180 --min-rows-window 20 --top 20 --out weekly_scan_gbpusd_v03.txt
```

Résultat :

```text
RAW_HITS: 80
CLUSTERS: 22
```

---

## 7. Fenêtres historiques validées

### 2026-05-01 08:00 → 09:30

```text
GRAVITY_RESPRING_NODE
JPY+CAD+USD vs EUR+GBP+CHF+AUD
WINDOW_ACTIVE_AFTER_BREATH
WATCH_SECOND_LEG
```

Film :

```text
08:00→08:03 NODE_BIRTH
08:24→08:44 CONFIRMATION
09:09→09:25 COUNTER_BREATH
09:25→09:30 ABSORPTION
```

Classement :

```text
LAB_MATCH_FORT
```

---

### 2026-04-30 17:30 → 19:00

```text
GRAVITY_RESPRING_NODE
AUD+CAD+CHF+JPY vs EUR+USD+GBP
WINDOW_ACTIVE_AFTER_BREATH
WATCH_SECOND_LEG
```

Film :

```text
17:30→17:38 PRE_FIELD
17:39→17:46 NODE_BIRTH
17:48→18:01 CONFIRMATION
18:02→18:21 COUNTER_BREATH
18:21→18:36 ABSORPTION
```

Classement :

```text
LAB_MATCH_PARTIEL / RAW_VARIANT_ROTATION
```

---

## 8. Famille détectée

Nom :

```text
GRAVITY_RESPRING_ROTATION_FAMILY
```

Structure :

```text
PRE_FIELD optionnel
→ NODE_BIRTH
→ CONFIRMATION
→ COUNTER_BREATH
→ ABSORPTION
→ WATCH_SECOND_LEG
```

Sous-pattern fort :

```text
USD_CAD_JPY_RESPRING_VS_RISK_FOLD
```

---

## 9. Limites actuelles

```text
force-only sur historique
pas de volume/pips/spread sur semaine précédente
PRICE_UNKNOWN fréquent
pas encore de FlowEventExtractor V0.2 extended
pas encore de FractalWindowEngine
pas encore de cockpit_state_v2.json
```

---

## 10. Prochaines missions

Ordre recommandé :

```text
1. Créer LAB_FAMILY_GRAVITY_RESPRING_ROTATION avec screens.
2. Appliquer patch lexique.
3. Coder FlowEventExtractor V0.2 extended.
4. Coder FractalWindowEngine V0.1.
5. Créer Daily Agent Scan V0.1.
6. Préparer cockpit_state_v2.json seulement ensuite.
```

---

## 11. Phrase de reprise

```text
PowerFlow lit maintenant le film :
DB → events → scene → next watch.
La prochaine étape est de relier ce film aux screens et à la fractalité HTF/LTF.
```
