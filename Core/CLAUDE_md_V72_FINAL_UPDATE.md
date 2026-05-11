# CLAUDE.md — V7.2 FINAL UPDATE POST-P0 LIVE

**Date :** 2026-05-11  
**Generated UTC :** 2026-05-11T10:30:45Z  
**Version :** PowerFlow V7.2  
**Git final :** `0dc2df6`  
**Branche :** `main`  
**Statut :** `P0 CORE PASS / STRICT PENDING_DATA_WINDOW`  
**Validation :** P0 live recovery successful + Dashboard hydration PASS

> Bloc documentaire prêt à insérer dans le `CLAUDE.md` principal.  
> Il devient le point de reprise pour Claude / GPT / tout agent IA opérant sur PowerFlow V7.2 après P0 live.

---

## SECTION 1 — STATUS GLOBAL

```text
PowerFlow version       : V7.2
Date état               : 2026-05-11
Git final               : 0dc2df6
P0 Core Perception      : PASS
P0 Dashboard Flow       : PASS
P0 LTF Data Quality     : PASS
P0 Automation           : PASS
P0 Strict Full          : PENDING_DATA_WINDOW
Dashboard Hydration     : PASS — 16 steps / 0 failed
Dashboard Contract      : PASS — 0 fail / 0 warn
Runtime posture         : PRODUCTION LIVE / MONITORING P0
```

### Verdict architecte

```text
PowerFlow perçoit.
PowerFlow mesure.
PowerFlow nomme.
PowerFlow alerte.
Le dashboard montre.
Le trader décide.
```

`PENDING_DATA_WINDOW` n’est pas un FAIL.  
C’est une attente d’accumulation statistique pendant que les briques critiques respirent.

---

## SECTION 2 — P0 LIVE RECOVERY SUMMARY

### Ce qui a changé depuis le dernier checkpoint

Avant recovery :

```text
M5/M15 arrêtés depuis 2026-05-08.
Cause : MT4 avait rechargé les anciens EA au reboot.
Effet : B4/B5/Node ne pouvaient pas respirer correctement.
Diagnostic initial : P0 strict impossible à valider.
```

Action recovery :

```text
Rechargement des bons EA MT4.
Bridge TCP redevenu actif.
M5/M15 restaurés dans powerflow.db.
Fenêtre fraîche observée depuis 2026-05-11T01:15:00Z.
```

Après recovery :

```text
B4 Temporal Density      : PASS_ALIVE / LAG1_COMPRESSION
B5 Spearman Gravity      : PASS_ALIVE / SPEARMAN_GRAVITY_ACTIVE
Temporal Node State      : PASS_ALIVE / HOT_NODE
Data Quality LTF         : PASS
Dashboard hydration      : PASS
Automation P0            : PASS
Strict Full              : PENDING_DATA_WINDOW
```

### Résultat

```text
Statut final = PASS_CORE_PARTIAL_STRICT

Core perception validée.
Infrastructure dashboard validée.
Automation P0 validée.
Fenêtre stricte en accumulation naturelle.
```

---

## SECTION 3 — PIPELINE ACTIF ACTUEL

| # | Brique | Module / runner | Statut | Output / surface | Commentaire |
|---:|---|---|---|---|---|
| 1 | B1 Legacy Regime | `run_regime_engine_once.py` | PASS | `output/dashboard_surface/regime_legacy.json` | Régime heuristique HTF |
| 2 | B1+ HMM Regime | `run_hmm_regime_once.py` | PASS | `output/dashboard_surface/regime_hmm.json` | Dual regime, jamais fusionné |
| 3 | B2 Cascade | `run_cascade_engine_once.py` | PASS_ENGINE | `output/dashboard_surface/cascade.json` | Event rate / cascade_building |
| 4 | B3 Force Kinematics | `run_force_kinematics_once.py` | PASS | `output/force_kinematics_state.json` | Contrat start/end/timeframes corrigé |
| 5 | P1 Currency Energy | `run_currency_energy_probe_once.py` | PASS_ALIVE | `output/dashboard_surface/energy.json` | Elastic tension / energy |
| 6 | B4 Rolling Density | `run_temporal_density_once.py` | PASS_ALIVE | `output/temporal_density_state.json` | LAG1_COMPRESSION possible |
| 7 | B4+ Wavelet Density | `run_wavelet_density_once.py` | PASS | `output/dashboard_surface/wavelet.json` | Dual density, jamais fusionnée |
| 8 | B5 Spearman Gravity | `run_spearman_gravity_once.py` | PASS_ALIVE | `output/spearman_gravity_state.json` | rho vivants / tail extremes |
| 9 | B6 Memory | `run_memory_query_once.py` | PASS | `output/dashboard_surface/memory.json` | Fréquences historiques, pas probabilité |
| 10 | B7 Fractal Resonance | `run_fractal_resonance_once.py` | PASS_ENGINE | `output/dashboard_surface/fractal.json` | SILENT est un état, pas une panne |
| 11 | B7+ Volatility Texture | `run_volatility_texture_once.py` | PASS | `output/dashboard_surface/texture.json` | STRUCTURAL / NEWS_SPIKE / friction |
| 12 | Guard Entropy | `run_alert_entropy_once.py` | PASS | `output/dashboard_surface/entropy.json` | Saturation qualifiée sans censure |
| 13 | Guard Session Overlay | `run_session_overlay_once.py` | PASS | `output/dashboard_surface/session.json` | Session active / phase / UTC |
| 14 | Guard Data Quality LTF | `run_data_quality_guard_once.py` | PASS | `output/data_quality_report.json` | TF1/5/15 clean |
| 15 | P2 Behavioral Mapper | `run_behavioral_alert_mapper_once.py` | PASS | `output/behavioral_alert_queue.json` | Queue normalisée |
| 16 | Temporal Node State | `run_temporal_node_state_once.py` | PASS_ALIVE | `output/dashboard_surface/node.json` | HOT_NODE / micro-node |
| 17 | P0 Final Validator | `p0_final_validator.py` | PASS_ENGINE | `output/P0_FINAL_DECISION.*` | Requalifie pending vs fail |
| 18 | Dashboard Normalizer | `dashboard_data_normalizer.py` | PASS | `output/dashboard_surface/*.json` | Surface contractuelle |
| 19 | Dashboard Contract Validator | `dashboard_contract_validator.py` | PASS | `output/DASHBOARD_CONTRACT_VALIDATION.md` | 0 fail / 0 warn |
| 20 | Hydration Failure Doctor | `dashboard_hydration_failure_doctor.py` | PASS | `output/DASHBOARD_HYDRATION_FAILURE_DOCTOR.md` | Lit `dashboard_hydrate_*` et `dashboard_hydration_*` |

### Pipeline runtime

```text
capture_bridge.py
  → powerflow.db
  → pf_* moteurs
  → run_* runners
  → output/dashboard_surface/*.json
  → dashboard_live_v7.2_final.html
  → trader
```

---

## SECTION 4 — COMMANDE OPÉRATIONNELLE UNIQUE

```powershell
.\run_p0_final_auto.ps1 -Symbol GBPUSD
```

Résultat attendu :

```text
PASS_CORE_PARTIAL_STRICT
  ✅ Core perception
  ✅ Dashboard flow
  ✅ Automation
  ⚠️ Strict full = PENDING_DATA_WINDOW
```

Commande dashboard session :

```powershell
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD -Serve
```

Résultat attendu :

```text
Hydration : 16 steps / 0 failed
Contract  : PASS 0 fail / 0 warn
Serve     : http://localhost:8787/dashboard_live_v7.2_final.html
```

---

## SECTION 5 — CHECKPOINT PRÉCÉDENT

À lire en premier dans un nouveau fil IA :

```text
CHECKPOINT_V72_POST_P0_LIVE_20260511.md
CURRENT_STATE_V72_POST_P0_20260511.md
LEXIQUE_GRAMMAIRE_V72_PATCH_POST_P0_20260511.md
```

Fichiers livrés / équivalents dans Core :

```text
CHECKPOINT_P0_LIVE_20260511.md
CURRENT_STATE_V7_POST_P0_UPDATE.md
LEXIQUE_GRAMMAIRE_V7_PATCH_POST_P0.md
DASHBOARD_WRAPPER_HARDENING_REPORT.md
DASHBOARD_V72_FINAL_VALIDATION_REPORT.md
```

---

## SECTION 6 — RÈGLES ABSOLUES POST-P0

### NE PAS

```text
❌ NE PAS modifier capture_bridge.py sans accord explicite
❌ NE PAS écrire manuellement dans powerflow.db
❌ NE PAS importer cockpit_* / dashboard_* / telegram_* depuis pf_*
❌ NE PAS fusionner B1 Legacy et B1+ HMM
❌ NE PAS fusionner B4 Rolling et B4+ Wavelet
❌ NE PAS injecter BUY/SELL
❌ NE PAS présenter Memory comme probabilité
❌ NE PAS masquer technical_risks
❌ NE PAS censurer M1 parce que précoce
```

### À faire

```text
✅ Laisser capture tourner naturellement
✅ Relancer P0 validation pour monitoring fenêtre
✅ Dashboard hydratation + validation avant chaque session
✅ py_compile avant commit
✅ 1 feature = 1 commit
✅ Exposer MISSING / STALE / DEGRADED
✅ Qualifier, ne pas retenir
```

---

## SECTION 7 — PROCHAIN CHECKPOINT

### Quand

```text
Quand PENDING_DATA_WINDOW atteint 100%.
Quand market_open_validator / P0 strict passe naturellement en PASS_STRICT.
```

### Statut attendu

```text
P0 Strict Full = PASS_STRICT
P0 Global      = PASS_FULL
```

### Action

```powershell
.\run_p0_final_auto.ps1 -Symbol GBPUSD
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
git status
```

Commit attendu :

```text
P0: promote strict validation from pending data window to PASS_STRICT
```

---

## NOTE POUR NOUVEL AGENT IA

```text
Ne recommence pas la stabilisation dashboard.
Ne repatche pas capture_bridge.py.
Ne touche pas powerflow.db.
Le prochain vrai sujet est la promotion PENDING_DATA_WINDOW → PASS_STRICT.
Le dashboard est contractuel, hydraté et validé.
```

---

*CLAUDE.md V7.2 Final Update — 2026-05-11 — à insérer dans CLAUDE.md principal.*
