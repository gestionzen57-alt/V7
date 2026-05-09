# CURRENT_STATE — PowerFlow V7
**Date : 2026-05-09 | Git : c579afa | Statut : PRODUCTION READY**

---

## ÉTAT GLOBAL

```
PowerFlow V7 = MOTEUR DE PERCEPTION ANTICIPATOIRE
Statut       = PRODUCTION — EN ATTENTE VALIDATION MARCHÉ OUVERT
Prochaine validation = Lundi 12 mai — Asian open 23h CEST
```

---

## PIPELINE ACTIF

```
capture_bridge.py          ✅  Bridge MT4 → powerflow.db (live)
powerflow.db               ✅  Mémoire SQLite centrale
pf_regime_engine.py        ✅  B1 — HTF_CONTEXT_STACK
pf_force_kinematics.py     ✅  B3 — Kalman Q=0.01 R=0.10
pf_temporal_density.py     ✅  B4 — Cycles / compression rolling
pf_spearman_gravity.py     ✅  B5 — Corrélation de rang toutes paires
pf_cascade_engine.py       ✅  B2 — SEQUENCE_VELOCITY 5min
pf_currency_energy_probe.py ✅ P_NEXT_1 — elastic_tension_score
pf_temporal_node_state.py  ✅  Node V0.8.2
pf_behavioral_alert_mapper.py ✅ V7 regime_context enrichi
pf_confluence_elastic.py   ✅  EIE — zone + élastique + fractalité
pf_confluence_gravity.py   ✅  Bridge EIE × B1 × B5 × RG
run_confluence_alert.py    ✅  Daemon 5min — P_NEXT_4
cockpit_agentic_state_v01.py ✅ V7 — regime_block + cascade_block
dashboard_live.html        ✅  Affichage cockpit
```

---

## RÉSOLUTION ANGLE MORT CRITIQUE V7

```
AVANT V6 :
  FIRST_DETACHMENT compression = FIRST_DETACHMENT expansion
  → même alerte pour deux réalités opposées

APRÈS V7 :
  regime_context injecté dans chaque alerte
  FIRST_DETACHMENT + COMPRESSION → HOT
  FIRST_DETACHMENT + RANGE       → WATCH
  FIRST_DETACHMENT + TENDANCE    → INFO
```

---

## DERNIÈRE SESSION (2026-05-09)

### Produit
- `pf_confluence_elastic.py` V1.0 ← calcul EIE + fractalité
- `pf_confluence_gravity.py` V0.2.0 ← bridge B1×B5×RG
- `run_confluence_alert.py` V2.0 ← daemon + EIE persistant + Telegram enrichi
- `run_confluence_scan.py` V2.0 ← API historique lab/film
- `lab_elastic.py` V1.0 ← 6 queries
- B3/B4/B5 validées py_compile ✅
- Git propre : c579afa — Cleanup 40 fichiers archivés

### P_NEXT résolus
- P_NEXT_1 ✅ tension élastique dans currency energy
- P_NEXT_4 ✅ EIE → behavioral_alert_queue.json

---

## DENSITÉ DB (2026-05-09)

```
TF1    : 6930 rows  → B3/B4 fiables
TF5    : 1382 rows  → B4/B5 fiables
TF15   :  465 rows  → zone EIE fiable
TF30   :  257 rows  → B4 partiel
TF60   :  133 rows  → B4 limité
TF240  :   39 rows  → B1 heuristique seulement
TF1440 :   11 rows  → B1 HMM : attendre ≥ 50 rows (~3 sem)
```

---

## FICHIERS STABLES — NE PAS TOUCHER

```
capture_bridge.py
powerflow.db
pf_temporal_node_state.py                      (99KB — ne pas refactoriser)
pf_relational_gravity_bridge.py               (bridge_version=0.1.4)
cockpit_agentic_state_v01_orchestral.py       (V0.1.4 UNIQUEMENT)
```

---

## PROCHAINES ACTIONS IMMÉDIATES

```
P0 — Lundi 12 mai, Asian open 23h CEST
  Valider B4 sur marché ouvert (dominant_period ≠ 1)
  Valider B5 (rho non-statiques)
  Valider EIE live (snapshot non NEUTRAL)
  Lancer daemon confluence_alert en conditions réelles

P1 — Semaine 12 mai
  Task Scheduler Windows : cycle 5min automatique
  Lab Engine V2 : 6 queries trading (B4+B5+regime)
  Dashboard V7 : cards B1 + B4 + B5

P2 — Moyen terme
  B1 HMM upgrade (quand TF1440 ≥ 50 rows)
  B4 Wavelet Morlet (si densité TF5 reste propre)
  Telegram V7 : alertes regime + cascade

P3 — Architecture future
  Task Scheduler orchestrateur
  Multi-symbol extension (EURUSD, USDJPY)
  Session memory (session overlay sur alertes)
```

---

## RÈGLES RUNTIME ABSOLUES

```
❌ Ne pas modifier capture_bridge.py
❌ Ne pas écrire dans powerflow.db (read-only uri=?mode=ro)
❌ Ne pas importer cockpit_* dans pf_*
❌ Pas de dépendances circulaires
❌ Pas de BUY/SELL dans les alertes
❌ cockpit_orchestral V0.1.5+ = NO GO

✅ py_compile avant tout commit
✅ 1 feature = 1 commit
✅ Rapport + Checkpoint fin de mission
✅ git_sync.ps1 après chaque mission
✅ Doctrine anti-nanny active
```

---

## WORKFLOW MULTI-IA ACTIF

```
Claude Projects (ce workspace) → Architecte / vision / docs
Claude Code                    → Exécution / tests / commits
Après 12 mai : Claude Max unique chef d'orchestre
```

---

*Updated 2026-05-09 | Source of truth : CLAUDE.md V7*
