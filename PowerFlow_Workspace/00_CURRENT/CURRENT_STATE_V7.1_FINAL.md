# CURRENT_STATE — PowerFlow V7.1 FINAL
**Date : 2026-05-09 | Git : acbe258 | Statut : PRODUCTION LIVE — P0 PRÊT**

---

## TABLEAU DE BORD GLOBAL

```
PowerFlow V7.1    = PRODUCTION
Version Python    = 3.x compatible
Git branch        = main
Remote            = github.com/gestionzen57-alt/V7.git
Derniers commits  = 18d0b28 (dashboard) + acbe258 (orchestrator)
Prochaine étape   = P0 lundi 12 mai 23h CEST (Asian open)
```

---

## COUCHES COMPLÈTES

```
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 0 — ACQUISITION ✅                                   │
│  capture_bridge.py  ←  MT4 TCP  →  powerflow.db (live)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 1 — MOTEUR (pf_*) ✅                                 │
│  B1-B5 + Confluence + V7.1 validation + Phase 3 replay      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 2 — ORCHESTRATION ✅                                 │
│  run_powerflow_cycle_once.py → 9 steps → cycle_report.json  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 3 — COCKPIT LIVE ✅                                  │
│  dashboard_live.html + 4 live guard cards + polling 30s     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 4 — TRADER                                           │
│  Décision finale souveraine                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## INVENTORY COMPLET — ÉTAT FINAL

### Couche 0 — Acquisition
```
capture_bridge.py              ✅  Bridge MT4 live
powerflow.db                   ✅  SQLite central live
```

### Couche 1 — Moteur (V7 core)
```
pf_regime_engine.py            ✅  B1 HTF context
pf_cascade_engine.py           ✅  B2 sequence velocity
pf_force_kinematics.py         ✅  B3 Kalman
pf_temporal_density.py         ✅  B4 cycles
pf_spearman_gravity.py         ✅  B5 gravity pairs
pf_currency_energy_probe.py    ✅  P_NEXT_1 energy
pf_temporal_node_state.py      ✅  Node V0.8.2 (stable)
pf_behavioral_alert_mapper.py  ✅  Mapper V7 regime_context
pf_confluence_elastic.py       ✅  EIE confluence
pf_confluence_gravity.py       ✅  Gravity fusion
pf_relational_gravity_bridge.py ✅ RG P1.2 bridge
pf_tension_signature.py        ✅  Micro/macro variance
```

### Couche 1 — Moteur (V7.1 validation)
```
pf_data_quality_guard.py       ✅  DB health metric
pf_market_open_validator.py    ✅  B4/B5/EIE live validation
pf_entropy_engine.py           ✅  Alert saturation meter
pf_session_overlay.py          ✅  Session context
pf_replay_engine.py            ✅  Deterministic replay
pf_film_engine.py              ✅  Behavioral timeline
```

### Couche 2 — Runners (Orchestration)
```
run_powerflow_cycle_once.py    ✅  9-step orchestrator complet
  ├─ step 1  data_quality_guard
  ├─ step 2  market_open_validator
  ├─ step 3  entropy_engine
  ├─ step 4  session_overlay_dashboard
  ├─ step 5  temporal_node_state
  ├─ step 6  currency_energy_probe
  ├─ step 7  confluence_alert (daemon)
  ├─ step 8  cascade_engine
  └─ step 9  dashboard_refresh
```

### Couche 2 — Runners (Spécialisés)
```
run_confluence_alert.py        ✅  EIE daemon 5min
run_entropy_engine_once.py     ✅  Dashboard entropy
run_session_overlay_dashboard_once.py ✅ Dashboard session
lab_replay.py                  ✅  Historique replay
lab_film.py                    ✅  Behavioral film
[tous les runners V7]          ✅  run_regime, run_density, run_spearman, etc.
```

### Couche 3 — Cockpit
```
dashboard_live.html            ✅  Interface live + 4 V7.1 cards
  ├─ Data Quality card          (data_quality_guard.json)
  ├─ Market Validator card      (market_open_validator.json)
  ├─ Entropy card               (entropy_engine.json)
  └─ Session Overlay card       (session_overlay.json)

cockpit_agentic_state_v01.py   ✅  Synthèse regime + cascade
```

---

## OUTPUTS JSON — INTERFACE RUNTIME

```
output/
├─ data_quality_guard.json              [V7.1] ← run_data_quality_guard
├─ market_open_validator.json           [V7.1] ← run_market_open_validator
├─ entropy_engine.json                  [V7.1] ← run_entropy_engine
├─ session_overlay.json                 [V7.1] ← run_session_overlay_dashboard
├─ temporal_node_state.json             [V7] ← run_temporal_node_state
├─ currency_energy.json                 [V7] ← run_currency_energy_probe
├─ behavioral_alert_queue.json          [V7] ← run_confluence_alert (append)
├─ cascade_state.json                   [V7] ← run_cascade_engine
├─ dashboard_data.json                  [V7] ← run_powerflow_dashboard_refresh
└─ cycle_report.json                    [V7.1] ← run_powerflow_cycle_once
```

---

## DB DENSITÉ (2026-05-09)

```
TF1    : 6930 rows  → B3/B4 fiables
TF5    : 1382 rows  → B4/B5 fiables
TF15   :  465 rows  → EIE fiable
TF30   :  257 rows  → B4 partiel
TF60   :  133 rows  → B4 limité
TF240  :   39 rows  → B1 heuristique seulement
TF1440 :   11 rows  → B1 HMM : attendre ≥ 50 rows (~3 sem)
```

---

## COMMANDES OPÉRATIONNELLES — P0 LUNDI 23h CEST

### Option 1 : Commande unique (recommandée)
```powershell
python .\run_powerflow_cycle_once.py --db .\powerflow.db --symbol GBPUSD
```

Exécute en ordre :
1. Data quality
2. Market validator
3. Entropy
4. Session overlay
5. Node state
6. Currency energy
7. Confluence alert
8. Cascade engine
9. Dashboard refresh

Durée estimée : ~44 secondes  
Output final : `output/cycle_report.json`

### Option 2 : Commandes individuelles si debug nécessaire
```powershell
python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-12 --pretty
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --recent-minutes 180 --pretty
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
python -c "from lab_elastic import q_eie_snapshot; q_eie_snapshot()"
python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty
python .\run_session_overlay_dashboard_once.py --timestamp now --pretty
python run_confluence_alert.py --once --dry-run
```

### Option 3 : Dry-run (vérifie sans exécuter)
```powershell
python .\run_powerflow_cycle_once.py --db .\powerflow.db --symbol GBPUSD --dry-run
```

---

## CRITÈRES P0 PASS

✅ **B4 TEMPORAL DENSITY**
```
dominant_period_bars ≠ 1 (au moins sur TF1 ou TF5)
cycle_state = COMPRESSING ou EXPANDING (pas NOISY ou STABLE)
```

✅ **B5 SPEARMAN GRAVITY**
```
spearman_rho fluctuant (change entre snapshots)
Labels varient (SYNCHRO, DIVERGENT, NEUTRAL selon les paires)
avg_rho non figé
```

✅ **EIE CONFLUENCE**
```
ELASTIC_IN_EXTREME détecté au moins une fois
(pas NEUTRAL permanent)
fractalite ≥ 1
elastic_score > 0.5
```

✅ **SESSION OVERLAY**
```
session = ASIAN (lundi 23h CEST)
session_phase = IGNITION ou MID_SESSION
minutes_since_open = correct
```

✅ **ENTROPY**
```
alert_entropy_state = NORMAL_ALERT_FLOW (pas SATURATED)
normalized_entropy exploitable
duplication_ratio acceptable
```

✅ **DB HEALTH**
```
Data fraîche (last_timestamp = now)
Aucun stale critique
Gaps visibles dans data_quality_guard.json (pas masqués)
Rows density cohérente par TF
```

✅ **DAEMON CONFLUENCE**
```
behavioral_alert_queue.json écrit
JSON valide
Aucun doublon massif
Entries persistent
```

---

## VERDICT P0

### Si PASS complet
```
Tous les capteurs sont VIVANTS (pas figés)
La machine perçoit vraiment, pas juste affiche des états pré-calculés
→ Lancer P1 Task Scheduler
→ Cycle 5min automatique
→ Dashboard cards live
```

### Si PARTIAL (certains FAIL)
```
Identifier quel capteur est figé :
  B4 ? → cycle_state = 1 partout ou NOISY
  B5 ? → rho figé ou labels ne changent jamais
  EIE ? → toujours NEUTRAL
→ Corriger cette brique
→ Relancer P0
```

### Si FAIL (aucun capteur vivant)
```
Probabilité très faible avec V7.1
Mais symptôme : marché fermé (week-end) ou capture_bridge arrêt
→ Vérifier MT4 connection
→ Vérifier DB fraîche
→ Attendre marché ouvert
```

---

## FICHIERS À NE PAS TOUCHER

```
capture_bridge.py
powerflow.db
pf_temporal_node_state.py              (99KB — stable)
pf_relational_gravity_bridge.py        (bridge_version=0.1.4)
cockpit_agentic_state_v01_orchestral.py (V0.1.4 UNIQUEMENT)
```

---

## RÈGLES RUNTIME ABSOLUES

```
❌ Ne pas modifier capture_bridge.py
❌ Ne pas écrire manuellement dans powerflow.db
❌ Ne pas importer cockpit_* dans pf_*
❌ Ne pas créer import circulaire
❌ Pas de BUY/SELL dans les alertes
❌ cockpit_orchestral V0.1.5+ = NO GO
❌ Features avancées gelées avant P0 PASS

✅ py_compile avant tout commit
✅ 1 feature = 1 commit
✅ Tests séquence P0
✅ git status propre
✅ Doctrine anti-nanny active
```

---

## PLAN IMMÉDIAT

### Dimanche 2026-05-10 soir
```
1. py_compile check
2. run_powerflow_cycle_once.py --dry-run
3. git status → propre
4. Prêt lundi
```

### Lundi 12 mai 23h CEST (Asian open)
```
1. python .\run_powerflow_cycle_once.py --db .\powerflow.db --symbol GBPUSD
2. Remplir P0_MARKET_OPEN_VALIDATION.md avec observations
3. Commit : git add . && git commit -m "P0: Market open validation ASIAN 20260512 — PASS"
4. git push origin main
```

### Après P0 PASS
```
P1 → Task Scheduler 5min automatique
P2 → Dashboard cards refreshed live
P3 → Lab Engine V2 (6 queries trading)
```

---

## GIT FINAL

```
Branch      : main
Latest      : acbe258 (orchestrator) + 18d0b28 (dashboard)
Status      : propre et prêt
Remote      : https://github.com/gestionzen57-alt/V7.git
```

---

## RÉSUMÉ MACHINE LISIBLE

```
POWERFLOW_V71_STATUS: PRODUCTION_LIVE
ORCHESTRATOR_READY: YES
DASHBOARD_READY: YES
P0_READINESS: YES
LAST_VALIDATION: 2026-05-09
NEXT_GATE: P0_LUNDI_23H_CEST
ARTIFACTS: cycle_report.json + dashboard_cards
DOCTRINE: perception_only / trader_decides / no_advice
```

---

*CURRENT_STATE V7.1 FINAL — 2026-05-09 — Production live — P0 prêt*
