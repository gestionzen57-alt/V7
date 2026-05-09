# CHECKPOINT — PowerFlow V6

**Date :** 2026-05-04  
**Session :** Nodes, séquences, DB, agents, orchestration fractale  
**Statut global :** vision clarifiée, cockpit mis en pause, priorité agents

---

## 1. Décision majeure

```text
Cockpit en stand-by.
Priorité à la création d’agents de lecture et d’interprétation.
```

Raison :

```text
Avant d’afficher, PowerFlow doit savoir lire correctement.
```

---

## 2. Ce qui est validé

### Git / Core

```text
Branche active : codex/personality-foundation-v01
Derniers commits poussés :
ca79492
39a2b86
20923a8
3f052a6
03f08ca
```

Tests passés localement :

```text
test_pf_personalities_foundation.py
test_pf_personality_zone_bridge.py
test_pf_coalitions_v01.py
test_pf_coalitions_personality_bridge.py
test_pf_coalition_relations_v01.py
test_run_coalition_relations_once_v03.py
test_pf_coalition_relations_personality_bridge.py
test_pf_battlefield_radar_v02.py
test_pf_battlefield_radar_personality_bridge.py
```

---

## 3. DB — état actuel

DB principale :

```text
powerflow.db
```

Table utile :

```text
force_snapshots
```

Colonnes actuelles :

```text
created_at
symbol
timeframe
bid
spread
force_gbp
force_usd
force_eur
force_jpy
force_cad
force_chf
force_aud
```

Limite :

```text
La DB n’a pas persisté les nouvelles données EA.
Pas de NZD.
Pas de OHLC.
Pas de tick_volume.
Pas de pip/body/range.
Pas de spread détaillé.
Pas de is_closed_bar.
```

Point critique :

```text
Le graphique voyait M1/M5/M15.
La DB ne les avait pas sur certaines fenêtres.
```

---

## 4. Séquence 09:00 → 10:15

Node identifié :

```text
09:23 → 09:27
CAD+JPY+USD respring
EUR+GBP+CHF/AUD fold
prix retenu
```

Confirmation :

```text
09:35 → 09:45 M5
USD/CAD/JPY poursuivent
AUD/GBP/CHF se vident
bid paie
```

Respiration :

```text
09:49 → 09:54
bloc opposé rebondit
prix répond peu
```

Absorption :

```text
10:00 → 10:15
structure principale reprend
```

Pattern :

```text
LAB_004_USD_CAD_JPY_RESPRING_AGAINST_RISK_BLOCK_FOLD
```

---

## 5. Séquence 12:45 → 13:45

Lecture :

```text
Séquence visuellement forte.
DB fine absente sur M1/M5/M15.
M30 confirme seulement une jambe large.
```

M30 utile :

```text
12:30 → 13:00
bid -15.1 pips
CAD/USD montent
EUR/GBP/AUD drainent
```

Pattern :

```text
LAB_005_USD_CAD_ANGLE_BREAK_WITH_GBP_EUR_DRAIN
```

Nom court :

```text
POWER_ANGLE_BREAK_TO_PRICE_IMPACT
```

Verdict :

```text
SCÈNE VISUELLEMENT FORTE
DB PARTIELLE
PATTERN À SAUVER
CAPTURE M1/M5/M15 À CORRIGER
```

---

## 6. Scripts créés

```text
pf_sequence_reader.py
run_sequence_reader_once.py
pf_force_kinematics.py
run_force_kinematics_once.py
```

Statut :

```text
V0.1 utile en analyse.
Pas encore intégré architecture production.
```

Limite connue :

```text
SequenceReader V0.1 ne possède pas encore de mémoire de séquence.
Il peut confondre contre-breath et nouveau node.
```

---

## 7. Architecture agents prioritaire

Classement :

```text
P0 — DB Freshness Agent
P1 — SequenceReader V0.2
P1/P2 — ForceKinematics Agent
P2 — FractalOrchestrator
P3 — NodeInterpreter
P4 — LabMemory
P5 — MissionBuilder
P6 — CockpitTranslator plus tard
```

---

## 8. Prochain levier prioritaire

### P0 — DB Freshness Agent

Objectif :

```text
Savoir immédiatement si PowerFlow a les yeux ouverts.
```

Contrôles :

```text
présence M1/M5/M15/M30/H1/H4
dernière ligne par TF
trous temporels
colonnes EA extended
NZD
OHLC
volume
pips
spread
is_closed_bar
```

---

## 9. Prochaine brique logique

### SequenceReader V0.2

À ajouter :

```text
mémoire de séquence
ordre temporel
phase principal / confirmation / breath / absorption
classification de fenêtre
```

Sortie attendue :

```text
09:24 NODE_BIRTH
09:35 CONFIRMATION
09:50 COUNTER_BREATH
10:00 ABSORPTION
```

---

## 10. Brique stratégique

### FractalOrchestrator

Mission :

```text
Relier HTF et LTF.
```

États à produire :

```text
HTF_GRAVITY_NODE
LTF_PRESIGNAL_BIRTH
MTF_CONFIRMATION_LATE
WINDOW_YOUNG
WINDOW_ACTIVE
WINDOW_LATE
WINDOW_CLOSED
WATCH_SECOND_LEG
WATCH_ABSORPTION
```

Phrase clé :

```text
Le HTF donne la scène, le LTF donne la fenêtre.
```

---

## 11. À ne pas faire maintenant

```text
Ne pas refaire le cockpit.
Ne pas surcoder une interface.
Ne pas ajouter des signaux sans DB fraîche.
Ne pas coder des patterns avant de les classer.
```

---

## 12. À faire ensuite

Ordre conseillé :

```text
1. Relire rapport + lexique.
2. Corriger / valider DB EA Extended.
3. Créer spec DB Freshness Agent.
4. Créer spec SequenceReader V0.2.
5. Créer spec FractalOrchestrator.
6. Tester sur LAB_004 et LAB_005.
7. Sauver les résultats.
8. Seulement ensuite décider du code production.
```

---

## 13. Phrase finale

```text
Les agents ne remplacent pas le cockpit.
Ils préparent la clarté que le cockpit affichera plus tard.
```
