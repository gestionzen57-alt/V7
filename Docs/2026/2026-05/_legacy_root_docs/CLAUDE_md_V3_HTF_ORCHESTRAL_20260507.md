# CLAUDE.md — PowerFlow V6 Complete Context V3
**Date**: 2026-05-07  
**Status**: PRODUCTION — HTF Corrected + Orchestral + Relational  
**Project**: PowerFlow — Market Flow Understanding Engine (Python)  
**Size**: ~28 KB densified | **Token Save**: 800+ per session

---

## 0. READ FIRST — DOCTRINE CORE CORRECTED

### Nature
```
PowerFlow = Forex flux perception engine, NOT:
  ❌ nounou / risk nanny
  ❌ BUY/SELL robot
  ❌ classic technical indicator
  ❌ delayed signal factory
  ❌ M1-only microfilm reader
```

### CRITICAL HTF CORRECTION
```
ANCIEN (FAUX):  M1/M5/M15 = centre de gravité
CORRIGÉ (VRAI): W/D/H4/H1 = contexte primaire / gravité / fenêtre
                M15/M5/M1 = manifestation tactique / ignition / relais
```

### Central Principle
```
Machine perceives → measures → names → alerts
Trader filters → decides → acts

HTF donne le contexte et la fenêtre temporelle
LTF détecte l'ignition, le relais ou l'invalidation
```

### W-D-HTF-LTF Hierarchy (CORRECTED)
```
W       régime lent / mémoire profonde / biais structurel de fond
D       cycle / respiration mère / fenêtre de retard supérieur
H4      gravité structurelle / zone de bataille / mémoire opérationnelle majeure
H1      traducteur intraday de la gravité HTF / pont H4-M15
M15     fenêtre énergétique / scénario court / battle window
M5      relais tactique / déclenchement mesuré
M1      microfilm / ignition / first detachment / rattrapage prix
```

### Operational Formula
```
HTF delayed gravity
+ H1 transition
+ M15 tactical window
+ M5 relay
+ M1 ignition
= PowerFlow actionable perception
```

### Anti-Nounou Rules
```
❌ Ne pas retenir alertes précoces par prudence générique
❌ Ne pas censurer M1 comme bruit par défaut
❌ Ne pas transformer Node en signal/BUY
❌ Ne pas financer conseil financier
❌ Ne pas réduire PowerFlow à M1-only
✅ UNIQUEMENT risques techniques (faux positif, latence, SQL slow, etc.)
```

---

## 1. ACTIVE STATE — VALIDATED CHAINS

### Node V0.7.x Chain (VALIDATED ✅)

**V0.7.1** — Capture Quality
```
Fields: live_reference_tf, relative_freshness, stale_relative_to_live_reference
Rule: Freshness must be relative to most recent timeframe in DB, not wall-clock only
```

**V0.7.2** — Relay Quality
```
Fields: m5_relay_missing_in_db, m5_relay_thin_sample, m5_relay_clean
Rule: M5 live ≠ M5 clean. Sample matters.
```

**V0.7.3** — Session Transition
```
Fields: session_transition, daily_open_transition, htf_rebuilding_after_daily_open
Rule: Daily Open rebuild ≠ ordinary stale data. Keep separate.
```

### Node V0.8.x Chain (VALIDATED RUNTIME ✅)

**V0.8-B** — Kinematics State
```
Fields: kinematics_state, angle_state, speed_state, acceleration_state, first_detachment
Example: M1_FIRST_DETACHMENT_GBP_UP, M5_POLARIZED_RELAY_FIELD

HTF RULE: Kinematics ne doit pas seulement lire M1.
          Elle doit dire si l'ignition LTF est cohérente avec la fenêtre HTF.
```

**V0.8.1** — Release State (TYPED)
```
States: RELEASE_ATTEMPT | RELEASE_CANDIDATE | RELEASE_CONFIRMED
        COUNTER_RELEASE_ATTEMPT | FAKE_RELEASE | RELEASE_REJECTED

Rule: No first_detachment = no confirmed release.
      COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED.
```

**V0.8.2** — Energy Release Alignment
```
Compares: release_state ↔ Currency Energy TF1/TF5/TF15
Mode: OBSERVATION_ONLY (never becomes signal)
Output: energy_context + secondary_state + field_quality

HTF CORRECTION: Energy Release Alignment ne regarde que TF1/TF5/TF15 pour l'instant.
                V0.8.3 ou V0.9 devra exposer explicitement le HTF_CONTEXT_STACK.
```

### Currency Energy V0.1 (LIVE OBSERVATION ✅)

```
Definition: Contextualized living force of a currency
Components: force_position, behavioral_zscore, zone_tension, speed_score, 
            angle_score, persistence_score, basket_deviation, htf_context_score
```

**CRITICAL RULES**:
```
Energy ≠ Direction
Energy ≠ Signal
Energy ≠ Node Heat
Energy QUALIFIES release_state but NEVER CREATES IT

HTF CORRECTION: Currency Energy doit intégrer le contexte W/D/H4/H1 comme gravité lente.
                Sinon elle risque de surpondérer le microfilm.
```

### Behavioral Flow (LIVE DASHBOARD ✅)

```
Definition: Dashboard comportemental complete showing node + relay + kinematics + release + energy
Sources: temporal_node_state.json → behavioral_alert_mapper.py → cockpit_agentic_state_v01.json
         → dashboard_sync_agent_v01.py → dashboard_data.json → dashboard_live.html

Key behavioral states:
  HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT
  FIRST_DETACHMENT_WITH_CLEAN_RELAY
  COUNTER_RELEASE_ATTEMPT_ALERT
  NODE_HEAT_ENERGY_DIVERGENCE
  TIGHT_GRAVITY_CLUSTER_ALERT
```

### Relational Gravity V0.1.x Chain (VALIDATED ✅)

**V0.1** — Base Probe
```
File: pf_relational_gravity_probe.py
Measures: how currencies relate to each other
Output: group, direction, leader, followers, antagonist, gap_mode, score, confidence, primary_state

States:
  POSITIVE_DISTANCE_SYNC
  GRAVITY_COMPRESSION_CLUSTER
  GRAVITY_EXPANSION_CLUSTER
  LEADER_PULLING_AWAY
  FOLLOWER_CATCH_UP
  ELASTIC_DISTANCE_STRETCH
  DESYNC_TRIGGER
  COALITION_VS_ANTAGONIST_EXPANSION
  MIRROR_GRAVITY_FIELD
  RELATIONAL_GRAVITY_NOISE
```

**V0.1.1** — Delta Filter
```
Added: DIRECTION_MIN_DELTA = 0.02
Purpose: filtrer devises plates pour éviter groupes fantômes
Result: devises plates restent dans metrics mais ne polluent plus group/antagonist
```

**P1.1** — Cockpit Bridge (VALIDATED ✅)
```
Files: pf_relational_gravity_bridge.py, cockpit_agentic_state_v01.py
Purpose: exposer relational_gravity dans cockpit
Status: cockpit_agentic_state_v01.json contient relational_gravity block

KNOWN ISSUE: USD peut apparaître leader ET antagoniste
             Champ MIXED raconté comme leader clair
```

**P1.2** — Bridge Guard (TO DO 🔴)
```
BLOCKER: Empêcher qu'un champ RELATIONAL_GRAVITY_MIXED soit raconté comme leader clair
Fix Required:
  if cross_tf_state = RELATIONAL_GRAVITY_MIXED:
    dominant_leader = MIXED
    leader_consistency = CONFLICT
    topline_reliable = false
    
INTERDITS TANT QUE P1.2 NON CORRIGÉ:
  ❌ P2 Behavioral Mapper
  ❌ Dashboard Relational Sync
  ❌ Telegram Relational Alerts
```

### Orchestral Gravity V0.2 (VALIDATED 07/05 ✅)

**New Bricks Created**:
```
pf_force_inflection.py     V0.1   — détection pliure contresens par devise par TF
pf_force_extrema.py        V0.1   — détection valleys/peaks avec asymétrie entrée/sortie
pf_orchestral_gravity.py   V0.2   — leader/follower/croisements/coalitions + zone_dynamics
run_orchestral_analysis_once.py   — combine les 3 briques, output .md ou .json
```

**Orchestral Concepts**:
```
PLIURE                     Changement brutal d'angle à contresens (sign flip + delta)
CONTRESENS_PLIURE_UP       Devise descendante plie brutalement vers haut
CONTRESENS_PLIURE_DOWN     Devise montante plie brutalement vers bas
VALLEY                     Minimum local qualifié (amplitude >= seuil par TF)
PEAK                       Maximum local qualifié
ASYMÉTRIE ENTRÉE/SORTIE    Vitesse entrée vs sortie (SLOW_ENTRY_FAST_EXIT = explosif)

LEADER (orchestral)        Devise angle le plus fort MAINTENANT
FOLLOWER (orchestral)      Devise même direction que leader, avec retard
ANTAGONIST (orchestral)    Devise direction opposée au leader
LAGGING                    Attiré mais trop faible pour être FOLLOWER
COALITION_UP/DOWN          Groupe devises même direction
CROSSING_ZONE              Deux devises niveaux proches (distance < 8)
ATTRACTION_STRENGTH        Force d'attraction follower → leader
```

**Validation DB 06/05**:
```
07:30  CAD  CONTRESENS_PLIURE_DOWN  Δ-74.7°  EXTREME  — crash Acte 1
08:00  GBP  CONTRESENS_PLIURE_UP    Δ+44.1°  BRUTAL   — rebond birth GBP
11:00  EUR  VALLEY  H1  amplitude=10.5  BALANCED
20:00  USD  LEADER (+5.6° [EARLY_EXTREME z=+2.11]) + ORCHESTRAL_COMPRESSION
```

**CRITICAL RULES**:
```
PLIURE ≠ simple variation d'angle
PLIURE = contresens brutal (sign flip + delta)
LEADER orchestral ≠ Currency Energy dominant
LEADER = angle le plus fort MAINTENANT dans cette fenêtre
ORCHESTRAL_GRAVITY ≠ signal
ORCHESTRAL_GRAVITY = carte perceptive multi-devise

NOT YET DONE:
  ❌ run_orchestral_loop.py (boucle live)
  ❌ intégration cockpit_agentic_state_v01.py (bloc orchestral)
  ❌ lab.py queries orchestrales
  ❌ H4 support (manque données avg_bars)
```

---

## 2. ACTIVE CORE FILES

### Runtime Foundation (TRÈS LOCKÉS 🔴)
```
capture_bridge.py          (live MT4 bridge)
db.py                      (database interface)
powerflow.db               (SQLite data store)
models.py, system_config.py, utils.py
```

### Active Engine Chain — Temporal Nodes (STABILISÉS ✅)
```
pf_temporal_node_state.py (V0.8.2, 99 KB, captures all nodes)
pf_behavioral_alert_mapper.py (33 KB, transforms states to alerts)
pf_currency_energy_probe.py (36 KB, energy observation)
```

### Active Engine Chain — Relational Gravity (PARTIAL ✅ / P1.2 TO DO 🔴)
```
pf_relational_gravity_probe.py (V0.1.1, relational analysis)
pf_relational_gravity_bridge.py (P1.1 OK, P1.2 TO FIX)
```

### Active Engine Chain — Orchestral Gravity (VALIDATED 07/05 ✅)
```
pf_force_inflection.py (V0.1, pliures contresens)
pf_force_extrema.py (V0.1, valleys/peaks asymétrie)
pf_orchestral_gravity.py (V0.2, leader/follower/coalitions)
run_orchestral_analysis_once.py (runner orchestral complet)
```

### Cockpit/Dashboard Chain (LIVE ✅)
```
cockpit_agentic_state_v01.py (13 KB, cockpit aggregation)
dashboard_sync_agent_v01.py (6 KB, final dashboard prep)
dashboard_live.html (32 KB, live visual)
dashboard_server.py (10 KB, web server)
dashboard_data.json (live JSON output)
```

### Cockpit Support Chain (SUPPORTING 🟢)
```
pf_fractal_zone_stack.py
pf_session_zone_reader.py
pf_powerflow_zone_brief.py
pf_zone_dynamics.py (used by orchestral_gravity)
pf_zone_evolution_reader.py
pf_zone_context_logger.py
```

### Radar/Coalition Chain (SUPPORTING 🟢)
```
pf_coalitions.py
pf_coalition_relations.py
pf_battlefield_radar.py
pf_battlefield_map.py
pf_cockpit_field.py
```

### Lab/Standby (NOT YET 🔵)
```
pf_temporal_nodes.py (old standby, use pf_temporal_node_state instead)
pf_temporal_density.py (spec-only, don't code yet)
pf_temporal_patterns.py (experimental)
```

---

## 3. LEXIQUE COMPLET V3 — HTF + ORCHESTRAL

### HTF Context (NEW 07/05)
```
HTF_CONTEXT_STACK                  W/D/H4/H1 complete context view
HTF_DELAYED_GRAVITY                HTF retardé créant fenêtre exploitable
HTF_TEMPORAL_WINDOW                Fenêtre temporelle HTF active
HTF_LAG_CATCHUP_WINDOW             Fenêtre où prix rattrape retard HTF
WEEKLY_REGIME_MEMORY               Mémoire régime lent W
DAILY_CYCLE_MEMORY                 Mémoire cycle D
H4_GRAVITY_FIELD                   Champ de gravité H4 structurel
H1_INTRADAY_TRANSLATOR             H1 traduit H4/D en intraday
HTF_BATTLE_CONTEXT                 Contexte de bataille HTF
HTF_DELAYED_SIGNAL_WINDOW          Fenêtre retardée HTF
HTF_STRUCTURAL_LAG                 Retard structurel HTF
```

### LTF inside HTF Context (NEW 07/05)
```
LTF_IGNITION_INSIDE_HTF_DELAY      Ignition LTF dans fenêtre HTF retardée
M1_MICROFILM_NOT_PRIMARY_CONTEXT   M1 n'est pas contexte primaire
M1_FIRST_DETACHMENT_INSIDE_HTF_WINDOW  First detachment M1 dans fenêtre HTF
M5_RELAY_INSIDE_HTF_FIELD          Relais M5 dans champ HTF
M15_TACTICAL_WINDOW_FROM_HTF_GRAVITY   Fenêtre tactique M15 depuis gravité HTF
PRICE_CATCHUP_TO_HTF_DELAY         Prix rattrape retard HTF
```

### Force & Tension
```
Z-SCORE_BEHAVIORAL                 Normalized behavioral tension (-∞ to +∞)
ELASTIC_LOADED                     Tension maintained + pullbacks absorbed
CHARGED                            Energy stored, ready for release
TENSION_FIELD                      Active tension zone
PRICE_LAG_THEN_CATCHUP             Price delayed then catches up to force
SPREAD_FRICTION_FIELD              Spread creates reading friction
```

### Zones (6 States)
```
NEUTRAL                            No sufficient tension
PRE_EXTREME                        Approaching extreme zone
EARLY_EXTREME                      Extreme born (immature)
ACCUMULATING                       Tension building, pullbacks absorbed
LEAKING                            Energy escaping
RUPTURE                            Release or structure break
```

### Nodes & Detachment
```
NODE                               Energy window (not geometric cross)
FIRST_DETACHMENT                   First cinematic separation
SAME_ANGLE_CLUSTER                 Multiple bars same angle
TIGHT_GRAVITY_CLUSTER              Compressed angle group
POLARIZED_RELAY_FIELD              Relay clearly directional
```

### Relay Quality
```
M5_RELAY_MISSING_IN_DB             No recent M5 bars
M5_RELAY_THIN_SAMPLE               M5 exists but sparse
M5_RELAY_CLEAN                     M5 tactical relay valid
CLEAN_RELAY                        Good tactical confirmation
```

### Release & Kinematics
```
RELEASE_ATTEMPT                    First attempt to break
RELEASE_CANDIDATE                  Qualified attempt
RELEASE_CONFIRMED                  Validated break with structure
COUNTER_RELEASE_ATTEMPT            Attempt in opposite direction
FAKE_RELEASE                       False break / absorption
RELEASE_REJECTED                   Rejected move

KINEMATICS_STATE                   Angle + speed + acceleration composite
ANGLE_STATE                        Direction of force change
SPEED_STATE                        Rate of force change
ACCELERATION_STATE                 Change in rate of change
```

### Energy Qualification
```
ENERGY_RELEASE_ALIGNMENT           Compares release_state ↔ Currency Energy
ENERGY_CONTEXT                     Normalized energy view for cockpit
ENERGY_VIEW                        Internal unified energy object
ENERGY_THIN_OR_MIXED               Field not clearly supportive
ENERGY_DIVERGENT                   Energy opposes or contradicts node

COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY      Attempt weak from energy side
PAIR_ENERGY_NOT_CONFIRMED                  Pair insufficient energy
FIRST_DETACHMENT_WITHOUT_PAIR_ENERGY       Detachment lacks pair support
NODE_HEAT_ENERGY_DIVERGENCE                Node hot but energy weak
```

### Relational Gravity
```
RELATIONAL_GRAVITY_STATE           Complete relational analysis state
RELATIONAL_GRAVITY_BRIDGE          Bridge probe → cockpit
RELATIONAL_GRAVITY_COCKPIT_BLOCK   Relational block in cockpit JSON
RELATIONAL_GRAVITY_MIXED           Multiple TF directions conflict
TOPLINE_RELIABILITY                Top-level summary reliable or not
LEADER_CONSISTENCY                 Leader same across TFs or conflict
DIRECTION_CONSISTENCY              Direction same across TFs or mixed
ANTAGONIST_CONSISTENCY             Antagonists consistent or mixed
LEADER_CONFLICT_INFO               Warning when leader conflicts
DIRECTION_MIN_DELTA                Filter flat currencies (0.02)
```

### Orchestral Gravity — Inflection (NEW 07/05)
```
PLIURE                             Changement brutal d'angle contresens
CONTRESENS_PLIURE_UP               Devise descendante plie vers haut
CONTRESENS_PLIURE_DOWN             Devise montante plie vers bas
SAME_DIRECTION_INFLECTION          Changement angle fort même sens
INFLECTION_SEVERITY                MICRO / MODERATE / BRUTAL / EXTREME
```

### Orchestral Gravity — Extrema (NEW 07/05)
```
VALLEY                             Minimum local qualifié (amplitude >= seuil)
PEAK                               Maximum local qualifié
AMPLITUDE                          Profondeur valley ou hauteur peak
SLOW_ENTRY_FAST_EXIT               Énergie accumulée, libération explosive
FAST_ENTRY_SLOW_EXIT               Impulsion puis absorption
BALANCED                           Entrée/sortie symétriques
FAST_ENTRY_FAST_EXIT               Passage rapide, peu d'intérêt
```

### Orchestral Gravity — Roles (NEW 07/05)
```
ORCHESTRAL_GRAVITY                 Carte relations multi-devise vivantes
LEADER (orchestral)                Devise angle le plus fort MAINTENANT
FOLLOWER (orchestral)              Devise même direction, retard ou force moindre
ANTAGONIST (orchestral)            Devise direction opposée au leader
LAGGING                            Attiré mais trop faible pour FOLLOWER
COALITION_UP / COALITION_DOWN      Groupe devises direction identique
STRONG_SYNCHRO                     Cohésion >= 0.85 très alignées
LOOSE_ALLIANCE                     Cohésion 0.60-0.85 alignées pas parfaites
POLARIZED_FIELD                    Cohésion < 0.60 divergence interne
CROSSING_ZONE                      Deux devises niveaux proches (distance < 8)
CROSSING_IMMINENT                  Distance < 4 croisement imminent
CONVERGING                         Deux devises se rapprochent activement
ATTRACTION_STRENGTH                Force attraction follower → leader (0.0-1.0)
ZONE_QUALITY (orchestral)          Qualification zone comportementale devise
```

### Orchestral Gravity — Patterns (NEW 07/05)
```
JPY_GRAVITY_PULLING_{X}_{Y}        JPY leader tire devises vers haut
JPY_LEADER_ZONE_CONFIRMED          JPY leader + zone ACCUMULATING
LEADER_{X}_ACCUMULATING_ZONE       Leader X en accumulation fiable
LEADER_{X}_RUPTURE_BREAKOUT        Leader X en rupture cassure mécanique
ANTAGONIST_{X}_RUPTURE             Antagoniste X en rupture sens opposé
USD_CAD_SYNCHRO_DOWN_COALITION     USD et CAD chutent synchro forte
GBP_EUR_RECOVERY_WAVE              GBP mène rebond, EUR suit
CROSSING_IMMINENT_{A}_{B}          Croisement imminent entre A et B
BIPOLAR_FIELD_ACTIVE               Champ bipolaire (leaders up vs antagonistes down)
ORCHESTRAL_COMPRESSION             5+ devises neutres — compression avant mouvement
```

### Behavioral Flow
```
BEHAVIORAL_FLOW                    Complete scene story
BEHAVIORAL_ALERT_QUEUE             Prioritized behavioral alerts
HOT_DETACHMENT_COUNTER_RELEASE     Strong detach + unconfirmed release
FIRST_DETACHMENT_WITH_CLEAN_RELAY  Ignition + good M5 relay

FIRST_DETACHMENT_WITH_CLEAN_RELAY      [HOT]   Event high
COUNTER_RELEASE_ATTEMPT_ALERT          [WATCH] Counter attempt tracking
NODE_HEAT_ENERGY_DIVERGENCE            [WATCH] Heat without energy
TIGHT_GRAVITY_CLUSTER_ALERT            [INFO]  Compressed structure
SAME_ANGLE_CLUSTER_ALERT               [INFO]  Sync movement
```

### Session & Time
```
SESSION_TRANSITION                 Market session change
DAILY_OPEN_TRANSITION              Daily open rebuild (HTF)
DAILY_OPEN_CAPTURE_DESYNC          DB capture lag at daily open
HTF_REBUILDING_AFTER_DAILY_OPEN    H1/H4 refreshing post-open
```

### Coalition & Battlefield
```
COALITION                          Family of synchronized currencies
COALITION_COHESION                 Internal cleanliness of coalition
ANTAGONIST                         Opposing force group
BIPOLAR_CURRENCY                   Currency on both sides (rotation signal)
BATTLEFIELD_RADAR                  Scene prioritization
RELATION_ACTIVE                    Coalition meets antagonist
```

---

## 4. ARCHITECTURE MAP

```
INPUT: force_snapshots (DB table with devise columns)
    ↓
───────────────── TEMPORAL NODES ─────────────────
pf_temporal_node_state.py
├─ Node V0.7.x (capture, relay, session)
├─ Node V0.8.x (kinematics, release)
├─ Energy Release Alignment
└─ OUTPUT: temporal_node_state.json
    ↓
───────────────── RELATIONAL GRAVITY ─────────────────
pf_relational_gravity_probe.py
├─ Analyze currency relations per TF
├─ Leader/Followers/Antagonists
├─ Gap modes / Scores / Confidence
└─ OUTPUT: relational_gravity_state per TF
    ↓
pf_relational_gravity_bridge.py
├─ Cross-TF synthesis
├─ Dominant direction/leader/antagonist
├─ [P1.2 TO FIX] MIXED field guard
└─ OUTPUT: relational_gravity_summary
    ↓
───────────────── ORCHESTRAL GRAVITY ─────────────────
pf_force_inflection.py
├─ Detect pliures contresens per devise per TF
└─ OUTPUT: List[InflectionEvent]

pf_force_extrema.py
├─ Detect valleys/peaks avec asymétrie
└─ OUTPUT: List[ExtremaEvent]

pf_orchestral_gravity.py
├─ Leader/Follower/Antagonist roles
├─ Coalitions UP/DOWN
├─ Crossing zones
├─ Named patterns
└─ OUTPUT: OrchestraState

run_orchestral_analysis_once.py
├─ Combine inflection + extrema + orchestral
└─ OUTPUT: orchestral_report.md or .json
    ↓
───────────────── BEHAVIORAL MAPPER ─────────────────
pf_behavioral_alert_mapper.py
├─ Converts states → alerts
├─ Filters by behavioral rules
└─ OUTPUT: behavioral_alert_queue.json
    ↓
───────────────── COCKPIT AGGREGATION ─────────────────
cockpit_agentic_state_v01.py
├─ Aggregates all insights
├─ Includes: temporal_nodes, relational_gravity, [orchestral future]
└─ OUTPUT: cockpit_agentic_state_v01.json
    ↓
───────────────── DASHBOARD SYNC ─────────────────
dashboard_sync_agent_v01.py
├─ Enriches with display metadata
└─ OUTPUT: dashboard_data.json
    ↓
───────────────── DISPLAY ─────────────────
dashboard_live.html
└─ DISPLAY: visual + interactive
```

---

## 5. DATABASE CONTRACT

### Main Table
```
force_snapshots (SQLite)
├─ created_at, symbol, timeframe, bid, spread
└─ force_gbp, force_usd, force_eur, force_jpy, 
   force_cad, force_chf, force_aud
```

### Access Rules
```
❌ Never modify powerflow.db without spec
❌ Never break existing tables
✅ Read-only access for probes (sqlite3 URI mode=ro)
✅ Always create documented migrations
✅ Tests: read-only unless explicit
```

---

## 6. PYTHON CONVENTIONS

### File Naming
```
pf_*.py          PowerFlow engines
run_*.py         Execution scripts
test_*.py        Test files
*_v0xx.py        Versioned backups (archive, don't use)
*_BACKUP_*.py    Keep in Archive/
```

### Imports
```python
# Standard library first
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

# Third-party
import pandas as pd
import numpy as np

# Local
from pf_temporal_node_state import get_temporal_node_state
from pf_behavioral_alert_mapper import behavioral_alert_mapper
from pf_relational_gravity_probe import analyze_relational_gravity
from pf_orchestral_gravity import analyze_orchestral_state
from db import get_connection
```

### Code Style
```
Python 3.9+
Type hints required
Docstrings on all modules/classes/functions
PEP 8 (soft 100 chars)
Tests with pytest
```

---

## 7. CRITICAL RULES (NEVER BREAK)

### Immutable Rules
```
❌ Don't touch capture_bridge.py unless explicit
❌ Don't write to powerflow.db without spec
❌ Don't import cockpit_* inside pf_*
❌ Don't create circular dependencies
❌ Don't branch Telegram directly from pf_*
❌ Don't refactor globally during feature work
❌ Don't commit without validation
❌ Don't reduce PowerFlow to M1-only
❌ Don't ignore HTF context in new features

✅ Validate code before commit
✅ 1 feature = 1 test + 1 commit
✅ Read-only tests by default
✅ Messages: [FEATURE] / [BUG] / [CLEANUP]
✅ Always consider HTF context stack
```

---

## 8. VALIDATED CHECKPOINTS

| Date | Feature | Status | Key Achievement |
|------|---------|--------|-----------------|
| 07/05 | HTF Doctrine | ✅ CORRECTED | W/D/H4/H1 = primary context |
| 07/05 | Orchestral V0.2 | ✅ LIVE | Inflection+Extrema+Orchestra |
| 07/05 | Relational P1.1 | ✅ LIVE | Cockpit Bridge (MIXED issue known) |
| 07/05 | Relational P1.2 | 🔴 TO DO | Bridge Guard BLOCKER |
| 06/05 | V0.8.2 | ✅ LIVE | Energy Release Alignment |
| 06/05 | V0.8.1 | ✅ LIVE | Release State Typed |
| 06/05 | V0.8-B | ✅ LIVE | Kinematics State |
| 06/05 | V0.7.3 | ✅ LIVE | Session Transition |
| 06/05 | V0.7.2 | ✅ LIVE | Relay Quality |
| 06/05 | V0.7.1 | ✅ LIVE | Capture Quality |
| 06/05 | Energy V0.1 | ✅ LIVE | Currency Energy Probe |
| 06/05 | Behavioral | ✅ LIVE | Behavioral Flow + Dashboard |

---

## 9. COMMON COMMANDS

### Validate Code
```bash
python -m py_compile pf_temporal_node_state.py
python -m pytest test_behavioral_alert_mapper.py -v
```

### Run Temporal Node State
```powershell
python run_temporal_node_state_once.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --recent-minutes 180 `
  --timeframes 1,5,15,30 `
  --out output/temporal_node_state.json `
  --pretty
```

### Run Relational Gravity
```powershell
python run_relational_gravity_probe_once.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --timeframes 1,5,15 `
  --bars 50 `
  --out output/relational_gravity_state.json `
  --pretty
```

### Run Orchestral Analysis
```powershell
# Rapport orchestral complet (Markdown)
python run_orchestral_analysis_once.py `
  --db powerflow.db `
  --start "2026-05-07T05:00:00+00:00" `
  --end "2026-05-07T21:00:00+00:00" `
  --tfs "15,60" --out output/orchestral_today.md

# Rapport JSON pour cockpit
python run_orchestral_analysis_once.py `
  --db powerflow.db `
  --start "2026-05-07T07:00:00+00:00" `
  --end "2026-05-07T12:00:00+00:00" `
  --tfs "5,15,60" --json --out output/orchestral_state.json
```

### Run Behavioral Mapper
```powershell
python run_behavioral_alert_mapper_once.py `
  --temporal output/temporal_node_state.json `
  --out output/behavioral_alert_queue.json `
  --pretty --summary
```

### Run Currency Energy
```powershell
python run_currency_energy_probe_once.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --timeframe 1 `
  --bars 50 `
  --out output/currency_energy_state_m1.json `
  --pretty
```

### Dashboard Refresh
```powershell
python run_powerflow_dashboard_refresh_once.py `
  --db powerflow.db `
  --symbol GBPUSD `
  --pretty --summary
```

---

## 10. CURRENT BLOCKERS (READ FIRST BEFORE NEW WORK)

### P1.2 Bridge Guard (BLOCKER 🔴)
```
FILE: pf_relational_gravity_bridge.py
ISSUE: RELATIONAL_GRAVITY_MIXED peut sortir avec dominant_leader unique fiable
       USD apparaît dans leader ET antagonist
       
FIX REQUIRED:
  if cross_tf_state = RELATIONAL_GRAVITY_MIXED:
    dominant_leader = MIXED
    leader_consistency = CONFLICT
    topline_reliable = false
    
BLOCKED UNTIL FIX:
  ❌ P2 Behavioral Mapper (relational alerts)
  ❌ Dashboard Relational Sync
  ❌ Telegram Relational Alerts
```

### HTF Context Stack (SPEC NEEDED 🟡)
```
CURRENT: Energy/Kinematics/Relational only look at TF1/TF5/TF15
NEEDED: HTF_CONTEXT_STACK_ENGINE exposing W/D/H4/H1 gravity
STATUS: Spec to be written
PRIORITY: P3 (after P1.2 fix)
```

### Orchestral Integration (NOT YET 🔵)
```
VALIDATED: pf_force_inflection, pf_force_extrema, pf_orchestral_gravity
NOT YET: Integration into cockpit_agentic_state_v01.py
NOT YET: run_orchestral_loop.py (boucle live)
NOT YET: lab.py queries orchestrales
NOT YET: H4 support (manque données avg_bars)
PRIORITY: P4 (after HTF Context Stack)
```

---

## 11. WHEN TALKING TO CLAUDE CODE

### Good Prompts
```
"Show me the relational gravity bridge logic"
"Fix P1.2 Bridge Guard: MIXED field should not show clear leader"
"Add HTF context to energy probe"
"Integrate orchestral state into cockpit"
"Write tests for orchestral patterns validation"
```

### What NOT to Ask
```
❌ Major architectural decisions (wait for Opus/GPT)
❌ Database schema changes (need spec first)
❌ Temporal density integration (standby)
❌ New features before P1.2 fix
❌ Telegram integration (too early)
```

---

## 12. MISSION PROTOCOL

### When Starting New Mission
1. Read this CLAUDE.md first (20 min)
2. Check CURRENT_STATE + CHECKPOINT_LATEST in workspace
3. Verify file status (locked vs active)
4. Check BLOCKERS section above
5. Write test first
6. Code
7. Validate
8. Safe commit

### After Mission Completes
Produce 5 outputs:
```
1. RAPPORT (what was done)
2. CHECKPOINT (short state update)
3. LEXIQUE_PATCH (new terms to integrate)
4. CURRENT_STATE_UPDATE (if needed)
5. NEXT_ACTION (what's next)
```

---

## 13. MULTI-IA COLLABORATION

### Structure
```
Claude       → Code / consolidation / patches
Claude Code  → Implementation / testing / automation
GPT Main     → Strategy / architecture / lexique updates / HTF doctrine
GPT Code     → Features / runners / integrations
Perplexity   → Research / external insights
Gemini       → Audio digestion / mobile notes
```

### Workspace Rules
```
00_CURRENT/     ← Single source of truth
04_CHECKPOINTS/ ← Dated records
03_REPORTS/     ← Session outputs
02_DOCS_ACTIVE/ ← Lexique / doctrine / architecture
05_MISSIONS/    ← Active/done/queue
07_SPECS/       ← Active specs
08_PATCHES/     ← Active patches
09_CORE_MAP/    ← Inventaire core / dépendances
```

---

## 14. CRITICAL NO-GO

```
🚫 Never modify capture_bridge.py unless explicit
🚫 Never write to powerflow.db without authorization
🚫 Never touch Telegram without defined policy
🚫 Never refactor globally mid-mission
🚫 Never delete backups during active work
🚫 Never commit without tests passing
🚫 Never create circular dependencies
🚫 Never transform Node alert into BUY/SELL
🚫 Never use Energy as standalone signal
🚫 Never reduce PowerFlow to M1-only microfilm
🚫 Never ignore HTF context in new features
🚫 Never start P2 Behavioral Mapper before P1.2 fix
🚫 Never confuse ORCHESTRAL_GRAVITY with signal
```

---

## 15. TOKEN SAVINGS

```
BEFORE CLAUDE.MD:
  Context explanation    ~900 tokens
  Your question         ~100 tokens
  ────────────────────────────
  Total per session     ~1000 tokens 😫

AFTER CLAUDE.MD V3:
  "Lis CLAUDE.md..."    ~50 tokens
  Your question         ~100 tokens
  ────────────────────────────
  Total per session     ~150 tokens 💰

SAVINGS: 850 tokens per session (-85%)
VALUE: 10x more requests for same Opus budget 🚀
```

---

## 16. STARTUP CHECKLIST

Before any new work:
- [ ] Read this CLAUDE.md V3
- [ ] Check CURRENT_STATE + CHECKPOINT_LATEST
- [ ] Check BLOCKERS section
- [ ] Verify target file status (locked/active)
- [ ] Review test patterns
- [ ] Write test first
- [ ] Code
- [ ] Run tests
- [ ] Validate with `py_compile`
- [ ] Commit safe

---

## 17. TRADER PRIMARY NEEDS (CORRECTED)

### Not This (FAUX)
```
❌ M1/M5/M15-only reader
❌ Microfilm-centric dashboard
❌ LTF primary context
```

### This (VRAI)
```
✅ HTF context reader: W/D/H4/H1 où est la gravité?
✅ HTF delay detector: le marché est-il en retard sur HTF?
✅ LTF ignition detector: le LTF commence-t-il à rattraper?
✅ Leader/Follower/Antagonist: qui tire? qui suit? qui contredit?
✅ Energy support/divergence: l'énergie supporte-t-elle le mouvement?
✅ Relational coherence/mixed: les relations sont-elles cohérentes ou mixtes?
✅ Next watch: que surveiller ensuite?
```

### Critical Alerts Needed
```
HTF_WINDOW_ACTIVE
HTF_LAG_CATCHUP_START
M1_IGNITION_INSIDE_HTF_WINDOW
M5_RELAY_CONFIRMS_HTF_WINDOW
RELATIONAL_GRAVITY_MIXED_WARNING
FIRST_DETACHMENT_WITH_CLEAN_RELAY
ENERGY_DOES_NOT_SUPPORT_RELEASE
ORCHESTRAL_COMPRESSION_BEFORE_MOVE
LEADER_RUPTURE_BREAKOUT
SECOND_LEG_WATCH
```

---

## 18. VERDICT

```
PowerFlow V6 is perception + measurement + naming + alerting.
Not decision. Not BUY/SELL. Not risk management.

HTF (W/D/H4/H1) gives context, gravity, delayed window.
LTF (M15/M5/M1) detects ignition, relay, or invalidation.

Node V0.8.2 validates temporal behavioral reading.
Relational Gravity V0.1.1 validates multi-currency relations (P1.2 TO FIX).
Orchestral Gravity V0.2 validates pliures/extrema/leader/follower/patterns.

BLOCKER: P1.2 Bridge Guard must fix MIXED field clarity.
NEXT: HTF_CONTEXT_STACK spec + integration.
LATER: Orchestral integration into cockpit.

Trader filters. Trader decides.
Machine extends perception. Nothing more.
```

---

**END CLAUDE.MD V3**

This is your context shortcut. Updated 2026-05-07.
HTF corrected. Orchestral integrated. Relational P1.2 blocker documented.
Multi-IA ready. Zero re-explanation needed.

Use it.
