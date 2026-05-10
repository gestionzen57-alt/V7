# CLAUDE.md V7.1 — PowerFlow Anticipatoire — MISE À JOUR FINALE
**Date : 2026-05-09 | Git : post-GPT-missions | Status : PRODUCTION LIVE**

---

## 0. DOCTRINE HTF — TA VISION CORRECTE

```
HTF  W/D/H4    = Analyse stratégique / régime / contexte primaire
MTF  H1/30/15  = Fenêtre temporelle / plan / scénario
LTF  15/5/1    = Intervention chirurgicale / ignition / exécution
```

**Anti-nanny** : zéro conseil financier. Risques techniques uniquement.
**Anti-GPT-biais** : zéro censure d'alerte. Trader filtre. Trader décide.

---

## 1. ÉTAT ACTUEL — V7.1 SPRINT COMPLET LIVRÉ

```
PowerFlow V7.1 = MOTEUR DE PERCEPTION + ORCHESTRATEUR + DASHBOARD LIVE
Statut         = PRODUCTION — PRÊT P0
Prochaine étape = Lundi 12 mai 23h CEST (Asian open)
Git commit      = 18d0b28 (dashboard) + acbe258 (orchestrator)
```

### ✅ CE QUI A ÉTÉ LIVRÉ CETTE SEMAINE

#### SPRINT 7J COMPLET (Perplexity/Gemini)
```
V7.1 Phase 1 : pf_data_quality_guard.py + pf_market_open_validator.py
V7.1 Phase 2 : pf_entropy_engine.py + pf_session_overlay.py
V7.1 Phase 3 : pf_replay_engine.py + pf_film_engine.py
```

#### MISSION GPT1 — Orchestrateur
```
run_powerflow_cycle_once.py          ✅ cycle complet 9 steps
9-steps ordre strict                 ✅ subprocess orchestration
Logs UTC + cycle_report.json         ✅ traçabilité totale
Windows scheduler ready              ✅ 44s cycle validé
Timeouts adaptés (Node 90s)          ✅ runtime known
```

#### MISSION GPT2 — Dashboard V7.1
```
4 live guard cards HTML/JS           ✅ Data Quality + Market Validator + Entropy + Session
polling 30s vanilla fetch()          ✅ compatible cockpit
Integration dashboard_live.html      ✅ commit 18d0b28
run_entropy_engine_once.py           ✅ produit entropy JSON
run_session_overlay_dashboard_once.py ✅ produit session JSON
```

---

## 2. PIPELINE COMPLET V7.1

```
=== COUCHE 0 — ACQUISITION ===
capture_bridge.py              ✅  Bridge MT4 → DB live
powerflow.db                   ✅  SQLite central

=== COUCHE 1 — MOTEUR (pf_*) ===
B1  pf_regime_engine.py        ✅  HTF context
B2  pf_cascade_engine.py       ✅  Sequence velocity
B3  pf_force_kinematics.py     ✅  Kalman Q=0.01 R=0.10
B4  pf_temporal_density.py     ✅  Cycles rolling
B5  pf_spearman_gravity.py     ✅  Spearman pairs
P_NEXT_1  pf_currency_energy_probe.py ✅ elastic_tension
P_NEXT_4  pf_confluence_elastic.py + pf_confluence_gravity.py ✅ EIE
V7.1 Phase 1  pf_data_quality_guard.py + pf_market_open_validator.py ✅
V7.1 Phase 2  pf_entropy_engine.py + pf_session_overlay.py ✅
V7.1 Phase 3  pf_replay_engine.py + pf_film_engine.py ✅

=== COUCHE 2 — RUNNERS ===
run_powerflow_cycle_once.py    ✅  Orchestrateur 9 steps complet
run_confluence_alert.py        ✅  Daemon EIE 5min
run_entropy_engine_once.py     ✅  Dashboard entropy
run_session_overlay_dashboard_once.py ✅ Dashboard session overlay
[tous les runners V7]          ✅

=== COUCHE 3 — COCKPIT ===
dashboard_live.html            ✅  4 live guard cards V7.1
cockpit_agentic_state_v01.py   ✅  Synthèse regime + cascade
```

---

## 3. COMMANDES OPÉRATIONNELLES LUNDI P0

### Séquence de validation (à lancer lundi 23h CEST Asian open)

```powershell
# Data Quality
python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-12 --pretty --output .\output\data_quality_guard.json

# Market Validator
python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --recent-minutes 180 --pretty --output .\output\market_open_validator.json

# B4 Temporal Density
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty

# B5 Spearman Gravity
python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty

# EIE snapshot
python -c "from lab_elastic import q_eie_snapshot; q_eie_snapshot()"

# Entropy
python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty --output .\output\entropy_engine.json

# Session Overlay
python .\run_session_overlay_dashboard_once.py --timestamp now --pretty --output .\output\session_overlay.json

# Daemon confluence
python run_confluence_alert.py --once --dry-run

# OU directement : cycle complet en une commande
python .\run_powerflow_cycle_once.py --db .\powerflow.db --symbol GBPUSD
```

---

## 4. CRITÈRES P0 PASS

```
✅ B4   : dominant_period_bars ≠ 1 ET cycle_state = COMPRESSING ou EXPANDING
✅ B5   : rho fluctuant ET labels varient (SYNCHRO/DIVERGENT/NEUTRAL)
✅ EIE  : ELASTIC_IN_EXTREME au moins une fois (pas NEUTRAL permanent)
✅ DB   : fraîche, no stale critique, gaps visibles
✅ Session : ASIAN à 23h CEST + IGNITION phase
✅ Entropy : NORMAL_ALERT_FLOW (pas SATURATED)
✅ Daemon : queue écrite, JSON valide, pas doublon massif
```

### Si P0 = PASS
```
→ Task Scheduler lancé P1
→ Cycle 5min automatique
→ Dashboard cards live
→ Prêt Lab Engine V2
```

### Si P0 = FAIL
```
→ Analyser quelle brique est figée
→ Corriger cette brique (B4 ou B5 ou EIE)
→ Relancer P0
```

---

## 5. GIT STATE FINAL

```
Commit orchestrator : acbe258 — V7.1: add full powerflow cycle orchestrator
Commit dashboard    : 18d0b28 — Dashboard: add V7.1 live guard cards
Branch              : main
Remote              : https://github.com/gestionzen57-alt/V7.git
Status              : propre, prêt pour P0
```

---

## 6. MISSIONS COMPLÉTÉES CETTE SEMAINE

| Mission | Responsable | Livrables | Statut |
|---------|------------|-----------|--------|
| V7.1 Sprint 7J | Gemini/Perplexity | 12 modules validation+traçabilité | ✅ |
| Orchestrateur | GPT1 | run_powerflow_cycle_once.py | ✅ |
| Dashboard Cards | GPT2 | 4 cards HTML/JS vanilla | ✅ |
| Docs update | Claude | P0 guide + CLAUDE.md V7.1 | ✅ |

---

## 7. RISQUES TECHNIQUES RÉSIDUELS

| Risque | Gravité | Mitigation |
|--------|---------|-----------|
| B4 figé weekend | Moyen | Valider avec données live lundi |
| B5 rho instable | Moyen | Rho turnover observable lundi |
| EIE NEUTRAL permanent | Moyen | Vérifier elastic_score lundi |
| Node Engine 32s | Faible | Timeout 90s en place |
| Dashboard JSON path | Faible | Vérifier serveur Flask statique |

---

## 8. PLAN POST-P0

```
P1 — Task Scheduler (après P0 PASS)
  Cycle automatique 5min via Windows Task Scheduler
  run_powerflow_cycle_once.py --db powerflow.db --symbol GBPUSD
  Logs + cycle_report.json

P2 — Dashboard V7.1 Cards (après P1 stable)
  Affichage live quality / validator / entropy / session
  Polling 30s
  Cockpit refreshed

P3 — Lab Engine V2
  6 queries trading B4+B5+regime
  Après P0 validé

GELÉS jusqu'après P0+P1 :
  Fractal Resonance
  Volatility Texture
  Memory Engine
  Multi-Symbol
```

---

## 9. FICHIERS STABLES — NE PAS TOUCHER

```
capture_bridge.py
powerflow.db
pf_temporal_node_state.py              (99KB)
pf_relational_gravity_bridge.py        (bridge_version=0.1.4)
cockpit_agentic_state_v01_orchestral.py (V0.1.4 UNIQUEMENT)
```

---

## 10. WORKFLOW MULTI-IA ACTIF

```
Claude Projects (ce fil)    = Chef d'orchestre / validation / docs / prompts
Claude Code                 = Exécution / tests / commits si demandé
GPT1                        = Mission orchestrator [COMPLÉTÉ]
GPT2                        = Mission dashboard [COMPLÉTÉ]
Perplexity / Gemini         = Si nouveau sprint 7J+ nécessaire
```

---

## 11. LEXIQUE ADDITIONS V7.1

Nouveaux termes validés :

```
POWERFLOW_CYCLE_ORCHESTRATOR    run_powerflow_cycle_once.py
NON_BLOCKING_CYCLE              fail n'arrête pas les steps suivants
CYCLE_REPORT                    output/cycle_report.json
STEP_STATUS                     OK ou FAIL pour chaque runner
ACCEPTED_RETURNCODE_WITH_OUTPUT returncode=2 mais output JSON exists
DRY_RUN_CYCLE                   --dry-run pour vérifier sans exécuter
SYMBOL_SANITIZATION             GBPUSD. → GBPUSD (nettoyage)
WINDOWS_UTF8_SUBPROCESS         PYTHONUTF8=1 pour unicode
NODE_TIMEOUT_SECONDS            90s dédié au Node Engine
DASHBOARD_WINDOW                fenêtre auto 180 minutes
SCHEDULER_READY_CYCLE           prêt pour Windows Task Scheduler
CYCLE_DURATION_PROFILE          observé ~44s total
```

Voir `LEXIQUE_GRAMMAIRE_V7.1.md` sections 16-21 pour détail complet.

---

## 12. CHECKPOINTS FINAL

```
2026-05-09  V7 → V7.1 Sprint COMPLET
            12 modules livré (Gemini/Perplexity)
            Orchestrator livré (GPT1)
            Dashboard Cards livré (GPT2)
            P0 Guide créé
            CLAUDE.md V7.1 final
            Git c7f50b0 → 18d0b28 → acbe258
            Prêt P0 lundi 23h CEST
```

---

## 13. PHRASE FINALE

```
PowerFlow V7.1 est en production.

Les 4 capteurs sont construits.
L'orchestrateur les déclenche.
Le dashboard les montre.
Le trader les interprète.

Lundi 23h, on teste qu'ils sont vivants.
Pas figés.
Pas aveugles.

La machine perçoit.
Le trader décide.
```

---

## 14. POINT D'ARRÊT AVANT P0

### Vérifications à faire dimanche soir (avant lundi)

```powershell
# 1. Python compile check
python -m py_compile pf_data_quality_guard.py
python -m py_compile pf_market_open_validator.py
python -m py_compile pf_entropy_engine.py
python -m py_compile pf_session_overlay.py
python -m py_compile run_powerflow_cycle_once.py

# 2. Dry-run orchestrator
python .\run_powerflow_cycle_once.py --db powerflow.db --symbol GBPUSD --dry-run

# 3. DB santé (optionnel mais bon)
python run_data_quality_guard_once.py --db powerflow.db --pretty

# 4. Git status propre
git status
```

Si tout OK → tu es prêt.

---

## 15. CONTACT / AIDE LUNDI

Si une commande fail lundi :

1. Note l'erreur exacte
2. Dis-moi quel step a échoué
3. Je te donne le fix immédiatement

Le cycle est non-bloquant : 1 step fail n'arrête pas les autres.

---

*CLAUDE.md V7.1 FINAL — 2026-05-09 — Prêt P0 lundi*
