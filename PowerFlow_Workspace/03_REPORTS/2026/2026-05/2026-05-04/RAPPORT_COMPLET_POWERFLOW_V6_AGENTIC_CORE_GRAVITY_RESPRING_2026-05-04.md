# RAPPORT COMPLET — PowerFlow V6 / Agentic Core V0.1 / Gravity Respring Rotation

**Date :** 2026-05-04  
**Session :** mise en place rapide des agents PowerFlow + validation LAB_004 + scan historique semaine précédente  
**Statut :** mission accomplie — noyau agentique V0.1 opérationnel  
**Mode :** combat / read-only DB / sans cockpit / sans Telegram  
**Durée indicative :** moins de 45 minutes pour obtenir la chaîne minimale fonctionnelle

---

## 1. Résumé exécutif

Cette session a permis de faire passer PowerFlow V6 d’un ensemble de modules et de concepts vers un premier **noyau agentique opérationnel**.

Chaîne validée :

```text
DBVisionGuard
→ FlowEventExtractor
→ SceneNamer
```

Objectif atteint :

```text
Lire la DB
découper le film
nommer la scène
sortir le next watch
```

Résultat central :

```text
PowerFlow sait maintenant extraire automatiquement :
PRE_FIELD
NODE_BIRTH
CONFIRMATION
COUNTER_BREATH
ABSORPTION
WATCH_SECOND_LEG
```

Le moteur a été testé sur :

```text
LAB_004 — GBPUSD 2026-05-04 09:00 → 10:15
force_snapshots legacy
force_snapshots_v2 live extended
scan semaine précédente legacy force-only
```

Conclusion :

```text
Agentic Core V0.1 est vivant.
La famille GRAVITY_RESPRING_ROTATION commence à être répétable.
```

---

## 2. Contexte de départ

La grammaire PowerFlow a été consolidée dans :

```text
LEXIQUE_GRAMMAIRE_POWERFLOW_V6_CONSOLIDE_2026-05-04.md
```

Objectif avant saut agentique :

```text
mettre à jour la grammaire
éviter de coder avec un vocabulaire dispersé
rassembler nodes / zones / fenêtres / agents / battlefield / DB V2
```

Une fois la grammaire stabilisée, la décision a été :

```text
GO Agentic Core V0.1
pas cockpit
pas Telegram
pas interface
read-only DB uniquement
```

---

## 3. Documents Lab intégrés pendant la session

Deux documents importants ont été ajoutés et pris en compte.

### 3.1 NOTES_NEXT_LABS_POWERFLOW_V6_2026-05-04.md

Apports centraux :

```text
M1 bavarde hors fenêtre.
M1 révèle la naissance dans la bonne fenêtre.
```

Concepts ajoutés :

```text
MICRO_WINDOW_ACTIVE
M1_NODE_BIRTH
M5_TACTICAL_CONFIRMATION
M15_SCENE_CONFIRMATION
PRICE_LAG_THEN_CATCHUP
VOLUME_PRESSURE_SPIKE
SPREAD_FRICTION_FIELD
FORCE_KINEMATICS
VELOCITY_FORCE
ANGLE_FORCE
ACCELERATION_FORCE
ENERGY_ROTATION
LOOKBACK_EXPERIMENT_FIELD
SCALP_FAST_FIELD
SCALP_FRACTAL_FIELD
SCALP_DEEP_FIELD
```

Lecture hiérarchique confirmée :

```text
HTF  = gravité / théâtre / pression de fond
M15  = scène tactique courte
M5   = traduction tactique / timing
M1   = naissance / micro-inflexion / accélération
```

Formule retenue :

```text
Le signal n’est pas un point unique.
Le signal est une séquence.
```

Séquence type :

```text
préparation
→ fenêtre active
→ naissance
→ confirmation
→ réponse prix
→ fermeture fenêtre
```

---

### 3.2 CHECKPOINT_POWERFLOW_V6_DB_V2_2026-05-04.md

Apports centraux :

```text
force_snapshots = legacy / compatibilité modules existants
force_snapshots_v2 = EA extended / flux enrichi / future base des agents séquence
```

Table V2 créée :

```text
force_snapshots_v2
```

Colonnes validées :

```text
created_at
symbol
timeframe
bar_time
bar_close_time
server_time
capture_time
is_closed_bar
bid
ask
mid
spread
spread_points
spread_price
spread_pips
open
high
low
close
tick_volume
pip_range
pip_body
pip_change
force_gbp
force_usd
force_eur
force_jpy
force_cad
force_chf
force_aud
force_nzd
```

Validation observée :

```text
force_nzd       OK
open/high/low   OK
close           OK
tick_volume     OK
pip_range       OK
pip_body        OK
pip_change      OK
spread_points   OK
spread_price    OK
spread_pips     OK
bid/ask/mid     OK
bar_time        OK
capture_time    OK
is_closed_bar   OK
```

Règle technique importante :

```python
bid = raw.get("bid")
close = raw.get("close")
ask = raw.get("ask")
mid = raw.get("mid")
```

À éviter :

```python
bid = raw.get("close", raw.get("bid"))
```

Car cela mélange prix live et clôture bougie.

---

## 4. Session 1 — DBVisionGuard V0.1

### Fichiers créés

```text
pf_db_vision_guard.py
run_db_vision_guard_once.py
```

### Mission

```text
Vérifier si PowerFlow a les yeux ouverts.
Contrôler les tables, colonnes, timeframes, lignes récentes et gaps.
```

### Commande lancée

```powershell
python run_db_vision_guard_once.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60,240 --recent-minutes 60 --gap-threshold-minutes 180
```

### Résultat utilisateur

```text
source_table: force_snapshots_v2
schema_state: SCHEMA_EXTENDED_OK

force_snapshots: LEGACY_FORCE_ONLY
force_snapshots_v2: SCHEMA_EXTENDED_OK

TF1   OK
TF5   OK
TF15  OK
TF30  OK
TF60  OK
TF240 OK

live_state: LIVE_EXTENDED_ACTIVE
vision_state: TACTICAL_OK
can_detect_ltf_birth: True
can_validate_htf_gravity: True
```

### Gap détecté

```text
TF240:
2026-05-04T12:00:00+00:00
→ 2026-05-04T16:00:00+00:00
240.0m
HISTORICAL_GAP_DETECTED
```

### Verdict

```text
DBVisionGuard validé.
force_snapshots_v2 active.
Schéma extended complet 19/19.
Vision tactique OK.
```

Note temporelle :

```text
DB time = broker time
broker time = local + 1h
```

---

## 5. Session 2 — FlowEventExtractor V0.1 → V0.1.3

### Fichiers créés

```text
pf_flow_event_extractor.py
run_flow_event_extractor_once.py
```

### Mission

```text
Lire force_snapshots ou force_snapshots_v2.
Extraire le film brut :
PRE_FIELD
NODE_BIRTH
CONFIRMATION
COUNTER_BREATH
ABSORPTION
```

### Fenêtre test

```text
GBPUSD
2026-05-04
09:00 → 10:15
```

### Premier bug détecté

Le moteur voyait le bon cluster dans les candidats, mais choisissait mal le node.

Erreur :

```text
PRICE_LAG trop pondéré
→ la respiration 09:49→10:00 volait le NODE_BIRTH
```

Mauvais résultat initial :

```text
09:49→10:00 NODE_BIRTH
```

alors que les candidats montraient :

```text
09:22→09:42
09:21→09:41
09:23→09:43

up = CAD+USD+JPY
down = GBP+EUR+AUD+CHF
```

### Correction V0.1.3

Règle modifiée :

```text
NODE_BIRTH = première vague majeure de rotation opposée
PRICE_LAG = bonus léger seulement
une respiration tardive ne peut pas voler le node principal
```

Ajout :

```text
EXTRACTOR_VERSION = 0.1.3
```

### Résultat validé

Commande :

```powershell
python run_flow_event_extractor_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --timeframes 1,5,15
```

Sortie validée :

```text
VERSION: 0.1.3

PRE_FIELD       09:00→09:20
NODE_BIRTH      09:21→09:28
CONFIRMATION    09:30→09:48
COUNTER_BREATH  09:48→10:01
ABSORPTION      10:02→10:08
```

### Verdict

```text
FlowEventExtractor validé.
Le moteur ne confond plus respiration et node principal.
LAB_004 devient lisible automatiquement.
```

---

## 6. Session 3 — SceneNamer V0.1

### Fichiers créés

```text
pf_scene_namer.py
run_scene_report_once.py
```

### Mission

```text
Prendre les événements du FlowEventExtractor.
Nommer la scène.
Produire un rapport court PowerFlow.
```

### Commande lancée

```powershell
python run_scene_report_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --timeframes 1,5,15 --out scene_report_lab004.txt
```

### Résultat validé

```text
SCENE:
GRAVITY_RESPRING_NODE

STATE:
WINDOW_ACTIVE_AFTER_BREATH
dominant_phase=ABSORPTION
confidence=0.86

ONE_LINE:
GRAVITY_RESPRING_NODE — JPY+CAD+USD reprennent contre EUR+GBP+AUD+CHF.
WINDOW_ACTIVE_AFTER_BREATH.
NEXT: WATCH_SECOND_LEG.
```

Film :

```text
09:00→09:20 PRE_FIELD
09:21→09:28 NODE_BIRTH
09:30→09:48 CONFIRMATION
09:48→10:01 COUNTER_BREATH
10:02→10:08 ABSORPTION
```

### Verdict

```text
SceneNamer validé.
Rapport texte lisible.
Agentic Core V0.1 complet.
```

---

## 7. Test live V2 extended

### Commande lancée

```powershell
python run_scene_report_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T18:00:00 --end 2026-05-04T21:15:00 --timeframes 1,5,15 --source-table force_snapshots_v2 --out scene_report_v2_live.txt
```

### Résultat

```text
MODE: EXTENDED
SOURCE_TABLE: force_snapshots_v2

SCENE:
RAW_NODE_BIRTH

STATE:
WINDOW_YOUNG

FILM:
20:30→20:45 PRE_FIELD
20:46→20:49 NODE_BIRTH

NEXT WATCH:
WATCH_M5_CONFIRMATION
```

Lecture :

```text
20:46→20:49
GBP+JPY+AUD respring
CAD+CHF fold
prix encore retenu
```

### Verdict

```text
Les agents lisent force_snapshots_v2.
La V2 extended est accessible.
Mais FlowEventExtractor V0.1 n’utilise pas encore volume/pips/spread/NZD.
```

Prochaine évolution :

```text
FlowEventExtractor V0.2 extended
```

---

## 8. Scan semaine précédente

### Contexte

La DB historique de la semaine précédente est trouée et ne contient pas les données bougies extended.

Donc le scan est :

```text
legacy force-only
sans OHLC
sans tick_volume
sans pip_body
sans spread_pips
```

Mais il peut quand même extraire :

```text
NODE_BIRTH
CONFIRMATION
COUNTER_BREATH
ABSORPTION
GRAVITY_RESPRING_NODE
RAW_NODE_BIRTH
```

---

### 8.1 Weekly scan V0.1

Fichier :

```text
run_weekly_agent_scan.py
```

Commande :

```powershell
python run_weekly_agent_scan.py --db powerflow.db --symbol GBPUSD --start 2026-04-27T00:00:00 --end 2026-05-04T00:00:00 --timeframes 1,5,15 --window-minutes 90 --step-minutes 30 --out weekly_scan_gbpusd.txt
```

Résultat :

```text
HITS: 82
```

Problème :

```text
trop de fenêtres chevauchées
```

---

### 8.2 Weekly scan V0.2 clustered

Fichier :

```text
run_weekly_agent_scan_v02.py
```

Résultat :

```text
RAW_HITS: 82
CLUSTERS: 3
```

Problème :

```text
clusters trop gros
la DB trouée colle artificiellement des demi-journées
```

---

### 8.3 Weekly scan V0.3 gap-aware

Fichier :

```text
run_weekly_agent_scan_v03.py
```

Commande :

```powershell
python run_weekly_agent_scan_v03.py --db powerflow.db --symbol GBPUSD --start 2026-04-27T00:00:00 --end 2026-05-04T00:00:00 --timeframes 1,5,15 --window-minutes 90 --step-minutes 30 --cluster-gap-minutes 45 --max-cluster-minutes 180 --min-rows-window 20 --top 20 --out weekly_scan_gbpusd_v03.txt
```

Résultat :

```text
RAW_HITS: 80
CLUSTERS: 22
```

Verdict :

```text
Scan V0.3 exploitable.
Les fenêtres sont regroupées proprement.
```

---

## 9. Fenêtres historiques ouvertes

### 9.1 Fenêtre 2026-05-01 08:00 → 09:30

Commande :

```powershell
python run_scene_report_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-01T08:00:00 --end 2026-05-01T09:30:00 --timeframes 1,5,15 --out scene_report_20260501_0800.txt
```

Résultat :

```text
SCENE:
GRAVITY_RESPRING_NODE

STATE:
WINDOW_ACTIVE_AFTER_BREATH

ONE_LINE:
GRAVITY_RESPRING_NODE — JPY+CAD+USD reprennent contre EUR+GBP+CHF+AUD.
WINDOW_ACTIVE_AFTER_BREATH.
NEXT: WATCH_SECOND_LEG.
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
LAB_MATCH FORT
```

Pourquoi :

```text
Très proche de LAB_004.
Même famille JPY/CAD/USD vs EUR/GBP/AUD/CHF.
```

---

### 9.2 Fenêtre 2026-04-30 17:30 → 19:00

Commande :

```powershell
python run_scene_report_once.py --db powerflow.db --symbol GBPUSD --start 2026-04-30T17:30:00 --end 2026-04-30T19:00:00 --timeframes 1,5,15 --out scene_report_20260430_1730.txt
```

Résultat :

```text
SCENE:
GRAVITY_RESPRING_NODE

STATE:
WINDOW_ACTIVE_AFTER_BREATH

ONE_LINE:
GRAVITY_RESPRING_NODE — AUD+CAD+CHF+JPY reprennent contre EUR+USD+GBP.
WINDOW_ACTIVE_AFTER_BREATH.
NEXT: WATCH_SECOND_LEG.
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
LAB_MATCH PARTIEL / VARIANTE ROTATION VIOLENTE
```

Pourquoi :

```text
Séquence complète.
Mais bloc différent : AUD+CAD+CHF+JPY vs EUR+USD+GBP.
```

---

## 10. Famille comportementale découverte

Nom proposé :

```text
GRAVITY_RESPRING_ROTATION_FAMILY
```

Définition :

```text
Famille de séquences où un bloc gravité/refuge/pivot reprend violemment le champ contre un bloc opposé,
puis passe par confirmation, respiration contraire et absorption.
```

Structure commune :

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

Variantes observées :

```text
JPY+CAD+USD vs EUR+GBP+CHF+AUD
AUD+CAD+CHF+JPY vs EUR+USD+GBP
USD+CAD+JPY vs EUR+GBP+AUD+CHF
```

Interprétation :

```text
La rotation violente de la semaine précédente est lisible en force-only.
La fractalité commence à apparaître : les scènes s’imbriquent.
```

Phrase clé :

```text
La fractalité confirme que le node n’est pas un point.
C’est une séquence imbriquée dans une rotation plus large.
```

---

## 11. État des fichiers créés

### Agents

```text
pf_db_vision_guard.py
run_db_vision_guard_once.py

pf_flow_event_extractor.py
run_flow_event_extractor_once.py

pf_scene_namer.py
run_scene_report_once.py
```

### Scanners

```text
run_weekly_agent_scan.py
run_weekly_agent_scan_v02.py
run_weekly_agent_scan_v03.py
```

### Sorties utilisateur

```text
scene_report_lab004.txt
scene_report_v2_live.txt
weekly_scan_gbpusd.txt
weekly_scan_gbpusd_v02.txt
weekly_scan_gbpusd_v03.txt
scene_report_20260501_0800.txt
scene_report_20260430_1730.txt
```

---

## 12. Ce qui est fiable maintenant

```text
DBVisionGuard sait distinguer legacy / v2 / gaps / live.
FlowEventExtractor sait découper un film force-only.
SceneNamer sait nommer une scène courte.
Weekly scan V0.3 sait sortir des clusters exploitables.
LAB_004 est détecté automatiquement.
La famille GRAVITY_RESPRING_ROTATION est répétable.
```

---

## 13. Limites actuelles

```text
Legacy force-only ne connaît pas les bougies.
PRICE_UNKNOWN apparaît sur historique sans bid exploitable ou sans réponse prix claire.
La V0.1 ne mesure pas encore volume/pips/spread/NZD.
Pas encore de FractalWindowEngine.
Pas encore de comparaison M1/M5/M15/M30/H1/H4.
Pas encore de score de répétabilité statistique.
Pas encore de cockpit_state_v2.json.
```

---

## 14. Prochaines missions recommandées

### Mission 1 — Créer le Lab famille avec screens

Nom :

```text
LAB_FAMILY_GRAVITY_RESPRING_ROTATION_2026-05-04.md
```

Inclure :

```text
LAB_004 2026-05-04 09:00→10:15
MATCH 2026-05-01 08:00→09:30
VARIANT 2026-04-30 17:30→19:00
screens
lecture trader
preuves DB
phases agents
différences
hypothèse répétable
```

---

### Mission 2 — Patch lexique officiel

Ajouter au lexique consolidé :

```text
GRAVITY_RESPRING_ROTATION_FAMILY
USD_CAD_JPY_RESPRING_VS_RISK_FOLD
FRACTAL_ROTATION_IMBRICATION
LAB_MATCH_FORT
LAB_MATCH_PARTIEL
RAW_VARIANT_ROTATION
MICRO_WINDOW_ACTIVE
M1_NODE_BIRTH
M5_TACTICAL_CONFIRMATION
M15_SCENE_CONFIRMATION
PRICE_LAG_THEN_CATCHUP
VOLUME_PRESSURE_SPIKE
SPREAD_FRICTION_FIELD
LOOKBACK_EXPERIMENT_FIELD
SCALP_FAST_FIELD
SCALP_FRACTAL_FIELD
SCALP_DEEP_FIELD
```

---

### Mission 3 — FlowEventExtractor V0.2 Extended

Ajouter lecture :

```text
force_nzd
OHLC
tick_volume
pip_range
pip_body
pip_change
spread_pips
ask
mid
bar_time
capture_time
is_closed_bar
```

Nouveaux états :

```text
MICRO_WINDOW_ACTIVE
M1_NODE_BIRTH
VOLUME_PRESSURE_SPIKE
PRICE_LAG_THEN_CATCHUP
SPREAD_FRICTION_FIELD
M5_TACTICAL_CONFIRMATION
```

---

### Mission 4 — FractalWindowEngine V0.1

Objectif :

```text
Relier M1/M5/M15 avec M30/H1/H4.
Dire où se situe la fenêtre.
```

Sorties :

```text
WINDOW_YOUNG
WINDOW_ACTIVE
WINDOW_LATE
WINDOW_CLOSED
WATCH_CONFIRMATION
WATCH_COUNTER_BREATH
WATCH_ABSORPTION
WATCH_SECOND_LEG
HTF_GRAVITY_SUPPORTIVE
LTF_BIRTH_ACTIVE
HTF_CONFIRMED_BUT_LTF_LATE
```

---

### Mission 5 — Daily Agent Scan V0.1

Objectif :

```text
Scanner une journée.
Clusteriser les fenêtres.
Sortir 5 scènes utiles.
Préparer les Labs sans noyer le trader.
```

---

## 15. Verdict final

Mission accomplie.

```text
PowerFlow V6 Agentic Core V0.1 est opérationnel.
La DB V2 extended est reconnue.
LAB_004 est détecté automatiquement.
La semaine précédente révèle une famille de rotations violentes.
La prochaine étape est le Lab fractal avec screens.
```

Phrase finale :

```text
PowerFlow commence à lire non seulement un événement,
mais une famille de séquences imbriquées.
```
