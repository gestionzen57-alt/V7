# CLAUDE.md — PowerFlow V6 Complete Context
**Date**: 2026-05-06  
**Status**: PRODUCTION READY — Node V0.8.2 + Energy + Behavioral  
**Project**: PowerFlow — Market Flow Understanding Engine (Python)  
**Size**: ~20 KB densified | **Token Save**: 750+ per session

---

## 0. READ FIRST — DOCTRINE CORE

### Nature
```
PowerFlow = Forex flux perception engine, NOT:
  ❌ nounou / risk nanny
  ❌ BUY/SELL robot
  ❌ classic technical indicator
  ❌ delayed signal factory
```

### Central Principle
```
Machine perceives → measures → names → alerts
Trader filters → decides → acts

NODE ≠ CROSS (geometric)
NODE = energy window / force partition
```

### M1-HTF Hierarchy
```
M1      naissance / microfilm / inflexion rapide
M5      relais tactique / deuxième jambe
M15     scénario court / source
M30-H1  gravité / structure
H4+     poids supérieur / mémoire
```

### Anti-Nounou Rules
```
❌ Ne pas retenir alertes précoces par prudence générique
❌ Ne pas censurer M1 comme bruit par défaut
❌ Ne pas transformer Node en signal/BUY
❌ Ne pas financer conseil financier
✅ UNIQUEMENT risques techniques (faux positif, latence, SQL slow, etc.)
```

---

## 1. ACTIVE STATE — VALIDATED NODES

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

Examples:
  ENERGY_RELEASE_ALIGNMENT
  COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY
  ENERGY_THIN_OR_MIXED
  FIRST_DETACHMENT_WITHOUT_PAIR_ENERGY
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
FIRST_DETACHMENT ≠ DOMINANT_CURRENCY_ENERGY
KINEMATICS_NODE ≠ CURRENCY_ENERGY_RANKING
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

---

## 2. ACTIVE CORE FILES

### Runtime Foundation (TRÈS LOCKÉS 🔴)
```
capture_bridge.py          (live MT4 bridge)
db.py                      (database interface)
powerflow.db               (SQLite data store)
models.py, system_config.py, utils.py
```

### Active Engine Chain (STABILISÉS 06/05 🟡)
```
pf_temporal_node_state.py (V0.8.2, 99 KB, captures all nodes)
pf_behavioral_alert_mapper.py (33 KB, transforms states to alerts)
pf_currency_energy_probe.py (36 KB, energy observation)
cockpit_agentic_state_v01.py (13 KB, cockpit aggregation)
dashboard_sync_agent_v01.py (6 KB, final dashboard prep)
```

### Dashboard/Display (LIVE 🟢)
```
dashboard_live.html        (32 KB, live visual)
dashboard_server.py        (10 KB, web server)
dashboard_data.json        (live JSON output)
```

### Cockpit Chain (SUPPORTING 🟢)
```
pf_fractal_zone_stack.py
pf_session_zone_reader.py
pf_powerflow_zone_brief.py
pf_zone_dynamics.py
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

## 3. LEXIQUE COMPLET V0.8.2

### Force & Tension
```
Z-SCORE_BEHAVIORAL    Normalized behavioral tension (-∞ to +∞)
ELASTIC_LOADED        Tension maintained + pullbacks absorbed
CHARGED               Energy stored, ready for release
TENSION_FIELD         Active tension zone
PRICE_LAG_THEN_CATCHUP Price delayed then catches up to force
SPREAD_FRICTION_FIELD Spread creates reading friction
```

### Zones (6 States)
```
NEUTRAL              No sufficient tension
PRE_EXTREME          Approaching extreme zone
EARLY_EXTREME        Extreme born (immature)
ACCUMULATING         Tension building, pullbacks absorbed
LEAKING              Energy escaping
RUPTURE              Release or structure break
```

### Nodes & Detachment
```
NODE                        Energy window (not geometric cross)
FIRST_DETACHMENT            First cinematic separation
SAME_ANGLE_CLUSTER          Multiple bars same angle
TIGHT_GRAVITY_CLUSTER       Compressed angle group
POLARIZED_RELAY_FIELD       Relay clearly directional
```

### Relay Quality
```
M5_RELAY_MISSING_IN_DB    No recent M5 bars
M5_RELAY_THIN_SAMPLE      M5 exists but sparse
M5_RELAY_CLEAN            M5 tactical relay valid
CLEAN_RELAY               Good tactical confirmation
```

### Release & Kinematics
```
RELEASE_ATTEMPT           First attempt to break
RELEASE_CANDIDATE         Qualified attempt
RELEASE_CONFIRMED         Validated break with structure
COUNTER_RELEASE_ATTEMPT   Attempt in opposite direction
FAKE_RELEASE              False break / absorption
RELEASE_REJECTED          Rejected move

KINEMATICS_STATE          Angle + speed + acceleration composite
ANGLE_STATE               Direction of force change
SPEED_STATE               Rate of force change
ACCELERATION_STATE        Change in rate of change
```

### Energy Qualification
```
ENERGY_RELEASE_ALIGNMENT  Compares release_state ↔ Currency Energy
ENERGY_CONTEXT            Normalized energy view for cockpit
ENERGY_VIEW               Internal unified energy object
ENERGY_THIN_OR_MIXED      Field not clearly supportive
ENERGY_DIVERGENT          Energy opposes or contradicts node

COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY      Attempt weak from energy side
PAIR_ENERGY_NOT_CONFIRMED                  Pair insufficient energy
FIRST_DETACHMENT_WITHOUT_PAIR_ENERGY       Detachment lacks pair support
NODE_HEAT_ENERGY_DIVERGENCE                Node hot but energy weak
```

### Behavioral Flow
```
BEHAVIORAL_FLOW                  Complete scene story
BEHAVIORAL_ALERT_QUEUE           Prioritized behavioral alerts
HOT_DETACHMENT_COUNTER_RELEASE   Strong detach + unconfirmed release
FIRST_DETACHMENT_WITH_CLEAN_RELAY Ignition + good M5 relay

FIRST_DETACHMENT_WITH_CLEAN_RELAY      [HOT]   Event high
COUNTER_RELEASE_ATTEMPT_ALERT          [WATCH] Counter attempt tracking
NODE_HEAT_ENERGY_DIVERGENCE            [WATCH] Heat without energy
TIGHT_GRAVITY_CLUSTER_ALERT            [INFO]  Compressed structure
SAME_ANGLE_CLUSTER_ALERT               [INFO]  Sync movement
```

### Session & Time
```
SESSION_TRANSITION             Market session change
DAILY_OPEN_TRANSITION          Daily open rebuild (HTF)
DAILY_OPEN_CAPTURE_DESYNC      DB capture lag at daily open
HTF_REBUILDING_AFTER_DAILY_OPEN H1/H4 refreshing post-open
```

### Coalition & Battlefield
```
COALITION                 Family of synchronized currencies
COALITION_COHESION        Internal cleanliness of coalition
ANTAGONIST                Opposing force group
BIPOLAR_CURRENCY          Currency on both sides (rotation signal)
BATTLEFIELD_RADAR         Scene prioritization
RELATION_ACTIVE           Coalition meets antagonist
```

---

## 4. ARCHITECTURE MAP

```
INPUT: force_snapshots (DB table with devise columns)
    ↓
pf_temporal_node_state.py
├─ Node V0.7.x (capture, relay, session)
├─ Node V0.8.x (kinematics, release)
├─ Energy Release Alignment
└─ OUTPUT: temporal_node_state.json
    ↓
pf_behavioral_alert_mapper.py
├─ Converts states → alerts
├─ Filters by behavioral rules
└─ OUTPUT: behavioral_alert_queue.json
    ↓
cockpit_agentic_state_v01.py
├─ Aggregates all insights
└─ OUTPUT: cockpit_agentic_state_v01.json
    ↓
dashboard_sync_agent_v01.py
├─ Enriches with display metadata
└─ OUTPUT: dashboard_data.json
    ↓
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

✅ Validate code before commit
✅ 1 feature = 1 test + 1 commit
✅ Read-only tests by default
✅ Messages: [FEATURE] / [BUG] / [CLEANUP]
```

---

## 8. VALIDATED CHECKPOINTS

| Date | Node | Status | Key Achievement |
|------|------|--------|-----------------|
| 06/05 | V0.8.2 | ✅ LIVE | Energy Release Alignment |
| 06/05 | V0.8.1 | ✅ LIVE | Release State Typed |
| 06/05 | V0.8-B | ✅ LIVE | Kinematics State |
| 06/05 | V0.7.3 | ✅ LIVE | Session Transition |
| 06/05 | V0.7.2 | ✅ LIVE | Relay Quality |
| 06/05 | V0.7.1 | ✅ LIVE | Capture Quality |
| 06/05 | Energy | ✅ LIVE | Currency Energy V0.1 |
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

## 10. WHEN TALKING TO CLAUDE CODE

### Good Prompts
```
"Show me the behavioral alert mapper logic"
"Add function to detect absorbed pullback series"
"Write tests for energy_context validation"
"Create script documenting recent changes"
```

### What NOT to Ask
```
❌ Major architectural decisions (wait for Opus)
❌ Database schema changes (need spec first)
❌ Temporal density integration (standby)
❌ Relational gravity (future mission)
```

---

## 11. MISSION PROTOCOL

### When Starting New Mission
1. Read this CLAUDE.md first (15 min)
2. Check CHECKPOINT_LATEST in workspace
3. Verify file status (locked vs active)
4. Write test first
5. Code
6. Validate
7. Safe commit

### After Mission Completes
Produce 5 outputs:
```
1. RAPPORT (what was done)
2. CHECKPOINT (short state update)
3. LEXIQUE (new terms to integrate)
4. CURRENT_STATE (update)
5. NEXT_ACTION (what's next)
```

---

## 12. MULTI-IA COLLABORATION

### Structure
```
Claude       → Code / consolidation / patches
Claude Code  → Implementation / testing / automation
GPT Main     → Strategy / architecture / lexique updates
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
```

---

## 13. CRITICAL NO-GO

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
🚫 Never confuse TemporalDensity with Temporal Nodes
```

---

## 14. TOKEN SAVINGS

```
BEFORE CLAUDE.MD:
  Context explanation    ~800 tokens
  Your question         ~100 tokens
  ────────────────────────────
  Total per session     ~900 tokens 😫

AFTER CLAUDE.MD:
  "Lis CLAUDE.md..."    ~50 tokens
  Your question         ~100 tokens
  ────────────────────────────
  Total per session     ~150 tokens 💰

SAVINGS: 750 tokens per session (-83%)
VALUE: 10x more requests for same Opus budget 🚀
```

---

## 15. STARTUP CHECKLIST

Before any new work:
- [ ] Read this CLAUDE.md
- [ ] Check CHECKPOINT_LATEST
- [ ] Verify target file status (locked/active)
- [ ] Review test patterns
- [ ] Write test first
- [ ] Code
- [ ] Run tests
- [ ] Validate with `py_compile`
- [ ] Commit safe

---

## 16. VERDICT

```
PowerFlow V6 is perception + measurement + naming + alerting.
Not decision. Not BUY/SELL. Not risk management.

Node V0.8.2 validates complete behavioral reading:
  ✅ Capture quality checks
  ✅ Relay quality validates
  ✅ Kinematics sees structure
  ✅ Release state types maturity
  ✅ Energy context observes support
  ✅ Behavioral flow tells story
  ✅ Dashboard shows scene

Trader filters. Trader decides.
Machine extends perception. Nothing more.
```

---

**END CLAUDE.MD V2**

This is your context shortcut. Updated 2026-05-06.
Multi-IA ready. Zero re-explanation needed.
Claude Code reads it automatically.

Use it.
