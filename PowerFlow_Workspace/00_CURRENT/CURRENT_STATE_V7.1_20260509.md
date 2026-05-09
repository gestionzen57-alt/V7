# CURRENT_STATE — PowerFlow V7.1
**Date : 2026-05-09 | Git : post-sprint-7J | Statut : PRODUCTION — EN ATTENTE P0 LUNDI**

---

## ÉTAT GLOBAL

```
PowerFlow V7.1 = MOTEUR DE PERCEPTION ANTICIPATOIRE + TRAÇABILITÉ
Statut         = PRODUCTION — VALIDATION MARCHÉ OUVERT PENDING
Prochaine étape = Lundi 12 mai — Asian open 23h CEST
```

---

## PIPELINE ACTIF V7.1 COMPLET

```
=== COUCHE 0 — ACQUISITION ===
capture_bridge.py              ✅  Bridge MT4 → powerflow.db (live)
powerflow.db                   ✅  Mémoire SQLite centrale

=== COUCHE 1 — MOTEUR (pf_*) ===

--- V7 Core ---
pf_regime_engine.py            ✅  B1 — HTF_CONTEXT_STACK
pf_force_kinematics.py         ✅  B3 — Kalman Q=0.01 R=0.10
pf_temporal_density.py         ✅  B4 — Cycles / compression rolling
pf_spearman_gravity.py         ✅  B5 — Corrélation de rang toutes paires
pf_cascade_engine.py           ✅  B2 — SEQUENCE_VELOCITY 5min
pf_currency_energy_probe.py    ✅  P_NEXT_1 — elastic_tension_score
pf_temporal_node_state.py      ✅  Node V0.8.2 (NE PAS TOUCHER)
pf_behavioral_alert_mapper.py  ✅  V7 regime_context enrichi
pf_confluence_elastic.py       ✅  EIE — zone + élastique + fractalité
pf_confluence_gravity.py       ✅  Bridge EIE × B1 × B5 × RG
pf_relational_gravity_bridge.py ✅  bridge_version=0.1.4 (NE PAS TOUCHER)
pf_tension_signature.py        ✅  Micro/macro variance

--- V7.1 Validation & Traceability ---
pf_data_quality_guard.py       ✅  Qualité DB — gaps/stale/rows/density
pf_market_open_validator.py    ✅  Valide B4/B5/EIE non figés live
pf_entropy_engine.py           ✅  Alert entropy / saturation / burst
pf_session_overlay.py          ✅  Contexte sessionnel Asian/London/NY
pf_replay_engine.py            ✅  Replay déterministe force_snapshots
pf_film_engine.py              ✅  Film comportemental timeline

=== COUCHE 2 — RUNNERS ===
run_confluence_alert.py        ✅  Daemon 5min — EIE → behavioral_queue
run_data_quality_guard_once.py ✅  V7.1
run_market_open_validator_once.py ✅ V7.1
run_entropy_engine_once.py     ✅  V7.1
run_session_overlay_once.py    ✅  V7.1
lab_replay.py                  ✅  V7.1
lab_film.py                    ✅  V7.1
[tous les runners V7 existants] ✅

=== COUCHE 3 — COCKPIT ===
cockpit_agentic_state_v01.py   ✅  V7 — regime_block + cascade_block
dashboard_live.html            ✅  Affichage cockpit
```

---

## CE QUI A ÉTÉ LIVRÉ — SPRINT 7J (2026-05-09)

```
Phase 1 — Infra & Qualité
  pf_data_quality_guard.py        ✅
  run_data_quality_guard_once.py  ✅
  pf_market_open_validator.py     ✅
  run_market_open_validator_once.py ✅
  DB read-only validée
  gaps / stale / no rows / static outputs exposés

Phase 2 — Entropy & Session Overlay
  pf_entropy_engine.py            ✅
  run_entropy_engine_once.py      ✅
  pf_session_overlay.py           ✅
  run_session_overlay_once.py     ✅
  Contexte sessionnel disponible
  Texture / désordre du flux mesurable

Phase 3 — Replay & Film Engine
  pf_replay_engine.py             ✅
  lab_replay.py                   ✅
  pf_film_engine.py               ✅
  lab_film.py                     ✅
  Replay déterministe depuis force_snapshots
  Film comportemental historique prêt
```

---

## DENSITÉ DB (2026-05-09)

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

## PROCHAINES ACTIONS — P0 LUNDI 12 MAI

```
Commandes P0 prioritaires (Asian open 23h CEST) :

python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-12 --pretty
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --recent-minutes 180 --pretty
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
python -c "from lab_elastic import q_eie_snapshot; q_eie_snapshot()"
python run_confluence_alert.py --once --dry-run
python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty
python .\run_session_overlay_once.py --timestamp now --pretty

Critères PASS :
  B4 : dominant_period_bars ≠ 1, cycle_state non statique
  B5 : rho fluctuant, labels cohérents (pas figés)
  EIE : snapshot non NEUTRAL si tension réelle
  DB : fraîche, gaps/stale visibles et quantifiés
  Session : session=ASIAN confirmée, minutes_since_open correct
  Entropy : alert_entropy_state dynamique

Livrable : P0_MARKET_OPEN_VALIDATION.md
```

---

## PLAN POST-P0

```
P1 — Task Scheduler (après P0 PASS)
  Cycle automatique 5min :
  1. run_data_quality_guard_once.py
  2. run_market_open_validator_once.py
  3. run_entropy_engine_once.py
  4. run_session_overlay_once.py
  5. run_temporal_node_state_once.py
  6. run_currency_energy_probe_once.py
  7. run_confluence_alert.py --once
  8. run_cascade_engine_once.py
  9. run_powerflow_dashboard_refresh_once.py

P2 — Dashboard V7.1 Cards (après P1 stable)
  Quality Card    → data_quality_guard.json
  Validator Card  → market_open_validator.json
  Entropy Card    → entropy_engine.json
  Session Card    → session_overlay.json

P3 — Lab Engine V2 (après P0 validé)
  6 queries trading B4+B5+regime

GELÉS jusqu'après P0+P1 :
  Fractal Resonance
  Volatility Texture
  Memory Engine
  Multi-Symbol
  B1 HMM
  B4 Wavelet
```

---

## FICHIERS STABLES — NE PAS TOUCHER

```
capture_bridge.py
powerflow.db
pf_temporal_node_state.py                     (99KB)
pf_relational_gravity_bridge.py               (bridge_version=0.1.4)
cockpit_agentic_state_v01_orchestral.py       (V0.1.4 UNIQUEMENT)
```

---

## RÈGLES RUNTIME ABSOLUES

```
❌ Ne pas modifier capture_bridge.py
❌ Ne pas écrire dans powerflow.db
❌ Ne pas importer cockpit_* dans pf_*
❌ Pas de dépendances circulaires
❌ Pas de BUY/SELL dans les alertes
❌ cockpit_orchestral V0.1.5+ = NO GO
❌ Features avancées gelées avant P0 PASS

✅ py_compile avant tout commit
✅ 1 feature = 1 commit
✅ Rapport + Checkpoint fin de mission
✅ git_sync.ps1 après chaque mission
✅ Doctrine anti-nanny active
```

---

*Updated 2026-05-09 — Sprint 7J clôturé — V7.1 LIVE*
